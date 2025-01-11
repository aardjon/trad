///
/// Contains information about the database schema, e.g. table and column names.
///
library;

import '../version.dart';

/// The schema version currently supported (and required) by this app.
final Version supportedSchemaVersion = Version(1, 0);

/// Contains some static metadata about the database itself. Contains exactly one row only which
/// never changes.
class MetadataTable {
  /// Name of the table.
  static const String tableName = 'database_metadata';

  /// Name of the major schema version column.
  static const String columnMajorVersion = '$tableName.schema_version_major';

  /// Name of the minor schema version column.
  static const String columnMinorVersion = '$tableName.schema_version_minor';

  /// Name of the compile time column.
  static const String columnCompileTime = '$tableName.compile_time';

  /// Name of the vendor column.
  static const String columnVendor = '$tableName.vendor';
}

/// Represents the `summits` table containing all summit data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the summits table. Always use these constants when referring to this table or its columns
/// to make future schema changes easier.
class SummitTable {
  /// Name of the table.
  static const String tableName = 'summits';

  /// Name of the ID column.
  static const String columnId = '$tableName.id';

  /// Name of the summit name column.
  static const String columnName = '$tableName.summit_name';

  /// Name of the latitude column.
  static const String columnLatitude = '$tableName.latitude';

  /// Name of the longitude column.
  static const String columnLongitude = '$tableName.longitude';
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
  static const String columnSummitId = '$tableName.summit_id';

  /// Name of the route name column.
  static const String columnName = '$tableName.route_name';

  /// Name of the grade name column (deprecated!).
  static const String columnGrade = '$tableName.route_grade';

  /// Name of the "af" climbing grade column.
  static const String columnGradeAf = '$tableName.grade_af';

  /// Name of the "ou" climbing grade column.
  static const String columnGradeOu = '$tableName.grade_ou';

  /// Name of the "rp" climbing grade column.
  static const String columnGradeRp = '$tableName.grade_rp';

  /// Name of the jumping grade column.
  static const String columnJumpGrade = '$tableName.grade_jump';

  /// Name of the star count column.
  static const String columnGradeStars = '$tableName.grade_stars';

  /// Name of the danger (exclamation) mark count column.
  static const String columnGradeDanger = '$tableName.grade_danger';
}

/// Represents the `posts` table containing all post data.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to the posts table. Always use these constants when referring to this table or its columns
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
