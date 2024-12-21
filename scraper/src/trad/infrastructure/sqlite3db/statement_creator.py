"""
Definition of the SqlStatementCreator class.
"""

from logging import getLogger
from typing import assert_never

from trad.adapters.boundaries.database.common import EntityName
from trad.adapters.boundaries.database.query import InsertQuery, SelectQuery
from trad.adapters.boundaries.database.structure import (
    ColumnDefinition,
    ColumnType,
    CreateIndexQuery,
    CreateTableQuery,
)

_logger = getLogger(__name__)


class SqlStatementCreator:
    """
    Creates SQL statements from Query objects. All statement creation methods return a tuple of the
    SQL statement string and a collection of the corresponding query parameters.
    """

    def create_table_creation_statement(
        self, query: CreateTableQuery
    ) -> tuple[str, tuple[object, ...]]:
        """
        Creates a CREATE TABLE (DDL) statement from the given table description. Returns the SQL
        statement and an empty parameter tuple.
        """
        column_clause = ", ".join(
            self._get_column_ddl_string(col, query.primary_key) for col in query.column_definition
        )
        fk_clause = self._get_foreign_keys_dll_string(query.column_definition)

        # Generate the table DDL statement
        sql_statement = f"CREATE TABLE IF NOT EXISTS {query.table_name} ({column_clause}"
        if len(query.primary_key) > 1:
            sql_statement += f", PRIMARY KEY({', '.join(query.primary_key)})"
        for unique_columns in query.unique_constraints or []:
            sql_statement += f", UNIQUE({', '.join(unique_columns)})"
        if fk_clause:
            sql_statement += f", {fk_clause}"
        sql_statement += ")"

        _logger.debug(sql_statement)
        return sql_statement, ()

    def _get_column_ddl_string(
        self,
        column: ColumnDefinition,
        table_primary_keys: list[EntityName],
    ) -> str:
        """Returns the DDL for a single [column]."""
        type_string = self._getcolumn_type_string(column.type)
        nullable_string = "NULL" if column.nullable else "NOT NULL"
        column_ddl = f"{column.name} {type_string} {nullable_string}"
        if column.name in table_primary_keys and len(table_primary_keys) == 1:
            column_ddl += " PRIMARY KEY"
            if column.autoincrement:
                column_ddl += " AUTOINCREMENT"
        return column_ddl

    def _get_foreign_keys_dll_string(self, column_definition: list[ColumnDefinition]) -> str:
        """
        Returns the SQL clause for creating all FOREIGN KEY constraints defined by
        [column_definition]. Empty string if there are nor foreign keys.
        """
        fk_clauses: list[str] = [
            (
                f"FOREIGN KEY({column.name}) REFERENCES {column.reference.table_name}"
                f"({column.reference.column_name}) ON DELETE {column.reference.delete_action}"
            )
            for column in column_definition
            if column.reference is not None
        ]
        return ", ".join(fk_clauses)

    def _getcolumn_type_string(self, column_type: ColumnType) -> str:
        """Returns the SQL type name of the given [column_type]."""
        match column_type:
            case ColumnType.BOOLEAN:
                return "BOOL"
            case ColumnType.INTEGER:
                return "INTEGER"
            case ColumnType.STRING:
                return "TEXT"
            case ColumnType.FLOAT:
                return "REAL"
        assert_never(column_type)

    def create_index_creation_statement(
        self, query: CreateIndexQuery
    ) -> tuple[str, tuple[object, ...]]:
        """
        Creates a CREATE INDEX (DDL) statement from the given [query]. Returns the SQL statement and
        an empty parameter tuple.
        """
        column_names = ", ".join(query.index_definition.column_names)

        # Generate the index DDL statement
        sql_statement = (
            f"CREATE INDEX {query.index_definition.name} ON {query.table_name} ({column_names})"
        )

        _logger.debug(sql_statement)
        return sql_statement, ()

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
