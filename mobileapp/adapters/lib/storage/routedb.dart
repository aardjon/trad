///
/// Definition of the route DB storage adapter.
///
library;

import 'dart:io';

import 'package:core/boundaries/storage/routedb.dart';
import 'package:core/entities/geoposition.dart';
import 'package:core/entities/post.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:core/entities/summit.dart';
import 'package:core/entities/errors.dart';
import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/paths.dart';
import '../boundaries/repositories/database.dart';
import '../boundaries/repositories/filesystem.dart';
import '../src/storage/routedb/schema.dart';
import '../src/storage/version.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.adapters.storage.routedb');

/// Implementation of the storage adapter used by the core to interact with the route DB repository.
class RouteDbStorage implements RouteDbStorageBoundary {
  /// The filename of the route database file (within the application data dir).
  static const String _dbFileName = 'peaks.sqlite';

  /// Interface to the component used to retrieve environment specific path information.
  final PathProviderBoundary _pathProviderBoundary;

  /// Interface to the component providing file system access.
  final FileSystemBoundary _fileSystemBoundary;

  /// The route db data repository.
  final RelationalDatabaseBoundary _repository;

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  RouteDbStorage(DependencyProvider dependencyProvider)
    : _pathProviderBoundary = dependencyProvider.provide<PathProviderBoundary>(),
      _fileSystemBoundary = dependencyProvider.provide<FileSystemBoundary>(),
      _repository = dependencyProvider.provide<RelationalDatabaseBoundary>();

  @override
  Future<void> startStorage() async {
    String connectionString = await _getExpectedDbFile();
    _logger.info('Connecting to route database at: $connectionString');
    await _startWithFile(connectionString);
  }

  Future<void> _startWithFile(String databaseFile) async {
    _connectDatabase(databaseFile);
    await _checkSchemaVersion(databaseFile);
  }

  /// Tries to connect the database with the given [connectionString]. Throws a
  /// [StorageStartingException] in case of connection errors.
  void _connectDatabase(String connectionString) {
    try {
      _repository.connect(connectionString, readOnly: true);
    } on Exception catch (e) {
      throw InaccessibleStorageException(connectionString, e);
    }
  }

  /// Checks if the (already connected) database with the [connectionString] has a compatible schema
  /// version. Throws [StorageStartingException] if it doesn't.
  Future<void> _checkSchemaVersion(String connectionString) async {
    Query query = Query.table(DatabaseMetadataTable.tableName, <String>[
      DatabaseMetadataTable.columnSchemaVersionMajor,
      DatabaseMetadataTable.columnSchemaVersionMinor,
    ]);
    query.limit = 1;

    ResultRows resultSet = <ResultRow>[];
    try {
      resultSet = await _repository.executeQuery(query);
    } on Exception {
      throw InvalidStorageFormatException(connectionString, 'Database is of an unexpected schema');
    }
    if (resultSet.isEmpty) {
      throw InvalidStorageFormatException(connectionString, 'Database has no schema version');
    }
    Version databaseVersion = Version(
      resultSet[0].getIntValue(DatabaseMetadataTable.columnSchemaVersionMajor),
      resultSet[0].getIntValue(DatabaseMetadataTable.columnSchemaVersionMinor),
    );
    if (!databaseVersion.isCompatible(supportedSchemaVersion)) {
      throw IncompatibleStorageException(connectionString, databaseVersion, supportedSchemaVersion);
    }
  }

  @override
  void stopStorage() {
    if (isStarted()) {
      _logger.info('Disconnecting from route database');
      _repository.disconnect();
    }
  }

  @override
  bool isStarted() {
    return _repository.isConnected();
  }

