"""
Contains information about the database schema, e.g. table structure and column names.

WARNING: This file has been generated, do not edit it manually because your changes may get lost!
To re-generate, run `invoke generate-schema routedb`.
"""

from collections.abc import Sequence
from enum import IntEnum
from typing import Final, override

from trad.application.boundaries.database import EntityName, SqlStatement
from trad.application.pipes.schemabase import TableSchema


class DatabaseMetadataTable(TableSchema):
    """
    Table containing some static metadata about the database itself.

    Must contain exactly one row.
    """

    TABLE_NAME = "database_metadata"
    """ Name of the table. """

    COLUMN_SCHEMA_VERSION_MAJOR: Final = "schema_version_major"
    """
    The name of the 'schema_version_major' INTEGER column:
    Major part of the schema version (corresponding to incompatible changes).
    """

    COLUMN_SCHEMA_VERSION_MINOR: Final = "schema_version_minor"
    """
    The name of the 'schema_version_minor' INTEGER column:
    Minor part of the schema version (corresponding to backward-compatible changes).
    """

    COLUMN_COMPILE_TIME: Final = "compile_time"
    """
    The name of the 'compile_time' TEXT column:
    Date and time this database has been created.

    This is an ISO 8601 string value (i.e. something like "YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM")
    and must include proper time zone information.
    """

    COLUMN_VENDOR: Final = "vendor"
    """
    The name of the 'vendor' TEXT column:
    Vendor identification label of the database provider.
    This is an arbitrary (even empty) display string to distinguish different database sources.
    """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def table_ddl(self) -> SqlStatement:
        return SqlStatement("""
        CREATE TABLE database_metadata (
            "schema_version_major" INTEGER NOT NULL,
            "schema_version_minor" INTEGER NOT NULL,
            "compile_time" TEXT NOT NULL,
            "vendor" TEXT NOT NULL,
            UNIQUE(schema_version_major, schema_version_minor, compile_time, vendor)
        );
        """)

    @override
    def index_ddl(self) -> list[SqlStatement]:
        return []


class SummitNamesTable(TableSchema):
    """
    All names of all summits.

    As a single summit can have multiple names, this table assigns specific names strings to summits.
    Each summit must have exactly one official name assigned, but there may be several (including no)
    additional names as well.

    This table is designed for both searching by name and retrieving the name(s) of summits.
    """

    TABLE_NAME = "summit_names"
    """ Name of the table. """

    COLUMN_NAME: Final = "name"
    """
    The name of the 'name' TEXT column:
    A single summit name string.
    """

    COLUMN_USAGE: Final = "usage"
    """
    The name of the 'usage' INTEGER column:
    Usage of this name string (for this summit):
    0 = Official name (the name given and used by local authorities, usually the default)
    1 = Alternate name (e.g. a well-known "nickname" or an old name)
    """

    COLUMN_SUMMIT_ID: Final = "summit_id"
    """
    The name of the 'summit_id' INTEGER column:
    ID of the summit this name is assigned to.
    """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def table_ddl(self) -> SqlStatement:
        return SqlStatement("""
        CREATE TABLE summit_names (
            "name" TEXT NOT NULL,
            "usage" INTEGER NOT NULL,
            "summit_id" INTEGER NOT NULL,
            PRIMARY KEY(summit_id, usage, name),
            FOREIGN KEY("summit_id") REFERENCES "summits" ("id") ON DELETE CASCADE
        );
        """)

    @override
    def index_ddl(self) -> list[SqlStatement]:
        return [
            SqlStatement(
                'CREATE INDEX "IdxSummitName" ON "summit_names" (name);',
            ),
        ]


