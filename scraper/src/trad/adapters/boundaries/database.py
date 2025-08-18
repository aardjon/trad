"""
Definition of the boundary between pipes (`adapters` ring) and a concrete DBMS access library
(`infrastructure` ring). The purpose of this inteface is not to hide the database itself but the
library for accessing it. This allows for mocking the real database in unit tests, and also makes
future changes/adaption to the lib interface easier.
"""

from __future__ import annotations

from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Literal, NewType

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

EntityName = str
"""
Name of a single entity within a relational database. These entities can be tables, columns or
indices, for example.
"""

SqlStatement = NewType("SqlStatement", str)
"""
SQL statement string that can be executed on a database.
"""


class DataRow:
    """
    A single row within a database table, either for inserting or as part of a result set.

    An instance of this class doesn't necesarily contain all columns that are physically available
    in the table, they may be limited by the corresponding query. The available cell values are
    accessed based on their column name.
    """

    def __init__(self, raw_data: Mapping[EntityName, object]):
        """
        Initializes a new row from the given raw data.

        [raw_data] is a dict assigning single values to column names.
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


class RelationalDatabaseBoundary(
    AbstractContextManager["RelationalDatabaseBoundary", Literal[False]]
):
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

    All database operations are blocking, thread-safe and atomic. However, the databse can be used
    as a contect manager to embrace several operations into a single transaction and make them
    blocking and atomic as a whole.
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
    def execute_write(
        self,
        query: SqlStatement,
        query_parameters: Collection[object] | None = None,
    ) -> None:
        """
        Executes the given [query] to manipulate (e.g. add or update) data in the database.

        All non-static parameter values for the query (e.g. within a WHERE clause) should be
        provided in the [query_parameters] list and only referenced by '?' within [query] to avoid
        SQL injection errors. Of course, the number of given parameters must match the number of
        references.

        If the provided statement string is in any way invalid or the query cannot succeed for some
        reason, an exception is raised.
        """

    @abstractmethod
    def execute_read(
        self,
        query: SqlStatement,
        query_parameters: Collection[object] | None = None,
    ) -> DataRowContainer:
        """
        Executes the given [query] to read and return data from the database.

        All non-static parameter values for the query (e.g. within a WHERE clause) should be
        provided in the [query_parameters] list and only referenced by '?' within [query] to avoid
        SQL injection errors. Of course, the number of given parameters must match the number of
        references.

        If the provided statement string is in any way invalid or the query cannot succeed for some
        reason, an exception is raised. If the query doesn't return any results, the returned result
        row list is empty.
        """
