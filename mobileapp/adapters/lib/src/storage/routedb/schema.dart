///
/// Contains information about the database schema, e.g. table and column names.
///
/// WARNING: This file has been generated, do not edit it manually because your changes may get
/// lost! To re-generate, run `invoke generate-schema routedb` from the scraper environment.
///
library;

import '../version.dart';

/// The schema version currently supported (and required) by this app.
final Version supportedSchemaVersion = Version(1, 0);

/// Table containing some static metadata about the database itself.
///
/// Must contain exactly one row.
class DatabaseMetadataTable {
  /// Name of the table.
  static const String tableName = 'database_metadata';

  /// The name of the 'schema_version_major' INTEGER column:
  /// Major part of the schema version (corresponding to incompatible changes).
  static const String columnSchemaVersionMajor = '$tableName.schema_version_major';

  /// The name of the 'schema_version_minor' INTEGER column:
  /// Minor part of the schema version (corresponding to backward-compatible changes).
  static const String columnSchemaVersionMinor = '$tableName.schema_version_minor';

  /// The name of the 'compile_time' TEXT column:
  /// Date and time this database has been created.
  ///
  /// This is an ISO 8601 string value (i.e. something like "YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM")
  /// and must include proper time zone information.
  static const String columnCompileTime = '$tableName.compile_time';

  /// The name of the 'vendor' TEXT column:
  /// Vendor identification label of the database provider.
  /// This is an arbitrary (even empty) display string to distinguish different database sources.
  static const String columnVendor = '$tableName.vendor';
}

/// All names of all summits.
///
/// As a single summit can have multiple names, this table assigns specific names strings to summits.
/// Each summit must have exactly one official name assigned, but there may be several (including no)
/// additional names as well.
///
/// This table is designed for both searching by name and retrieving the name(s) of summits.
class SummitNamesTable {
  /// Name of the table.
  static const String tableName = 'summit_names';

  /// The name of the 'name' TEXT column:
  /// A single summit name string.
  static const String columnName = '$tableName.name';

  /// The name of the 'usage' INTEGER column:
  /// Usage of this name string (for this summit):
  /// 0 = Official name (the name given and used by local authorities, usually the default)
  /// 1 = Alternate name (e.g. a well-known "nickname" or an old name)
  static const String columnUsage = '$tableName.usage';

  /// The name of the 'summit_id' INTEGER column:
  /// ID of the summit this name is assigned to.
  static const String columnSummitId = '$tableName.summit_id';
}

/// Table containing all summit data.
///
/// The summit names are stored in the `summit_names` table. Each summit is guaranteed to have
/// exactly one official name assigned.
///
/// To store geographical coordinate values as integer values, their decimal representation is
/// multiplied by 10.000.000 to support the same precision as the OSM database (7 decimal places,
/// ~1 cm). Positive values are N/E, negative ones are S/W. For example, (50,9170936, 14,1992389) is
/// stored as (509170936, 141992389).
///
/// See also: https://wiki.openstreetmap.org/wiki/Precision_of_coordinates
class SummitsTable {
  /// Name of the table.
  static const String tableName = 'summits';

  /// The name of the 'id' INTEGER column:
  /// Summit ID, unique within this database.
  static const String columnId = '$tableName.id';

  /// The name of the 'latitude' INTEGER column:
  /// The latitude value of the geographical position.
  static const String columnLatitude = '$tableName.latitude';

  /// The name of the 'longitude' INTEGER column:
  /// The longitude value of the geographical position.
  static const String columnLongitude = '$tableName.longitude';
}

