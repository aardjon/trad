"""
Definition of the boundary between pipes (`adapters` ring) and a concrete DBMS implementation
(`infrastructure` ring).
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

EntityName = str
"""
Name of a single entity within a relational database. These entities can be tables, columns or
indices, for example.
"""


class DataRow:
    """
    A single row within a database table, either for inserting or as part of a result set.

    For inserting data, the "value" of a field can also be a [SelectQuery] instance, which is then
    executed as a subquery to the actual value. This case can never happen in a query result set, of
    course.

    An instance of this class doesn't necessarily contain all columns that are physically available
    in the table, they may be limited by the corresponding query. The available cell values are
    accessed based on their column name.
    """

    def __init__(self, raw_data: Mapping[EntityName, str | int | SelectQuery | None]):
        """
        Initializes a new row from the given raw data.

        [raw_data] is a dict assigning single values to column names. Instead of a value, a
        [SelectQuery] instance can be provided to retrieve a value from the database as necessary.
        """
        self._raw_data: Mapping[EntityName, object] = raw_data
        """ Raw column data. """

    def get_column_names(self) -> Collection[EntityName]:
        """Returns a list of all column names that are available in this row object."""
        return self._raw_data.keys()

    def get_int_value(self, column_name: EntityName) -> int | None:
        """
        Returns the value of the requested integer column [column_name].

        Exceptions (usually programming errors):
         - KeyError: The requested column doesn't exist in this row
         - TypeError: The requested column is of a different type
        """
        value = self.__get_value(column_name)
        if not isinstance(value, int | None):
            raise TypeError("Value of column {column_name} is of unexpected type {type(value)}.")
        return value

    def get_string_value(self, column_name: EntityName) -> str | None:
        """
        Returns the value of the requested string column [column_name].

        Exceptions (usually programming errors):
         - KeyError: The requested column doesn't exist in this row
         - TypeError: The requested column is of a different type
        """
        value = self.__get_value(column_name)
        if not isinstance(value, str | None):
            raise TypeError("Value of column {column_name} is of unexpected type {type(value)}.")
        return value

    def get_object_value(self, column_name: EntityName) -> object:
        """
        Returns the value of the requested column [column_name].

        If the requested column doesn't exist in this row, a [KeyError] is raised (this is usually a
        programming error).
        """
        return self.__get_value(column_name)

    def __get_value(self, column_name: EntityName) -> object:
        """
        Returns the value of the given [column_name] if the column exists in the result set.

        The value may still be None (for NULLABLE columns). If the row doesn't contain the requested
        column at all, a [KeyError] is raised.
        """
        try:
            return self._raw_data[column_name]
        except KeyError as e:
            raise KeyError(
                f"Column {column_name} doesn't exist in this row, did you forget to select it?."
            ) from e


DataRowContainer = list[DataRow]
""" The result set returned by a table query. """


@dataclass
class Query:
    """
    Common base class for all queries that can be executed on a database.

    Query classes are merely for transporting and representing queries, they don't do much
    validation. They can be executed by handing it to one of [RelationalDatabaseBoundary]s execution
    methods, which will cause an error if the query is in any way invalid.
    """

    table_name: EntityName
    """ Table name to query. """


RawDDLStatement = NewType("RawDDLStatement", str)
"""
Raw SQL DDL statement string for creating a database entity.

