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


class SummitsTable(TableSchema):
    """
    Represents the `summits` table containing all summit data.

    The main purpose of this class is to provide a namespace with all structural information of
    the summits table, as well as string constants for the column names. Always use these constants
    when referring to this table or its columns to make future schema changes easier.
    """

    TABLE_NAME = "peaks"
    """ Name of the table. """

    COLUMN_ID: Final = "id"
    """ Name of the ID column. """

    COLUMN_NAME: Final = "peak_name"
    """ Name of the summit name column. """

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
        ]

    @override
    def indices(self) -> list[IndexDefinition]:
        return [IndexDefinition(name="IdxPeakName", column_names=[self.COLUMN_NAME])]

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

    COLUMN_SUMMIT_ID: Final = "peak_id"
    """ Name of the column referencing the summit a route belongs to. """

    COLUMN_NAME: Final = "route_name"
    """ Name of the route name column. """

    COLUMN_GRADE: Final = "route_grade"
    """ Name of the route grade column. """

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
