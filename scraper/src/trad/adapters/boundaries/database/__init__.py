"""
Definition of the boundary between pipes (`adapters` ring) and a concrete DBMS implementation
(`infrastructure` ring).
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path

from trad.adapters.boundaries.database.query import DataRowContainer, InsertQuery, SelectQuery
from trad.adapters.boundaries.database.structure import RawDDLStatement


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
