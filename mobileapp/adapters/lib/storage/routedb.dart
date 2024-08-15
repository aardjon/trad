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

import '../boundaries/repositories/database.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.adapters.storage.routedb');

/// Implementation of the storage adapter used by the core to interact with the route DB repository.
class RouteDbStorage implements RouteDbStorageBoundary {
  /// The route db data repository.
  final RelationalDatabaseBoundary _repository;

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  RouteDbStorage(DependencyProvider dependencyProvider)
      : _repository = dependencyProvider.provide<RelationalDatabaseBoundary>();

  @override
  void initStorage(String routeDbFile) {
    _repository.connect(routeDbFile);
    // TODO(aardjon): Check schema version!
  }

  @override
  Future<Summit> retrieveSummit(int summitDataId) async {
    List<ResultRow> resultSet = await _repository.queryTable(
      _SummitTable.tableName,
      <String>[_SummitTable.columnId, _SummitTable.columnName],
      whereClause: '${_SummitTable.columnId} = ?',
      whereParameters: <int>[summitDataId],
    );
    int? id = resultSet[0].getIntValue(_SummitTable.columnId);
    String? name = resultSet[0].getStringValue(_SummitTable.columnName);
    return Summit(id!, name!);
  }

  @override
  Future<List<Summit>> retrieveSummits([String? nameFilter]) async {
    // Build the WHERE clause if filtering is requested
    String? whereClause;
    List<Object?> whereParameters = <Object?>[];
    if (nameFilter != null) {
      _logger.debug('Retrieving filtered summit list for "$nameFilter"');
      String filterColumn = _SummitTable.columnName;
      whereClause = '$filterColumn LIKE ?';
      whereParameters.add('%$nameFilter%');
    } else {
      _logger.debug('Retrieving complete summit list');
    }
    // Run the database query
    List<ResultRow> resultSet = await _repository.queryTable(
      _SummitTable.tableName,
      <String>[_SummitTable.columnId, _SummitTable.columnName],
      whereClause: whereClause,
      whereParameters: whereParameters,
      orderBy: _SummitTable.columnName,
    );
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

    String orderByClause;
    switch (sortCriterion) {
      case RoutesFilterMode.name:
        orderByClause = '${_RoutesTable.columnName} ASC';
      case RoutesFilterMode.grade:
        orderByClause = '${_RoutesTable.columnGrade} ASC';
      case RoutesFilterMode.rating:
        orderByClause = '$averageRatingColumnName DESC';
    }

    List<ResultRow> resultSet = await _repository.queryJoin(
      _RoutesTable.tableName,
      _PostsTable.tableName,
      '${_RoutesTable.columnRouteId} = ${_PostsTable.columnRouteId}',
      <String>[
        _RoutesTable.columnRouteId,
        _RoutesTable.columnName,
        _RoutesTable.columnGrade,
        "AVG(${_PostsTable.columnRating}) AS '$averageRatingColumnName'",
      ],
      whereClause: '${_RoutesTable.columnSummitId} = ?',
      whereParameters: <Object>[summitId],
      groupBy: <String>[
        _RoutesTable.columnRouteId,
        _RoutesTable.columnName,
        _RoutesTable.columnGrade,
      ],
      orderBy: orderByClause,
    );
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
    List<ResultRow> resultSet = await _repository.queryTable(
      _RoutesTable.tableName,
      <String>[_RoutesTable.columnRouteId, _RoutesTable.columnName, _RoutesTable.columnGrade],
      whereClause: '${_RoutesTable.columnRouteId} = ?',
      whereParameters: <int>[routeDataId],
    );
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
    // Build the WHERE and ORDER BY clauses
    String whereClause = '${_PostsTable.columnRouteId} = ?';
    String orderByClause = '${_PostsTable.columnTimestamp} ';
    if (sortCriterion == PostsFilterMode.newestFirst) {
      orderByClause += 'DESC';
    } else {
      orderByClause += 'ASC';
    }
    // Run the database query
    List<ResultRow> resultSet = await _repository.queryTable(
      _PostsTable.tableName,
      <String>[
        _PostsTable.columnPostId,
        _PostsTable.columnName,
        _PostsTable.columnTimestamp,
        _PostsTable.columnComment,
        _PostsTable.columnRating,
      ],
      whereClause: whereClause,
      whereParameters: <int>[routeId],
      orderBy: orderByClause,
    );
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