  @override
  Future<void> importRouteDbFile(String filePath) async {
    if (isStarted()) {
      throw StateError('Cannot import a DB file when the storage is STARTED.');
    }

    final File fileToImport = _fileSystemBoundary.getFile(filePath);
    final File destinationFile = _fileSystemBoundary.getFile(await _getExpectedDbFile());

    if (!fileToImport.existsSync()) {
      throw PathNotFoundException(
        filePath,
        const OSError('File not found'),
        'Unable to import database because the requested file does not exist',
      );
    }

    // Check if the given file is a usable route database by trying to start with it (throws if it
    // is not).
    _logger.debug('Checking database compatibility before import');
    await _startWithFile(filePath);
    _repository.disconnect();

    // Remove the existing database, if any
    if (destinationFile.existsSync()) {
      _logger.debug('Deleting the old database at "${destinationFile.path}"');
      destinationFile.deleteSync();
    }

    // Copy the new database file to its final destination
    _logger.debug('Copying "${fileToImport.path}" to "${destinationFile.path}"');
    fileToImport.copySync(destinationFile.path);
  }

  Future<String> _getExpectedDbFile() async {
    Directory dataDir = await _pathProviderBoundary.getAppDataDir();
    return _fileSystemBoundary.joinPaths(dataDir.path, _dbFileName);
  }

  @override
  Future<DateTime> getCreationDate() async {
    if (!isStarted()) {
      throw StateError('Cannot get database creation date while the storage is STOPPED.');
    }
    // TODO(aardjon): The data retrieval date must be stored in the database itself. But for now, we
    //    use the file modification date for simplicity.
    String dbFilePath = await _getExpectedDbFile();
    File dbFile = _fileSystemBoundary.getFile(dbFilePath);
    return dbFile.statSync().modified;
  }

  @override
  Future<Summit> retrieveSummit(int summitDataId) async {
    // Unknown/Missing position values are stored in the database with this special coordinates.
    const (int, int) undefinedCoordinates = (0, 0);
    // The precision of geographic coordinates stored in the database. The read value must be
    // divided by this factor to get regular (floating point) decimal degree.
    const double coordinateValuePrecision = 10000000;

    Query query = Query.join(
      <String>[SummitsTable.tableName, SummitNamesTable.tableName],
      <String>['${SummitNamesTable.columnSummitId}=${SummitsTable.columnId}'],
      <String>[
        SummitNamesTable.columnName,
        SummitsTable.columnLatitude,
        SummitsTable.columnLongitude,
      ],
    );
    query.setWhereCondition(
      '${SummitsTable.columnId} = ? and ${SummitNamesTable.columnUsage} = 0',
      <int>[summitDataId],
    );
    query.limit = 1;

    List<ResultRow> resultSet = await _repository.executeQuery(query);
    String name = resultSet[0].getStringValue(SummitNamesTable.columnName);
    int lat = resultSet[0].getIntValue(SummitsTable.columnLatitude);
    int lon = resultSet[0].getIntValue(SummitsTable.columnLongitude);
    GeoPosition? position;
    if ((lat, lon) != undefinedCoordinates) {
      position = GeoPosition(lat / coordinateValuePrecision, lon / coordinateValuePrecision);
    }
    return Summit(summitDataId, name, position);
  }

  @override
  Future<List<Summit>> retrieveSummits([String? nameFilter]) async {
    // Configure the query
    Query query = Query.table(SummitNamesTable.tableName, <String>[
      SummitNamesTable.columnSummitId,
      SummitNamesTable.columnName,
    ]);
    if (nameFilter != null) {
      _logger.debug('Retrieving filtered summit list for "$nameFilter"');
      query.setWhereCondition('${SummitNamesTable.columnName} LIKE ?', <String>['%$nameFilter%']);
    } else {
      _logger.debug('Retrieving complete summit list');
    }
    query.orderByColumns = <String>[SummitNamesTable.columnName];

    // Run the database query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Summit> summits = <Summit>[];
    for (final ResultRow dataRow in resultSet) {
      int id = dataRow.getIntValue(SummitNamesTable.columnSummitId);
      String name = dataRow.getStringValue(SummitNamesTable.columnName);
      summits.add(Summit(id, name));
    }
    return summits;
  }

