"""
Unit tests for the trad.infrastructure.sqlite3db.database module.
"""

from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection
from unittest.mock import MagicMock, Mock

import pytest

from trad.adapters.boundaries.database.query import (
    DataRow,
    InsertQuery,
    SelectQuery,
)
from trad.adapters.boundaries.database.structure import (
    ColumnDefinition,
    ColumnType,
    CreateIndexQuery,
    CreateTableQuery,
    IndexDefinition,
    Reference,
)
from trad.infrastructure.sqlite3db import Sqlite3Database


@dataclass
class Sqlite3Mock:
    """
    Return type of the fixtures creating database instances. It's only needed because some fixtures
    actually want to return more than one value.
    """

    database: Sqlite3Database
    """
    The created [Sqlite3Database] instance. This is a not a mock, but uses a mocked sqlite3
    connection under the hood.
    """
    sqlite3_connection: Mock
    """
    Mocked [sqlite3.Connection] which is used by [database]. This way, tests can run without having
    to create real database files.
    """


@pytest.fixture
def sqlite3_database() -> Sqlite3Mock:
    connection_mock = Mock(Connection)
    database = Sqlite3Database(sqlite3_connect=Mock(return_value=connection_mock))
    return Sqlite3Mock(database=database, sqlite3_connection=connection_mock)


@pytest.fixture
def connected_sqlite3_database(sqlite3_database: Sqlite3Mock) -> Sqlite3Mock:
    sqlite3_database.database.connect(Path("test.sqlite"))
    sqlite3_database.sqlite3_connection.reset_mock()
    sqlite3_database.sqlite3_connection.execute = MagicMock()
    sqlite3_database.sqlite3_connection.cursor = Mock(
        return_value=sqlite3_database.sqlite3_connection
    )
    return sqlite3_database


def create_select_query(
    table_name: str,
    column_names: list[str],
    where_condition: str,
    where_parameters: list[object],
) -> SelectQuery:
    query = SelectQuery(table_name, column_names)
    if where_condition:
        query.set_where_condition(where_condition, where_parameters)
    return query


