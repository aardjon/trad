"""
Partial definition of the boundary between pipes (`adapters` ring) and a concrete DBMS
implementation (`infrastructure` ring). This module provides data types that are used by both the
`structure`and and `query` sub modules.
"""

from dataclasses import dataclass

EntityName = str
"""
Name of a single entity within a relational database. These entities can be tables, columns or
indices, for example.
"""


@dataclass
class Query:
    """
    Common base class for all queries that can be executed on a database.

    Query classes are merely for transporting and representing queries, they don't do much
    validation. They can be executed by handing it to one of [RelationalDatabaseBoundary]s execution
    methods, which will cause an error if the query is in any way invalid.
    """

    table_name: EntityName
    """ Table name to query. """
