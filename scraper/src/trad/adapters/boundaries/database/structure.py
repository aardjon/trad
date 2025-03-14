"""
Partial definition of the boundary between pipes (`adapters` ring) and a concrete DBMS
implementation (`infrastructure` ring). This module provides the interfaces needed for defining the
database structure (tables, columns...) itself.
"""

from typing import NewType

RawDDLStatement = NewType("RawDDLStatement", str)
"""
Raw SQL DDL statement string for creating a database entity.

This is usually a CREATE statement, e.g. to create tables or indices.
"""