  @override
  Future<List<Route>> retrieveRoutesOfSummit(int summitId, RoutesFilterMode sortCriterion) async {
    const String averageRatingColumnName = 'rating'; // Name of the virtual column from the join

    /// Configure the query
    List<String> orderByColumns;
    switch (sortCriterion) {
      case RoutesFilterMode.name:
        orderByColumns = <String>['${RoutesTable.columnRouteName} ASC'];
      case RoutesFilterMode.grade:
        orderByColumns = <String>[
          '${RoutesTable.columnGradeAf} ASC',
          '${RoutesTable.columnGradeJump} ASC',
        ];
      case RoutesFilterMode.rating:
        orderByColumns = <String>['$averageRatingColumnName DESC'];
    }

    Query query = Query.join(
      <String>[RoutesTable.tableName, PostsTable.tableName],
      <String>['${RoutesTable.columnId} = ${PostsTable.columnRouteId}'],
      <String>[
        RoutesTable.columnId,
        RoutesTable.columnRouteName,
        RoutesTable.columnRouteGrade,
        "AVG(${PostsTable.columnRating}) AS '$averageRatingColumnName'",
      ],
    );
    query.setWhereCondition('${RoutesTable.columnSummitId} = ?', <Object>[summitId]);
    query.groupByColumns = <String>[
      RoutesTable.columnId,
      RoutesTable.columnRouteName,
      RoutesTable.columnRouteGrade,
    ];
    query.orderByColumns = orderByColumns;

    // Execute the query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Route> routes = <Route>[];
    for (final ResultRow dataRow in resultSet) {
      int routeId = dataRow.getIntValue(RoutesTable.columnId);
      String name = dataRow.getStringValue(RoutesTable.columnRouteName);
      String grade = dataRow.getStringValue(RoutesTable.columnRouteGrade);
      // The returned 'rating' is null for routes with no posts at all
      double? rating = dataRow.getOptDoubleValue(averageRatingColumnName);
      routes.add(Route(routeId, name, grade, rating));
    }
    return routes;
  }

  @override
  Future<Route> retrieveRoute(int routeDataId) async {
    Query query = Query.table(RoutesTable.tableName, <String>[
      RoutesTable.columnId,
      RoutesTable.columnRouteName,
      RoutesTable.columnRouteGrade,
    ]);
    query.setWhereCondition('${RoutesTable.columnId} = ?', <int>[routeDataId]);

    List<ResultRow> resultSet = await _repository.executeQuery(query);

    int id = resultSet[0].getIntValue(RoutesTable.columnId);
    String name = resultSet[0].getStringValue(RoutesTable.columnRouteName);
    String grade = resultSet[0].getStringValue(RoutesTable.columnRouteGrade);
    return Route(id, name, grade, 0);
  }

  @override
  Future<List<Post>> retrievePostsOfRoute(int routeId, PostsFilterMode sortCriterion) async {
    _logger.debug('Retrieving posts for route "$routeId", sorted by $sortCriterion');

    // Configure the query
    String orderByColumn = '${PostsTable.columnPostDate} ';
    if (sortCriterion == PostsFilterMode.newestFirst) {
      orderByColumn += 'DESC';
    } else {
      orderByColumn += 'ASC';
    }

    Query query = Query.table(PostsTable.tableName, <String>[
      PostsTable.columnId,
      PostsTable.columnUserName,
      PostsTable.columnPostDate,
      PostsTable.columnComment,
      PostsTable.columnRating,
    ]);
    query.setWhereCondition('${PostsTable.columnRouteId} = ?', <int>[routeId]);
    query.orderByColumns = <String>[orderByColumn];

    // Run the database query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Post> posts = <Post>[];
    for (final ResultRow dataRow in resultSet) {
      String name = dataRow.getStringValue(PostsTable.columnUserName);
      String timestamp = dataRow.getStringValue(PostsTable.columnPostDate);
      String comment = dataRow.getStringValue(PostsTable.columnComment);
      int rating = dataRow.getIntValue(PostsTable.columnRating);
      DateTime postDate = DateTime.parse(timestamp);
      posts.add(Post(name, postDate, comment, rating));
    }
    return posts;
  }
}
