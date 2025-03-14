"""
Definition of the SqlStatementCreator class.
"""

from logging import getLogger

from trad.adapters.boundaries.database.query import InsertQuery, SelectQuery

_logger = getLogger(__name__)


class SqlStatementCreator:
    """
    Creates SQL statements from Query objects. All statement creation methods return a tuple of the
    SQL statement string and a collection of the corresponding query parameters.
    """

    def create_insert_statement(self, query: InsertQuery) -> tuple[str, tuple[object, ...]]:
        """
        Creates a INSERT INTO statement as described by [query]. Returns the SQL statement and a
        tuple of the corresponding query parameters.
        """
        column_name_list = query.data_row.get_column_names()
        column_names = ", ".join(column_name_list)
        values = ", ".join(["?"] * len(column_name_list))
        sql_statement = (
            f"INSERT OR IGNORE INTO {query.table_name} ({column_names}) VALUES ({values})"
        )

        complete_sql_statement, complete_parameters = self._create_subquery_statements(
            sql_statement=sql_statement,
            query_parameters=[query.data_row.get_object_value(c) for c in column_name_list],
        )

        _logger.debug(complete_sql_statement)
        _logger.debug(complete_parameters)
        return complete_sql_statement, complete_parameters

    def create_select_statement(self, query: SelectQuery) -> tuple[str, tuple[object, ...]]:
        """
        Creates a SELECT statement as described by [query]. Returns the SQL statement and a tuple of
        the corresponding query parameters.
        """
        query_parameters = query.where_parameters
        sql_statement = "SELECT "
        sql_statement += ", ".join(query.column_names)
        sql_statement += f" FROM {query.table_name}"
        if query.where_condition:
            sql_statement += f" WHERE {query.where_condition}"
        if query.order_by_columns:
            sql_statement += " ORDER BY" + ", ".join(query.order_by_columns)
        if query.limit is not None:
            sql_statement += " LIMIT ?"
            query_parameters.append(query.limit)

        complete_sql_statement, complete_parameters = self._create_subquery_statements(
            sql_statement=sql_statement,
            query_parameters=query_parameters,
        )

        _logger.debug(complete_sql_statement)
        _logger.debug(complete_parameters)
        return complete_sql_statement, complete_parameters

    def _create_subquery_statements(
        self,
        sql_statement: str,
        query_parameters: list[object],
    ) -> tuple[str, tuple[object, ...]]:
        """
        Replaces all query parameters ('?') in the given [sql_statement] with a subquery statement
        if the corresponding object within [query_parameters] is a [SelectQuery]. Returns a new SQL
        statement and parameter list. [query_parameters] itself is not modified.
        """
        if not query_parameters:
            return sql_statement, tuple(query_parameters)

        where_parts = sql_statement.split("?")
        new_sql_statement = ""
        new_parameters: tuple[object, ...] = ()
        for partial_sql, parameter in zip(where_parts[:-1], query_parameters, strict=True):
            new_sql_statement += partial_sql
            if isinstance(parameter, SelectQuery):
                subquery_clause, subquery_params = self.create_select_statement(parameter)
                new_sql_statement += f"({subquery_clause})"
                new_parameters += subquery_params
            else:
                new_sql_statement += "?"
                new_parameters += (parameter,)
        new_sql_statement += where_parts[-1]
        return new_sql_statement, new_parameters
