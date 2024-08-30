///
/// Contains information about the database schema, e.g. table and column names.
///
library;

/// Represents the `summits` table containing all summit data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the summits table. Always use these constants when referring to this table or its columns
/// to make future schema changes easier.
class SummitTable {
  /// Name of the table.
  static const String tableName = 'peaks';

  /// Name of the ID column.
  static const String columnId = '$tableName.id';

  /// Name of the summit name column.
  static const String columnName = '$tableName.peak_name';
}

/// Represents the `routes` table containing all route data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the routes table. Always use these constants when referring to this table or its columns
/// to make future schema changes easier.
class RoutesTable {
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
class PostsTable {
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