class SummitsTable(TableSchema):
    """
    Table containing all summit data.

    The summit names are stored in the `summit_names` table. Each summit is guaranteed to have
    exactly one official name assigned.

    To store geographical coordinate values as integer values, their decimal representation is
    multiplied by 10.000.000 to support the same precision as the OSM database (7 decimal places,
    ~1 cm). Positive values are N/E, negative ones are S/W. For example, (50,9170936, 14,1992389) is
    stored as (509170936, 141992389).

    See also: https://wiki.openstreetmap.org/wiki/Precision_of_coordinates
    """

    TABLE_NAME = "summits"
    """ Name of the table. """

    COLUMN_ID: Final = "id"
    """
    The name of the 'id' INTEGER column:
    Summit ID, unique within this database.
    """

    COLUMN_LATITUDE: Final = "latitude"
    """
    The name of the 'latitude' INTEGER column:
    The latitude value of the geographical position.
    """

    COLUMN_LONGITUDE: Final = "longitude"
    """
    The name of the 'longitude' INTEGER column:
    The longitude value of the geographical position.
    """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def table_ddl(self) -> SqlStatement:
        return SqlStatement("""
        CREATE TABLE summits (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "latitude" INTEGER NOT NULL,
            "longitude" INTEGER NOT NULL
        );
        """)

    @override
    def index_ddl(self) -> list[SqlStatement]:
        return []


class RoutesTable(TableSchema):
    """
    Table containing all routes.

    Route names are unique for each summit, therefore route data from different sources can be
    merged based on the (summit, route name) combination.

    Routes have several grades describing their difficulty, depending on the route characteristics
    (e.g. does it include a jump?), the climbing style (e.g. "all free" or "redpoint") and also on
    each other:
     - A route without a jumping grade is usually climbed without having to jump
     - A route with both grades contains a single jump within its climbing parts
     - A route with only a jumping grade consists of a single jump only
     - The AF/RP ratings of a route with OU grade require some additional support

    Grades are represented by integer numbers, with 1 being the lowest (or "easiest") possible
    rating and without an upper bound. Each step in the corresponding scale system increases the
    value by one, so e.g. the saxon grade VIIb is stored as 8 and the UIAA grade IV is stored as 6.
    0 can be used when a certain grade doesn't apply to a route at all, e.g. when there is no jump.
    """

    TABLE_NAME = "routes"
    """ Name of the table. """

    COLUMN_ID: Final = "id"
    """
    The name of the 'id' INTEGER column:
    Route ID, unique within this database.
    """

    COLUMN_SUMMIT_ID: Final = "summit_id"
    """
    The name of the 'summit_id' INTEGER column:
    ID of the summit this route is assigned to. Foreign key to the summits table.
    """

    COLUMN_ROUTE_NAME: Final = "route_name"
    """
    The name of the 'route_name' TEXT column:
    Name of this route. Unique within this summit, but different summits may have routes with
    identical names (e.g. "AW").
    """

    COLUMN_ROUTE_GRADE: Final = "route_grade"
    """
    The name of the 'route_grade' TEXT column:
    Grade label. Deprecated, please use the more fine-grained grade columns instead.
    """

    COLUMN_GRADE_AF: Final = "grade_af"
    """
    The name of the 'grade_af' INTEGER column:
    The grade that applies when climbing this route in the AF ("alles frei", i.e. "all free")
    style, i.e. without any belaying (no rope, no abseiling). Set to 0 when it is just a single
    jump.
    """

    COLUMN_GRADE_RP: Final = "grade_rp"
    """
    The name of the 'grade_rp' INTEGER column:
    The grade that applies when climbing this route in the RP ("Rotpunkt", i.e. "redpoint")
    style. Set to 0 when it is just a single jump.
    """

    COLUMN_GRADE_OU: Final = "grade_ou"
    """
    The name of the 'grade_ou' INTEGER column:
    The grade that applies when climbing this route in the OU ("ohne Unterstützung", i.e.
    "without support") style, i.e. without using the support considered in the AF style
    grade. Set to 0 when the AF grade doesn't include any support.
    """

    COLUMN_GRADE_JUMP: Final = "grade_jump"
    """
    The name of the 'grade_jump' INTEGER column:
    The grade of the jump within this route. Set to 0 when there is no need to jump.
    """

    COLUMN_STARS: Final = "stars"
    """
    The name of the 'stars' INTEGER column:
    The count of official stars assigend to this route. An increasing number of stars marks a
    route as "more beautiful". 0 is the default for regular routes.
    """

    COLUMN_DANGER: Final = "danger"
    """
    The name of the 'danger' BOOLEAN column:
    True if the route is officially marked as "dangerous", false if not.
    """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def table_ddl(self) -> SqlStatement:
        return SqlStatement("""
        CREATE TABLE routes (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "summit_id" INTEGER NOT NULL,
            "route_name" TEXT NOT NULL,
            "route_grade" TEXT NOT NULL,
            "grade_af" INTEGER NOT NULL,
            "grade_rp" INTEGER NOT NULL,
            "grade_ou" INTEGER NOT NULL,
            "grade_jump" INTEGER NOT NULL,
            "stars" INTEGER NOT NULL,
            "danger" BOOLEAN NOT NULL,
            UNIQUE(summit_id, route_name, route_grade),
            FOREIGN KEY("summit_id") REFERENCES "summits" ("id") ON DELETE CASCADE
        );
        """)

    @override
    def index_ddl(self) -> list[SqlStatement]:
        return [
            SqlStatement(
                'CREATE INDEX "IdxRouteName" ON "routes" (route_name);',
            ),
        ]


