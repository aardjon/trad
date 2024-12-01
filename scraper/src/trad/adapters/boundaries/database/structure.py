"""
Partial definition of the boundary between pipes (`adapters` ring) and a concrete DBMS
implementation (`infrastructure` ring). This module provides the interfaces needed for defining the
database structure (tables, columns...) itself.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Final, Literal

from trad.adapters.boundaries.database.common import EntityName, Query


class ColumnType(Enum):
    """Data type for the values stored in a table columns."""

    BOOLEAN = auto()
    """ Boolean type. """
    INTEGER = auto()
    """ Integer type. """
    FLOAT = auto()
    """ Floating-point type. """
    STRING = auto()
    """ Variable-length string type. """


@dataclass
class Reference:
    """Definition of the destination of a foreign key."""

    table_name: EntityName
    """ The name of the referenced ("parent") table. """
    column_name: EntityName
    """ The name of the referenced ("parent") column (must be one of [table_name]s columns). """
    delete_action: Literal["CASCADE", "REJECT", "SET NULL", "SET DEFAULT", "NO ACTION"] | None = (
        field(default="NO ACTION", kw_only=True)
    )
    """ The desired behaviour in case the remote values is deleted. """


@dataclass
class ColumnDefinition:
    """Definition of a single table column."""

    name: EntityName
    """ The column name. """
    type: ColumnType
    """ Column content data type. """
    nullable: bool = field(default=True, kw_only=True)
    """ Does the column accept NULL values (True) or not (False)? """
    autoincrement: bool = field(default=False, kw_only=True)
    """
    Enable the SQL "autoincrement" feature for this column. Only supported for primary key ID
    columns.
    """
    reference: Reference | None = field(default=None, kw_only=True)
    """
    If set, this column references values from another column (possibly in a different table) by
    means of a foreign key relationship.
    """


@dataclass
class IndexDefinition:
    """Definition of a single index on a certain table."""

    name: EntityName
    """ The name of the index. """
    column_names: list[EntityName]
    """ Names of the columns the index is built on (in that order). """


@dataclass
class CreateTableQuery(Query):
    """
    Query for creating a new data table in a database.
    """

    column_definition: list[ColumnDefinition]
    """ Specification of all columns of the new table. """
    primary_key: list[EntityName]
    """
    List of column names that form the table's primary key (in that order). The column names must of
    course be defined in the [column_definition].
    """
    unique_constraints: list[list[EntityName]] | None = None
    """
    Definition of unique constraints for the new table: Each list item is a list of column names
    whose values must (in this combination) be unique within this table. The column names must of
    course be defined in the [column_definition].
    """

    def __post_init__(self) -> None:
        """
        Post-initialization checks for the data fields.
        """
        column_names: Final = [c.name for c in self.column_definition]
        if any(pk not in column_names for pk in self.primary_key):
            raise ValueError("Some primary key refers to an undefined column.")
        for uc in self.unique_constraints or []:
            if any(c not in column_names for c in uc):
                raise ValueError("Some unique constraint refers to an undefined column.")


@dataclass
class CreateIndexQuery(Query):
    """
    Query for creating a new index within a database.
    """

    table_name: EntityName
    """ Name of the table to base the index on. """
    index_definition: IndexDefinition
    """ Specification of the new table index. """
