"""
Contains information about the database schema, e.g. table structure and column names.
"""

from abc import ABCMeta, abstractmethod
from typing import Final, override

from trad.adapters.boundaries.database.common import EntityName
from trad.adapters.boundaries.database.structure import (
    ColumnDefinition,
    ColumnType,
    IndexDefinition,
    Reference,
)


class TableSchema(metaclass=ABCMeta):
    """
    Base class and interface for the definition of a single database table.
    Each derived class specifies all features of a physical table.
    """

    @abstractmethod
    def table_name(self) -> EntityName:
        """Name of the table."""

    @abstractmethod
    def column_specification(self) -> list[ColumnDefinition]:
        """Definition of this table's columns."""

    @abstractmethod
    def indices(self) -> list[IndexDefinition]:
        """
        List of indices on this table. All columns within the index specification must of course be
        defined within [column_specification()].
        """

    @abstractmethod
    def primary_key(self) -> list[EntityName]:
        """
        List of all columns (names) that are part of the primary key (in that order). All columns
        must be defined within [column_specification()], of course.
        """

    @abstractmethod
    def unique_constraints(self) -> list[list[EntityName]]:
        """
        List of unique constraints for this table. Each item is a list of columns whose combined
        values shall be unique. All columns must be defined within [column_specification()], of
        course.
        """


class DbMetadataTable(TableSchema):
    """
    Represents the "database_metadata" table containing some static metadata. Contains exactly one
    row only.
    """

    TABLE_NAME = "database_metadata"
    """ Name of the table. """

    COLUMN_SCHEMA_VERSION_MAJOR: Final = "schema_version_major"
    """ Name of the major schema version column. """

    COLUMN_SCHEMA_VERSION_MINOR: Final = "schema_version_minor"
    """ Name of the minor schema version column. """

    COLUMN_COMPILE_TIME: Final = "compile_time"
    """ Name of the compile time column. """

    COLUM_VENDOR: Final = "vendor"
    """ Name of the vendor string column. """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def column_specification(self) -> list[ColumnDefinition]:
        return [
            ColumnDefinition(self.COLUMN_SCHEMA_VERSION_MAJOR, ColumnType.INTEGER, nullable=False),
            ColumnDefinition(self.COLUMN_SCHEMA_VERSION_MINOR, ColumnType.INTEGER, nullable=False),
            ColumnDefinition(self.COLUMN_COMPILE_TIME, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUM_VENDOR, ColumnType.STRING, nullable=False),
        ]

    @override
    def indices(self) -> list[IndexDefinition]:
        return []

    @override
    def primary_key(self) -> list[EntityName]:
        return []

    @override
    def unique_constraints(self) -> list[list[EntityName]]:
        return []


class SummitsTable(TableSchema):
    """
    Represents the `summits` table containing all summit data.

    The main purpose of this class is to provide a namespace with all structural information of
    the summits table, as well as string constants for the column names. Always use these constants
    when referring to this table or its columns to make future schema changes easier.
    """

    TABLE_NAME = "summits"
    """ Name of the table. """

    COLUMN_ID: Final = "id"
    """ Name of the ID column. """

    COLUMN_NAME: Final = "summit_name"
    """ Name of the summit name column. """

    COLUMN_LATITUDE: Final = "latitude"
    """ Name of the latitude column. """

    COLUMN_LONGITUDE: Final = "longitude"
    """ Name of the longitude column. """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def column_specification(self) -> list[ColumnDefinition]:
        return [
            ColumnDefinition(
                self.COLUMN_ID, ColumnType.INTEGER, nullable=False, autoincrement=True
            ),
            ColumnDefinition(self.COLUMN_NAME, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUMN_LATITUDE, ColumnType.INTEGER, nullable=False),
            ColumnDefinition(self.COLUMN_LONGITUDE, ColumnType.INTEGER, nullable=False),
        ]

    @override
    def indices(self) -> list[IndexDefinition]:
        return [IndexDefinition(name="IdxSummitName", column_names=[self.COLUMN_NAME])]

    @override
    def primary_key(self) -> list[EntityName]:
        return [self.COLUMN_ID]

    @override
    def unique_constraints(self) -> list[list[EntityName]]:
        return [[self.COLUMN_NAME]]


