///
/// Definition of the route DB storage adapter.
///
library;

import 'dart:io';

import 'package:core/boundaries/storage/routedb.dart';
import 'package:core/entities/post.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:core/entities/summit.dart';
import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/paths.dart';
import '../boundaries/repositories/database.dart';
import '../boundaries/repositories/filesystem.dart';
import '../src/storage/routedb/schema.dart';

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
    _repository.connect(connectionString, readOnly: true);
    // TODO(aardjon): Check schema version!
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
        'Unable to import "{filePath}" because it does not exist.',
      );
    }

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
  Future<Summit> retrieveSummit(int summitDataId) async {
    Query query = Query.table(
      SummitTable.tableName,
      <String>[SummitTable.columnId, SummitTable.columnName],
    );
    query.setWhereCondition('${SummitTable.columnId} = ?', <int>[summitDataId]);
    List<ResultRow> resultSet = await _repository.executeQuery(query);
    int? id = resultSet[0].getIntValue(SummitTable.columnId);
    String? name = resultSet[0].getStringValue(SummitTable.columnName);
    return Summit(id!, name!);
  }

  @override
  Future<List<Summit>> retrieveSummits([String? nameFilter]) async {
    // Configure the query
    Query query = Query.table(
      SummitTable.tableName,
      <String>[SummitTable.columnId, SummitTable.columnName],
    );
    if (nameFilter != null) {
      _logger.debug('Retrieving filtered summit list for "$nameFilter"');
      query.setWhereCondition('${SummitTable.columnName} LIKE ?', <String>['%$nameFilter%']);
    } else {
      _logger.debug('Retrieving complete summit list');
    }
    query.orderByColumns = <String>[SummitTable.columnName];

    // Run the database query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Summit> summits = <Summit>[];
    for (final ResultRow dataRow in resultSet) {
      int? id = dataRow.getIntValue(SummitTable.columnId);
      String? name = dataRow.getStringValue(SummitTable.columnName);
      summits.add(Summit(id!, name!));
    }
    return summits;
  }

  @override
  Future<List<Route>> retrieveRoutesOfSummit(
    int summitId,
    RoutesFilterMode sortCriterion,
  ) async {
    const String averageRatingColumnName = 'rating'; // Name of the virtual column from the join

    /// Configure the query
    String orderByColumn;
    switch (sortCriterion) {
      case RoutesFilterMode.name:
        orderByColumn = '${RoutesTable.columnName} ASC';
      case RoutesFilterMode.grade:
        orderByColumn = '${RoutesTable.columnGrade} ASC';
      case RoutesFilterMode.rating:
        orderByColumn = '$averageRatingColumnName DESC';
    }

    Query query = Query.join(
      <String>[RoutesTable.tableName, PostsTable.tableName],
      <String>['${RoutesTable.columnRouteId} = ${PostsTable.columnRouteId}'],
      <String>[
        RoutesTable.columnRouteId,
        RoutesTable.columnName,
        RoutesTable.columnGrade,
        "AVG(${PostsTable.columnRating}) AS '$averageRatingColumnName'",
      ],
    );
    query.setWhereCondition('${RoutesTable.columnSummitId} = ?', <Object>[summitId]);
    query.groupByColumns = <String>[
      RoutesTable.columnRouteId,
      RoutesTable.columnName,
      RoutesTable.columnGrade,
    ];
    query.orderByColumns = <String>[orderByColumn];

    // Execute the query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Route> routes = <Route>[];
    for (final ResultRow dataRow in resultSet) {
      int? routeId = dataRow.getIntValue(RoutesTable.columnRouteId);
      String? name = dataRow.getStringValue(RoutesTable.columnName);
      String? grade = dataRow.getStringValue(RoutesTable.columnGrade);
      double? rating = dataRow.getDoubleValue(averageRatingColumnName);
      routes.add(Route(routeId!, name!, grade!, rating));
    }
    return routes;
  }

  @override
  Future<Route> retrieveRoute(int routeDataId) async {
    Query query = Query.table(
      RoutesTable.tableName,
      <String>[RoutesTable.columnRouteId, RoutesTable.columnName, RoutesTable.columnGrade],
    );
    query.setWhereCondition('${RoutesTable.columnRouteId} = ?', <int>[routeDataId]);

    List<ResultRow> resultSet = await _repository.executeQuery(query);

    int? id = resultSet[0].getIntValue(RoutesTable.columnRouteId);
    String? name = resultSet[0].getStringValue(RoutesTable.columnName);
    String? grade = resultSet[0].getStringValue(RoutesTable.columnGrade);
    return Route(id!, name!, grade!, 0);
  }

  @override
  Future<List<Post>> retrievePostsOfRoute(
    int routeId,
    PostsFilterMode sortCriterion,
  ) async {
    _logger.debug('Retrieving posts for route "$routeId", sorted by $sortCriterion');

    // Configure the query
    String orderByColumn = '${PostsTable.columnTimestamp} ';
    if (sortCriterion == PostsFilterMode.newestFirst) {
      orderByColumn += 'DESC';
    } else {
      orderByColumn += 'ASC';
    }

    Query query = Query.table(
      PostsTable.tableName,
      <String>[
        PostsTable.columnPostId,
        PostsTable.columnName,
        PostsTable.columnTimestamp,
        PostsTable.columnComment,
        PostsTable.columnRating,
      ],
    );
    query.setWhereCondition('${PostsTable.columnRouteId} = ?', <int>[routeId]);
    query.orderByColumns = <String>[orderByColumn];

    // Run the database query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Post> posts = <Post>[];
    for (final ResultRow dataRow in resultSet) {
      String? name = dataRow.getStringValue(PostsTable.columnName);
      String? timestamp = dataRow.getStringValue(PostsTable.columnTimestamp);
      String? comment = dataRow.getStringValue(PostsTable.columnComment);
      int? rating = dataRow.getIntValue(PostsTable.columnRating);
      DateTime postDate = DateTime.parse(timestamp!);
      posts.add(Post(name!, postDate, comment!, rating!));
    }
    return posts;
  }
}
