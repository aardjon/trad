"""
Sqlite3 implementation of the relation database component.
"""

import sqlite3
from collections.abc import Callable, Collection
from logging import getLogger
from pathlib import Path
from types import TracebackType
from typing import Literal, Self, override

from trad.adapters.boundaries.database import (
    DataRow,
    DataRowContainer,
    RelationalDatabaseBoundary,
    SqlStatement,
)
from trad.kernel.errors import InvalidStateError

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
        super().__init__()
        self._sqlite3_connect = sqlite3_connect
        """
        Function to use for connecting to a Sqlite3 database.

        Having this as a separate member allows to replace the real library with a different or
        mocked one, e.g. for unit testing. Never use `sqlite3.connect()` directly but only this
        member.
        """

        self._db_handle: sqlite3.Connection | None = None
        """ Handle to the currently opened database, or `None` if no database has been opened. """

    @override
    def __enter__(self) -> Self:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")
        self._db_handle.execute("BEGIN TRANSACTION")
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")

        if exc_type is None:
            self._db_handle.execute("COMMIT TRANSACTION")
        else:
            self._db_handle.execute("ROLLBACK TRANSACTION")
        return False

    @override
    def connect(self, destination_file: Path, *, overwrite: bool = False) -> None:
        if overwrite:
            destination_file.unlink(missing_ok=True)
        elif destination_file.exists():
            error = FileExistsError("Destination file already exists")
            error.filename = str(destination_file)
            raise error

        self._db_handle = self._sqlite3_connect(str(destination_file), autocommit=True)
        # Disable safe DB writes/commits for a *much* higher write performance. With these settings
        # we will likely end up with a corrupt database file in case of a crash or power outage, but
        # this is not a problem because the next run creates a new database anyway.
        self._db_handle.execute("PRAGMA synchronous=off")
        self._db_handle.execute("PRAGMA journal_mode=memory")
        # Enable foreign key checks to ensure the relational integrity of the new database
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
    def execute_write(
        self,
        query: SqlStatement,
        query_parameters: Collection[object] | None = None,
    ) -> None:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")
        self._db_handle.execute(query, tuple(query_parameters) if query_parameters else ())

    @override
    def execute_read(
        self,
        query: SqlStatement,
        query_parameters: Collection[object] | None = None,
    ) -> DataRowContainer:
        if self._db_handle is None:
            raise InvalidStateError("Please connect() to a database before querying it.")

        result_set = self._db_handle.execute(
            query, tuple(query_parameters) if query_parameters else ()
        )
        column_names = [col[0] for col in result_set.description]
        return [DataRow(dict(zip(column_names, row, strict=True))) for row in result_set]