/// Table containing all routes.
///
/// Route names are unique for each summit, therefore route data from different sources can be
/// merged based on the (summit, route name) combination.
///
/// Routes have several grades describing their difficulty, depending on the route characteristics
/// (e.g. does it include a jump?), the climbing style (e.g. "all free" or "redpoint") and also on
/// each other:
///  - A route without a jumping grade is usually climbed without having to jump
///  - A route with both grades contains a single jump within its climbing parts
///  - A route with only a jumping grade consists of a single jump only
///  - The AF/RP ratings of a route with OU grade require some additional support
///
/// Grades are represented by integer numbers, with 1 being the lowest (or "easiest") possible
/// rating and without an upper bound. Each step in the corresponding scale system increases the
/// value by one, so e.g. the saxon grade VIIb is stored as 8 and the UIAA grade IV is stored as 6.
/// 0 can be used when a certain grade doesn't apply to a route at all, e.g. when there is no jump.
class RoutesTable {
  /// Name of the table.
  static const String tableName = 'routes';

  /// The name of the 'id' INTEGER column:
  /// Route ID, unique within this database.
  static const String columnId = '$tableName.id';

  /// The name of the 'summit_id' INTEGER column:
  /// ID of the summit this route is assigned to. Foreign key to the summits table.
  static const String columnSummitId = '$tableName.summit_id';

  /// The name of the 'route_name' TEXT column:
  /// Name of this route. Unique within this summit, but different summits may have routes with
  /// identical names (e.g. "AW").
  static const String columnRouteName = '$tableName.route_name';

  /// The name of the 'route_grade' TEXT column:
  /// Grade label. Deprecated, please use the more fine-grained grade columns instead.
  static const String columnRouteGrade = '$tableName.route_grade';

  /// The name of the 'grade_af' INTEGER column:
  /// The grade that applies when climbing this route in the AF ("alles frei", i.e. "all free")
  /// style, i.e. without any belaying (no rope, no abseiling). Set to 0 when it is just a single
  /// jump.
  static const String columnGradeAf = '$tableName.grade_af';

  /// The name of the 'grade_rp' INTEGER column:
  /// The grade that applies when climbing this route in the RP ("Rotpunkt", i.e. "redpoint")
  /// style. Set to 0 when it is just a single jump.
  static const String columnGradeRp = '$tableName.grade_rp';

  /// The name of the 'grade_ou' INTEGER column:
  /// The grade that applies when climbing this route in the OU ("ohne Unterstützung", i.e.
  /// "without support") style, i.e. without using the support considered in the AF style
  /// grade. Set to 0 when the AF grade doesn't include any support.
  static const String columnGradeOu = '$tableName.grade_ou';

  /// The name of the 'grade_jump' INTEGER column:
  /// The grade of the jump within this route. Set to 0 when there is no need to jump.
  static const String columnGradeJump = '$tableName.grade_jump';

  /// The name of the 'stars' INTEGER column:
  /// The count of official stars assigend to this route. An increasing number of stars marks a
  /// route as "more beautiful". 0 is the default for regular routes.
  static const String columnStars = '$tableName.stars';

  /// The name of the 'danger' BOOLEAN column:
  /// True if the route is officially marked as "dangerous", false if not.
  static const String columnDanger = '$tableName.danger';
}

/// Table containing all posts that have been assigned to routes.
class PostsTable {
  /// Name of the table.
  static const String tableName = 'posts';

  /// The name of the 'id' INTEGER column:
  /// Post ID, unique within this database.
  static const String columnId = '$tableName.id';

  /// The name of the 'route_id' INTEGER column:
  /// ID of the route this post is assigned to. Foreign key to the routes table.
  static const String columnRouteId = '$tableName.route_id';

  /// The name of the 'user_name' TEXT column:
  /// Name of the post's author.
  static const String columnUserName = '$tableName.user_name';

  /// The name of the 'post_date' TEXT column:
  /// The date and time the post was published. ISO 8601 string value
  /// ("YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM").
  static const String columnPostDate = '$tableName.post_date';

  /// The name of the 'comment' TEXT column:
  /// The comment.
  static const String columnComment = '$tableName.comment';

  /// The name of the 'rating' INTEGER column:
  /// The rating the author assigned to the route this post corresponds to. This is a signed integer
  /// value in the range between -3 (extremely bad/dangerous) to 3 (extremely outstanding/great).
  static const String columnRating = '$tableName.rating';
}
