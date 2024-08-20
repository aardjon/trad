///
/// Definition of the route DB storage adapter.
///
library;

import 'package:core/boundaries/storage/routedb.dart';
import 'package:core/entities/post.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:core/entities/summit.dart';
import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';
import 'package:crosscuttings/path.dart';

import '../boundaries/paths.dart';
import '../boundaries/repositories/database.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.adapters.storage.routedb');

/// Implementation of the storage adapter used by the core to interact with the route DB repository.
class RouteDbStorage implements RouteDbStorageBoundary {
  /// The filename of the route database file (within the application data dir).
  static const String _dbFileName = 'peaks.sqlite';

  /// Interface to the component used to retrieve environment specific path information.
  final PathProviderBoundary _pathProviderBoundary;

  /// The route db data repository.
  final RelationalDatabaseBoundary _repository;

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  RouteDbStorage(DependencyProvider dependencyProvider)
      : _pathProviderBoundary = dependencyProvider.provide<PathProviderBoundary>(),
        _repository = dependencyProvider.provide<RelationalDatabaseBoundary>();

  @override
  Future<void> initStorage() async {
    Path dataDir = await _pathProviderBoundary.getAppDataDir();
    String connectionString = dataDir.join(_dbFileName).toString();
    _logger.info('Connecting to route database at: $connectionString');
    _repository.connect(connectionString, readOnly: true);
    // TODO(aardjon): Check schema version!
  }

  @override
  Future<Summit> retrieveSummit(int summitDataId) async {
    Query query = Query.table(
      _SummitTable.tableName,
      <String>[_SummitTable.columnId, _SummitTable.columnName],
    );
    query.setWhereCondition('${_SummitTable.columnId} = ?', <int>[summitDataId]);
    List<ResultRow> resultSet = await _repository.executeQuery(query);
    int? id = resultSet[0].getIntValue(_SummitTable.columnId);
    String? name = resultSet[0].getStringValue(_SummitTable.columnName);
    return Summit(id!, name!);
  }

  @override
  Future<List<Summit>> retrieveSummits([String? nameFilter]) async {
    // Configure the query
    Query query = Query.table(
      _SummitTable.tableName,
      <String>[_SummitTable.columnId, _SummitTable.columnName],
    );
    if (nameFilter != null) {
      _logger.debug('Retrieving filtered summit list for "$nameFilter"');
      query.setWhereCondition('${_SummitTable.columnName} LIKE ?', <String>['%$nameFilter%']);
    } else {
      _logger.debug('Retrieving complete summit list');
    }
    query.orderByColumns = <String>[_SummitTable.columnName];

    // Run the database query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Summit> summits = <Summit>[];
    for (final ResultRow dataRow in resultSet) {
      int? id = dataRow.getIntValue(_SummitTable.columnId);
      String? name = dataRow.getStringValue(_SummitTable.columnName);
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
        orderByColumn = '${_RoutesTable.columnName} ASC';
      case RoutesFilterMode.grade:
        orderByColumn = '${_RoutesTable.columnGrade} ASC';
      case RoutesFilterMode.rating:
        orderByColumn = '$averageRatingColumnName DESC';
    }

    Query query = Query.join(
      <String>[_RoutesTable.tableName, _PostsTable.tableName],
      <String>['${_RoutesTable.columnRouteId} = ${_PostsTable.columnRouteId}'],
      <String>[
        _RoutesTable.columnRouteId,
        _RoutesTable.columnName,
        _RoutesTable.columnGrade,
        "AVG(${_PostsTable.columnRating}) AS '$averageRatingColumnName'",
      ],
    );
    query.setWhereCondition('${_RoutesTable.columnSummitId} = ?', <Object>[summitId]);
    query.groupByColumns = <String>[
      _RoutesTable.columnRouteId,
      _RoutesTable.columnName,
      _RoutesTable.columnGrade,
    ];
    query.orderByColumns = <String>[orderByColumn];

    // Execute the query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Route> routes = <Route>[];
    for (final ResultRow dataRow in resultSet) {
      int? routeId = dataRow.getIntValue(_RoutesTable.columnRouteId);
      String? name = dataRow.getStringValue(_RoutesTable.columnName);
      String? grade = dataRow.getStringValue(_RoutesTable.columnGrade);
      double? rating = dataRow.getDoubleValue(averageRatingColumnName);
      routes.add(Route(routeId!, name!, grade!, rating));
    }
    return routes;
  }

