"""
Abstract interface for describing the database schema (e.g. table structure and column names).
"""

from abc import ABCMeta, abstractmethod

from trad.adapters.boundaries.database import EntityName, RawDDLStatement


class TableSchema(metaclass=ABCMeta):
    """
    Base class and interface for the definition of a single database table.
    Each derived class specifies all features of a physical table.
    """

    @abstractmethod
    def table_name(self) -> EntityName:
        """Name of the table."""

    @abstractmethod
    def table_ddl(self) -> RawDDLStatement:
        """
        Returns the raw SQL (DDL) statement for newly creating this table.
        """

    @abstractmethod
    def index_ddl(self) -> list[RawDDLStatement]:
        """
        Returns a list of raw SQL (DDL) statements for newly creating all indices of this table.
        """