class PostsTable(TableSchema):
    """
    Table containing all posts that have been assigned to routes.
    """

    TABLE_NAME = "posts"
    """ Name of the table. """

    COLUMN_ID: Final = "id"
    """
    The name of the 'id' INTEGER column:
    Post ID, unique within this database.
    """

    COLUMN_ROUTE_ID: Final = "route_id"
    """
    The name of the 'route_id' INTEGER column:
    ID of the route this post is assigned to. Foreign key to the routes table.
    """

    COLUMN_USER_NAME: Final = "user_name"
    """
    The name of the 'user_name' TEXT column:
    Name of the post's author.
    """

    COLUMN_POST_DATE: Final = "post_date"
    """
    The name of the 'post_date' TEXT column:
    The date and time the post was published. ISO 8601 string value
    ("YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM").
    """

    COLUMN_COMMENT: Final = "comment"
    """
    The name of the 'comment' TEXT column:
    The comment.
    """

    COLUMN_RATING: Final = "rating"
    """
    The name of the 'rating' INTEGER column:
    The rating the author assigned to the route this post corresponds to. This is a signed integer
    value in the range between -3 (extremely bad/dangerous) to 3 (extremely outstanding/great).
    """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def table_ddl(self) -> SqlStatement:
        return SqlStatement("""
        CREATE TABLE posts (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "route_id" INTEGER NOT NULL,
            "user_name" TEXT NOT NULL,
            "post_date" TEXT NOT NULL,
            "comment" TEXT NOT NULL,
            "rating" INTEGER NOT NULL,
            FOREIGN KEY("route_id") REFERENCES "routes" ("id") ON DELETE CASCADE
        );
        """)

    @override
    def index_ddl(self) -> list[SqlStatement]:
        return []


class DatabaseSchema:
    """
    Represents the whole database schema itself.
    """

    _MAJOR_VERSION: Final = 1
    """
    Major schema version.

    To be incremented for incompatible schema changes, i.e. the mobile app needs to be adapted to
    work with the new database. For example, the removal or renaming of column or tables.
    When incrementing [_MAJOR_VERSION], set [_MINOR_VERSION] back to 0.
    """

    _MINOR_VERSION: Final = 0
    """
    Minor schema version.

    To be incremented for backward-compatible schema changes, i.e. the mobile app can use the new
    database without adaptions (but may of course lack some new features/improvements). Examples:
     - Adding a new table or column with additional data
     - Adding a new index (improving performance)
    """

    def get_table_schemata(self) -> Sequence[TableSchema]:
        """
        Return all table definitions that are part of this schema version.
        """
        return (
            DatabaseMetadataTable(),
            SummitNamesTable(),
            SummitsTable(),
            RoutesTable(),
            PostsTable(),
        )

    def get_schema_version(self) -> tuple[int, int]:
        """Returns the version of this database schema as a tuple of (major, minor)."""
        return self._MAJOR_VERSION, self._MINOR_VERSION


class NameUsage(IntEnum):
    """
    Usage definition of a single name string.
    """

    official = 0
    """
    The corresponding name is the official name given and used by some authorities. It is used e.g.
    in the summit register. Each summit must have exactly one official name assigned.
    """

    alternate = 1
    """
    The corresponding name is a non-official but well-known and widely used alternative one. It can
    be e.g. a nickname, a historic or a colloquial name. A single summit can have any (including no)
    alternate names.
    """
