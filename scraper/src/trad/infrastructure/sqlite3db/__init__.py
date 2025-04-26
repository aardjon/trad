"""
Sqlite3 implementation of the relation database component.
"""

import sqlite3
from collections.abc import Callable
from logging import getLogger
from pathlib import Path
from typing import override

from trad.adapters.boundaries.database import (
    DataRow,
    DataRowContainer,
    InsertQuery,
    RawDDLStatement,
    RelationalDatabaseBoundary,
    SelectQuery,
)
from trad.crosscuttings.errors import InvalidStateError
from trad.infrastructure.sqlite3db.statement_creator import SqlStatementCreator

_logger = getLogger(__name__)


class Sqlite3Database(RelationalDatabaseBoundary):
    """
    SQLite3 based implementation of the relational database.

    This implementation encapsulates the `sqlite3` package and therefore all its details. When
    [connect()]ing to a SQLite database, the connection_string is simply the full path to the SQLite
    database file to open.
    """

    def __init__(
        self,
        sqlite3_connect: Callable[..., sqlite3.Connection] = sqlite3.connect,
    ) -> None:
        """
        Constructor for injecting an alternative sqlite3 implementation.

        For easier unit testing, a mocked sqlite3.connect function (returning an alternative
        sqlite3.Connection implementation) can be injected by providing it as [sqlite3_connect]. In
        normal/productive cases always use the default parameter value.
        """
        self._sqlite3_connect = sqlite3_connect
        """
        Function to use for connecting to a Sqlite3 database.

        Having this as a separate member allows to replace the real library with a different or
        mocked one, e.g. for unit testing. Never use `sqlite3.connect()` directly but only this
        member.
        """

        self._db_handle: sqlite3.Connection | None = None
        """ Handle to the currently opened database, or `None` if no database has been opened. """

        self._statement_creator = SqlStatementCreator()
        """ Delegate for creating SQL statements from Query instances. """

    @override
    def connect(self, destination_file: Path, *, overwrite: bool = False) -> None:
        if overwrite:
            destination_file.unlink(missing_ok=True)
        elif destination_file.exists():
            error = FileExistsError("Destination file already exists")
            error.filename = str(destination_file)
            raise error

        self._db_handle = self._sqlite3_connect(str(destination_file))
        self._db_handle.execute("PRAGMA foreign_keys=true;")

    @override
    def disconnect(self) -> None:
        if self._db_handle is not None:
            self._db_handle.close()
            self._db_handle = None

    def is_connected(self) -> bool:
        """
        Returns True if the repository is currently connected to a database, otherwise False.

        This is only used for testing and therefore (currently) not available on the public
        interface.
        """
        return self._db_handle is not None

    @override
    def execute_raw_ddl(self, ddl_statement: RawDDLStatement) -> None:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")
        self._db_handle.execute(ddl_statement)
        self._db_handle.commit()

    @override
    def execute_select(self, query: SelectQuery) -> DataRowContainer:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")

        result_set = self._db_handle.execute(
            *self._statement_creator.create_select_statement(query)
        )
        return [DataRow(dict(zip(query.column_names, row, strict=True))) for row in result_set]

    @override
    def execute_insert(self, query: InsertQuery) -> None:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")

        self._db_handle.execute(*self._statement_creator.create_insert_statement(query))
        self._db_handle.commit()

    @override
    def run_analyze(self) -> None:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")
        self._db_handle.execute("ANALYZE")

    @override
    def run_vacuum(self) -> None:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")
        self._db_handle.execute("VACUUM")