class TestSqlite3Database:
    """Unit tests for the Sqlite3Database class."""

    def test_connect(self) -> None:
        """
        Unit test for the connect() method.

        Ensures that the database is created, opened and initialized properly (i.e. foreign keys are
        enabled).
        """
        sqlite3_connection_mock = Mock(Connection)
        sqlite3_connect_mock = Mock(return_value=sqlite3_connection_mock)
        db = Sqlite3Database(sqlite3_connect=sqlite3_connect_mock)

        assert not db.is_connected()
        db.connect(Path("test.sqlite"))
        sqlite3_connect_mock.assert_called_once_with("test.sqlite")
        assert db.is_connected()
        sqlite3_connection_mock.execute.assert_called_once_with("PRAGMA foreign_keys=true;")

    @pytest.mark.parametrize("is_connected", [True, False])
    def test_disconnect(
        self,
        is_connected: bool,
        sqlite3_database: Sqlite3Mock,
    ) -> None:
        """
        Unit test for the disconnect() method.

        Ensures that:
         - the database is really closed again
         - calling disconnect() on a closed database doesn't do any harm

        :param is_connected: Defines whether the database shall be connected (True) before calling
            disconnect() or not (False).
        """
        db = sqlite3_database.database

        assert not db.is_connected()
        if is_connected:
            db.connect(Path("test.sqlite"))
        db.disconnect()

        assert sqlite3_database.sqlite3_connection.close.call_count == (1 if is_connected else 0)
        assert not db.is_connected()

    @pytest.mark.parametrize(
        ("column_definition", "primary_key", "unique_constraints", "expected_sql"),
        [
            (  # Most simple possible table
                [ColumnDefinition(name="id", type=ColumnType.INTEGER)],
                ["id"],
                None,
                "CREATE TABLE IF NOT EXISTS simple_table (id INTEGER NULL PRIMARY KEY)",
            ),
            (  # Supporting "NOT NULL"
                [ColumnDefinition(name="id", type=ColumnType.INTEGER, nullable=False)],
                ["id"],
                None,
                "CREATE TABLE IF NOT EXISTS simple_table (id INTEGER NOT NULL PRIMARY KEY)",
            ),
            (  # Supporting combined primary keys
                [
                    ColumnDefinition(name="id1", type=ColumnType.INTEGER),
                    ColumnDefinition(name="id2", type=ColumnType.INTEGER),
                ],
                ["id1", "id2"],
                None,
                "CREATE TABLE IF NOT EXISTS simple_table (id1 INTEGER NULL, id2 INTEGER NULL, PRIMARY KEY(id1, id2))",
            ),
            (  # Create a foreign key
                [
                    ColumnDefinition(name="local_id", type=ColumnType.INTEGER),
                    ColumnDefinition(
                        name="remote_id",
                        type=ColumnType.INTEGER,
                        reference=Reference("simple_table", "local_id"),
                    ),
                ],
                ["local_id"],
                None,
                "CREATE TABLE IF NOT EXISTS simple_table ("
                "local_id INTEGER NULL PRIMARY KEY, remote_id INTEGER NULL, "
                "FOREIGN KEY(remote_id) REFERENCES simple_table(local_id) ON DELETE NO ACTION)",
            ),
        ],
    )
    def test_create_table(
        self,
        column_definition: list[ColumnDefinition],
        primary_key: list[str],
        unique_constraints: list[list[str]] | None,
        expected_sql: str,
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        connected_sqlite3_database.database.execute_create_table(
            CreateTableQuery(
                table_name="simple_table",
                column_definition=column_definition,
                primary_key=primary_key,
                unique_constraints=unique_constraints,
            )
        )

        connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
            expected_sql, ()
        )

    @pytest.mark.parametrize(
        ("index_query", "expected_sql"),
        [
            (
                CreateIndexQuery(
                    table_name="example",
                    index_definition=IndexDefinition(
                        name="idx_nam_rat", column_names=["name", "rating"]
                    ),
                ),
                "CREATE INDEX idx_nam_rat ON example (name, rating)",
            ),
        ],
    )
    def test_create_index(
        self,
        index_query: CreateIndexQuery,
        expected_sql: str,
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        connected_sqlite3_database.database.execute_create_index(index_query)

        connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
            expected_sql, ()
        )

    def test_execute_insert(
        self,
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        connected_sqlite3_database.database.execute_insert(
            InsertQuery(
                table_name="example",
                data_row=DataRow(raw_data={"name": "bla", "count": 42}),
            )
        )

        connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
            "INSERT OR IGNORE INTO example (name, count) VALUES (?, ?)",
            ("bla", 42),
        )

    @pytest.mark.parametrize(
        ("query", "expected_statement", "expected_parameters"),
        [
            (
                create_select_query(
                    table_name="example",
                    column_names=["*"],
                    where_condition="",
                    where_parameters=[],
                ),
                "SELECT * FROM example",
                (),
            ),
            (
                create_select_query(
                    table_name="example",
                    column_names=["id"],
                    where_condition="name = ?",
                    where_parameters=["Test"],
                ),
                "SELECT id FROM example WHERE name = ?",
                ("Test",),
            ),
            (
                create_select_query(
                    table_name="example",
                    column_names=["name"],
                    where_condition="rating = ? AND cat = ?",
                    where_parameters=[42, "good"],
                ),
                "SELECT name FROM example WHERE rating = ? AND cat = ?",
                (42, "good"),
            ),
            (
                create_select_query(
                    table_name="main",
                    column_names=["name"],
                    where_condition="cat_id = ?",
                    where_parameters=[
                        create_select_query(
                            table_name="sub",
                            column_names=["id"],
                            where_condition="category = ?",
                            where_parameters=["test"],
                        )
                    ],
                ),
                "SELECT name FROM main WHERE cat_id = (SELECT id FROM sub WHERE category = ?)",
                ("test",),
            ),
        ],
    )
    def test_execute_select(
        self,
        query: SelectQuery,
        expected_statement: str,
        expected_parameters: tuple[object, ...],
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        connected_sqlite3_database.database.execute_select(query)

        connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
            expected_statement,
            expected_parameters,
        )