  @override
  Future<Route> retrieveRoute(int routeDataId) async {
    Query query = Query.table(
      _RoutesTable.tableName,
      <String>[_RoutesTable.columnRouteId, _RoutesTable.columnName, _RoutesTable.columnGrade],
    );
    query.setWhereCondition('${_RoutesTable.columnRouteId} = ?', <int>[routeDataId]);

    List<ResultRow> resultSet = await _repository.executeQuery(query);

    int? id = resultSet[0].getIntValue(_RoutesTable.columnRouteId);
    String? name = resultSet[0].getStringValue(_RoutesTable.columnName);
    String? grade = resultSet[0].getStringValue(_RoutesTable.columnGrade);
    return Route(id!, name!, grade!, 0);
  }

  @override
  Future<List<Post>> retrievePostsOfRoute(
    int routeId,
    PostsFilterMode sortCriterion,
  ) async {
    _logger.debug('Retrieving posts for route "$routeId", sorted by $sortCriterion');

    // Configure the query
    String orderByColumn = '${_PostsTable.columnTimestamp} ';
    if (sortCriterion == PostsFilterMode.newestFirst) {
      orderByColumn += 'DESC';
    } else {
      orderByColumn += 'ASC';
    }

    Query query = Query.table(
      _PostsTable.tableName,
      <String>[
        _PostsTable.columnPostId,
        _PostsTable.columnName,
        _PostsTable.columnTimestamp,
        _PostsTable.columnComment,
        _PostsTable.columnRating,
      ],
    );
    query.setWhereCondition('${_PostsTable.columnRouteId} = ?', <int>[routeId]);
    query.orderByColumns = <String>[orderByColumn];

    // Run the database query
    List<ResultRow> resultSet = await _repository.executeQuery(query);

    // Convert and return the result data
    List<Post> posts = <Post>[];
    for (final ResultRow dataRow in resultSet) {
      String? name = dataRow.getStringValue(_PostsTable.columnName);
      String? timestamp = dataRow.getStringValue(_PostsTable.columnTimestamp);
      String? comment = dataRow.getStringValue(_PostsTable.columnComment);
      int? rating = dataRow.getIntValue(_PostsTable.columnRating);
      DateTime postDate = DateTime.parse(timestamp!);
      posts.add(Post(name!, postDate, comment!, rating!));
    }
    return posts;
  }
}

/// Represents the `summits` table containing all summit data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the summits table. Always use these constants when referring to this table or its columns
/// to make future schema changes easier.
class _SummitTable {
  /// Name of the table.
  static const String tableName = 'peaks';

  /// Name of the ID column.
  static const String columnId = 'id';

  /// Name of the summit name column.
  static const String columnName = 'peak_name';
}

/// Represents the `routes` table containing all route data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the routes table. Always use these constants when referring to this table or its columns
/// to make future schema changes easier.
class _RoutesTable {
  /// Name of the table.
  static const String tableName = 'routes';

  /// Name of the route ID column.
  static const String columnRouteId = '$tableName.id';

  /// Name of the summit ID column (referencing the summit a route belongs to).
  static const String columnSummitId = '$tableName.peak_id';

  /// Name of the route name column.
  static const String columnName = '$tableName.route_name';

  /// Name of the route grade column.
  static const String columnGrade = '$tableName.route_grade';
}

/// Represents the `posts` table containing all post data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the routes table. Always use these constants when referring to this table or its columns
/// to make future schema changes easier.
class _PostsTable {
  /// Name of the table.
  static const String tableName = 'posts';

  /// Name of the post ID column
  static const String columnPostId = '$tableName.id';

  /// Name of the route ID column (referencing the route a post belongs to).
  static const String columnRouteId = '$tableName.route_id';

  /// Name of the user name column.
  static const String columnName = '$tableName.user_name';

  /// Name of the timestamp column.
  static const String columnTimestamp = '$tableName.post_date';

  /// Name of the comment column.
  static const String columnComment = '$tableName.comment';

  /// Name of the user rating column.
  static const String columnRating = '$tableName.rating';
}