class RoutesTable(TableSchema):
    """
    Represents the `routes` table containing all route data.

    The main purpose of this class is to provide a namespace with all structural information of
    the routes table, as well as string constants for the column names. Always use these constants
    when referring to this table or its columns to make future schema changes easier.
    """

    TABLE_NAME: Final = "routes"
    """ Name of the table. """

    COLUMN_ROUTE_ID: Final = "id"
    """ Name of the route ID column. """

    COLUMN_SUMMIT_ID: Final = "summit_id"
    """ Name of the summit ID column (referencing the summit a route belongs to). """

    COLUMN_NAME: Final = "route_name"
    """ Name of the route name column. """

    COLUMN_GRADE: Final = "route_grade"
    """ Name of the grade name column (deprecated!). """

    COLUMN_GRADE_AF: Final = "grade_af"
    """ Name of the 'af' climbing grade column. """

    COLUMN_GRADE_RP: Final = "grade_rp"
    """ Name of the 'rp' climbing grade column. """

    COLUMN_GRADE_OU: Final = "grade_ou"
    """ Name of the 'ou' climbing grade column. """

    COLUMN_GRADE_JUMP: Final = "grade_jump"
    """ Name of the jumping grade column. """

    COLUMN_STARS: Final = "stars"
    """ Name of the star count column. """

    COLUMN_DANGER: Final = "danger"
    """ Name of the danger (exclamation) mark count column. """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def column_specification(self) -> list[ColumnDefinition]:
        return [
            ColumnDefinition(
                self.COLUMN_ROUTE_ID, ColumnType.INTEGER, nullable=False, autoincrement=True
            ),
            ColumnDefinition(
                self.COLUMN_SUMMIT_ID,
                ColumnType.INTEGER,
                nullable=False,
                reference=Reference(
                    SummitsTable.TABLE_NAME, SummitsTable.COLUMN_ID, delete_action="CASCADE"
                ),
            ),
            ColumnDefinition(self.COLUMN_NAME, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUMN_GRADE, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUMN_GRADE_AF, ColumnType.INTEGER, nullable=True),
            ColumnDefinition(self.COLUMN_GRADE_RP, ColumnType.INTEGER, nullable=True),
            ColumnDefinition(self.COLUMN_GRADE_OU, ColumnType.INTEGER, nullable=True),
            ColumnDefinition(self.COLUMN_GRADE_JUMP, ColumnType.INTEGER, nullable=True),
            ColumnDefinition(self.COLUMN_STARS, ColumnType.INTEGER, nullable=False),
            ColumnDefinition(self.COLUMN_DANGER, ColumnType.BOOLEAN, nullable=False),
        ]

    @override
    def indices(self) -> list[IndexDefinition]:
        return [IndexDefinition(name="IdxRouteName", column_names=[self.COLUMN_NAME])]

    @override
    def primary_key(self) -> list[EntityName]:
        return [self.COLUMN_ROUTE_ID]

    @override
    def unique_constraints(self) -> list[list[EntityName]]:
        return [[self.COLUMN_SUMMIT_ID, self.COLUMN_NAME, self.COLUMN_GRADE]]


class PostsTable(TableSchema):
    """
    Represents the `posts` table containing all post data.

    The main purpose of this class is to provide a namespace with all structural information of
    the posts table, as well as string constants for the column names. Always use these constants
    when referring to this table or its columns to make future schema changes easier.
    """

    TABLE_NAME: Final = "posts"
    """ Name of the table. """

    COLUMN_POST_ID: Final = "id"
    """ Name of the post ID column. """

    COLUMN_ROUTE_ID: Final = "route_id"
    """ Name of the column referencing the route a post belongs to. """

    COLUMN_USERNAME: Final = "user_name"
    """ Name of the user name column. """

    COLUMN_TIMESTAMP: Final = "post_date"
    """ Name of the timestamp column. """

    COLUMN_COMMENT: Final = "comment"
    """ Name of the comment column. """

    COLUMN_RATING: Final = "rating"
    """ Name of the rating column. """

    @override
    def table_name(self) -> EntityName:
        return self.TABLE_NAME

    @override
    def column_specification(self) -> list[ColumnDefinition]:
        return [
            ColumnDefinition(
                self.COLUMN_POST_ID, ColumnType.INTEGER, nullable=False, autoincrement=True
            ),
            ColumnDefinition(
                self.COLUMN_ROUTE_ID,
                ColumnType.INTEGER,
                nullable=False,
                reference=Reference(
                    RoutesTable.TABLE_NAME, RoutesTable.COLUMN_ROUTE_ID, delete_action="CASCADE"
                ),
            ),
            ColumnDefinition(self.COLUMN_USERNAME, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUMN_TIMESTAMP, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUMN_COMMENT, ColumnType.STRING, nullable=False),
            ColumnDefinition(self.COLUMN_RATING, ColumnType.INTEGER, nullable=False),
        ]

    @override
    def indices(self) -> list[IndexDefinition]:
        return []

    @override
    def primary_key(self) -> list[EntityName]:
        return [self.COLUMN_POST_ID]

    @override
    def unique_constraints(self) -> list[list[EntityName]]:
        return []
