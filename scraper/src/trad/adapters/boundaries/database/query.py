"""
Partial definition of the boundary between pipes (`adapters` ring) and a concrete DBMS
implementation (`infrastructure` ring). This module provides the data structures needed for querying
and manipulating data.
"""

from collections.abc import Collection

from trad.adapters.boundaries.database.common import EntityName, Query


class DataRow:
    """
    A single row within a database table, either for inserting or as part of a result result.

    An instance of this class doesn't necessarily contain all columns that are physically available
    in the table, they may be limited by the corresponding query. The available cell values are
    accessed based on their column name.
    """

    def __init__(self, raw_data: dict[EntityName, object]):
        """
        Initializes a new row from the given raw data.

        [raw_data] is a dict assigning single values to column names.
        """
        self._raw_data = raw_data
        """ Raw column data. """

    def get_column_names(self) -> Collection[EntityName]:
        """Returns a list of all column names that are available in this row object."""
        return self._raw_data.keys()

    def get_int_value(self, column_name: EntityName) -> int | None:
        """
        Returns the value of the requested integer column [column_name].

        If the requested column doesn't exist in this row or is of a different type, an
        [ArgumentError] is thrown (because this is usually a programming error).
        """
        return self.__get_value(column_name)

    def get_string_value(self, column_name: EntityName) -> str | None:
        """
        Returns the value of the requested string column [column_name].

        If the requested column doesn't exist in this row or is of a different type, an
        [ArgumentError] is thrown (because this is usually a programming error).
        """
        return self.__get_value(column_name)

    def get_object_value(self, column_name: EntityName) -> object:
        """
        Returns the value of the requested column [column_name].

        If the requested column doesn't exist in this row, a [KeyError] is thrown (this is usually a
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


class InsertQuery(Query):
    """
    Query for inserting a new data row into a table.
    """

    def __init__(self, table_name: EntityName, data_row: DataRow):
        """
        Create a new query for inserting the given [data_row] into [table_name].
        """
        super().__init__(table_name)
        self.data_row = data_row
        """
        Data to be inserted. The dict keys are column names that must of course be available on that
        table. Also, the table must represent a valid table row.
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
        """Parameter values referenced by [where_condition]."""
        return self._where_parameters

    def set_where_condition(self, where_condition: str, where_parameters: list[object]) -> None:
        """
        Defines a condition to filter for, setting the `where_condition` and `where_parameters`
        properties to the provided values.

        [where_condition] is a regular SQL WHERE clause without the WHERE keyword. All non-static
        parameter values should be provided in the [where_parameters] list and only referenced by
        '?' within [where_condition] to avoid SQL injection errors. Of course, the number of given
        parameters must match the number of references, otherwise the query will fail upon
        execution.
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
    adjusting adding the missing entity first. In general, the end user cannot do much about it when
    it happens unexpectedly at runtime.
    """
