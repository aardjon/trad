"""
Unit tests for the trad.infrastructure.sqlite3db module.
"""

import contextlib
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection
from typing import Final
from unittest.mock import MagicMock, Mock

import pytest

from trad.application.boundaries.database import SqlStatement
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
        sqlite3_connect_mock.assert_called_once_with("test.sqlite", autocommit=True)
        assert db.is_connected()
        sqlite3_connection_mock.execute.assert_called_with("PRAGMA foreign_keys=true;")

    @pytest.mark.parametrize("is_connected", [True, False])
    def test_disconnect(
        self,
        *,
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
        ("query_statement", "query_parameters"),
        [
            (
                "Fake SQL statement without parameters",
                None,
            ),
            (
                "Fake SQL statement with ? parameters ?",
                [42, "11"],
            ),
        ],
    )
    def test_execute_write(
        self,
        query_statement: str,
        query_parameters: list[object] | None,
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        connected_sqlite3_database.database.execute_write(
            query=SqlStatement(query_statement), query_parameters=query_parameters
        )
        connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
            query_statement, tuple(query_parameters or ())
        )

    def test_execute_read(
        self,
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        result_data = [1, 2, 3]
        query_statement = SqlStatement("Fake SQL statement with ? parameters ?")
        query_parameters = [47, "11"]

        mocked_result_set = MagicMock(
            description=[("id", None, None, None, None, None, None, None)]
        )
        mocked_result_set.__iter__.return_value = [(v,) for v in result_data]
        connected_sqlite3_database.sqlite3_connection.execute.return_value = mocked_result_set

        result = connected_sqlite3_database.database.execute_read(
            query=query_statement, query_parameters=query_parameters
        )
        assert [row.get_object_value("id") for row in result] == result_data
        connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
            query_statement, tuple(query_parameters)
        )

    @pytest.mark.parametrize(
        ("transaction_fails", "expected_final_statement"),
        [
            (False, "COMMIT TRANSACTION"),  # Transaction succeeds (no exception)
            (True, "ROLLBACK TRANSACTION"),  # Transaction fails (raised an exception)
        ],
    )
    def test_transaction(
        self,
        *,
        transaction_fails: bool,
        expected_final_statement: str,
        connected_sqlite3_database: Sqlite3Mock,
    ) -> None:
        """
        Ensures that using the database as a context manager correctly startds and ends transations:
         - Entering the context BEGINs a transaction
         - Leaving the context normally does a COMMIT
         - Leaving the context with an exception does a ROLLBACK
        """

        class FakeDbOperationError(Exception):
            """
            Fake exception to simulate a failing database operation. Using a dedicated type here to
            surely distinguish it from any other (possibly unwanted) errors.
            """

        expected_db_calls: Final = 2  # Expected number of DB calls during this test

        # The failing transaction context raises a FakeDbOperationFailure. To be able to check for
        # the proper rollback later, we need to suppress this exception (but still propagate any
        # others!)
        with contextlib.suppress(FakeDbOperationError), connected_sqlite3_database.database:
            connected_sqlite3_database.sqlite3_connection.execute.assert_called_once_with(
                "BEGIN TRANSACTION"
            )
            if transaction_fails:
                raise FakeDbOperationError
        connected_sqlite3_database.sqlite3_connection.execute.assert_called_with(
            expected_final_statement
        )
        assert connected_sqlite3_database.sqlite3_connection.execute.call_count == expected_db_calls