This is usually a CREATE statement, e.g. to create tables or indices.
"""


class InsertQuery(Query):
    """
    Query for inserting a new data row into a table. If a [SelectQuery] is provided as a field value
    within the data row it is executed as a subquery to retrieve the actual value for that field.
    """

    def __init__(self, table_name: EntityName, data_row: DataRow):
        """
        Create a new query for inserting the given [data_row] into [table_name].
        """
        super().__init__(table_name)

        self.data_row = data_row
        """
        Data to be inserted. The dict keys are column names that must of course be available on that
        table. Also, the table must represent a valid table row. Values may either be concrete
        values or [SelectQuery] objects to run for retrieving a value.
        """


class FilteringQuery(Query):
    """
    Base class for queries that can limit or filter table content, as done e.g. for selecting or
    updating.
    """

    def __init__(self, table_name: EntityName):
        """
        Create a query for a single database table with the name [table_name].
        """
        super().__init__(table_name)

        self._where_condition: str | None = None
        """ The SQL WHERE condition. """

        self._where_parameters: list[object] = []
        """ Parameter values referenced by [_where_condition]. """

        self.limit: int | None = None
        """ Number of rows the result set shall be limited to, or None to return all results. """

    @property
    def where_condition(self) -> str | None:
        """The SQL WHERE condition to filter by (without the WHERE keyword)."""
        return self._where_condition

    @property
    def where_parameters(self) -> list[object]:
        """
        Parameter values referenced by [where_condition]. May contain [SelectQuery] instances
        instead of actual values, to use the query result.
        """
        return self._where_parameters

    def set_where_condition(self, where_condition: str, where_parameters: list[object]) -> None:
        """
        Defines a condition to filter for, setting the `where_condition` and `where_parameters`
        properties to the provided values.

        [where_condition] is a regular SQL WHERE clause without the WHERE keyword. All non-static
        parameter values should be provided in the [where_parameters] list and only referenced by
        '?' within [where_condition] to avoid SQL injection errors. The [where_parameters] list may
        also contain [SelectQuery] instances to retrieve the actual values from the database. Of
        course, the number of given parameters must match the number of references, otherwise the
        query will fail upon execution.
        """
        self._where_condition = where_condition
        self._where_parameters = where_parameters


class SelectQuery(FilteringQuery):
    """
    Query for retrieving data from the database.

    [SelectQuery] instances can be provided in places like [FilteringQuery.set_where_condition()] or
    [InsertQuery.data_row]. The corresponding placeholder is then replaced with a subquery statement
    representing this query instance. The query must return an appropriate result set for this to
    work, though.
    """

    def __init__(self, table_name: EntityName, column_names: list[EntityName]):
        """
        Create a query that retrieves [column_names] from the table with the name [table_name].
        """
        super().__init__(table_name)

        self.column_names = column_names
        """ The names of the columns to retrieve. """

        self.order_by_columns: list[EntityName] = []
        """ Specifies the names of the columns the result rows are ordered by. """


class EntityNotFoundError(Exception):
    """
    Raised when an entity the operation depends on is missing in the database (e.g. trying to add a
    route to a non-existing summit). In many cases these are programming errors that can be fixed by
    adding the missing entity first. In general, the end user cannot do much about it when it
    happens unexpectedly at runtime.
    """


class RelationalDatabaseBoundary(metaclass=ABCMeta):
    """
    Boundary interface to a relational database.

    A relational database is a repository organizing data in *entities* (tables and columns) and
    relations between them. This interface provides generic access to a relational (e.g. SQL)
    database. Each implementation encapsulates details like the used database engine or the used
    driver library. However, the repository interface is schema-agnostic, which means that all
    information about the actual structure (including information like table or column names) belong
    to the `adapters` ring.

    The database can be either `connected` or `disconnected`. Most of its methods only work after
    [connect()]ing to a database.

    All database operations are blocking, thread-safe and atomic.
    """

    @abstractmethod
    def connect(self, destination_file: Path, *, overwrite: bool = False) -> None:
        """
        Connects to the database specified by the [destination_file]. [overwrite] controls what to
        do in case the file already exists: True, replaces the existing file, False raises an Error.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """
        Closes the current database connection, if any.

        If no database is connected, this method does nothing.
        """

    @abstractmethod
    def execute_raw_ddl(self, ddl_statement: RawDDLStatement) -> None:
        """
        Executes the given [ddl_statement] for creating a new database entity.
        """

    @abstractmethod
    def execute_insert(self, query: InsertQuery) -> None:
        """
        Executes the given [query] to insert data into a table.
        """

    @abstractmethod
    def execute_select(self, query: SelectQuery) -> DataRowContainer:
        """
        Executes the given [query] and returns the result set.

        If the provided query is in any way invalid, an exception is raised. If the query doesn't
        return any results, the returned result row list is empty.
        """

    @abstractmethod
    def run_analyze(self) -> None:
        """
        Executes the ANALYZE command to gather statistics for improving future query plans.
        """

    @abstractmethod
    def run_vacuum(self) -> None:
        """
        Executes the VACUUM command to rebuild the database into a minimal amount of disk space.
        """
