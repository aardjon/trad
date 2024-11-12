"""
Concrete pipe implementation writing a route database with schema version 1.
"""

from logging import getLogger
from pathlib import Path
from typing import override

from trad.adapters.filters.boundaries import RouteDbCreatingPipe

_logger = getLogger(__name__)


class DbSchemaV1Pipe(RouteDbCreatingPipe):
    """
    Pipe implementation for creating a route database file (schema version 1) that can be used with
    the trad mobile app.

    This class encapsulates all knowledge about the structure of the route database in this
    particular schema version.
    """

    @override
    def initialize_pipe(self, destination_path: Path) -> None:
        # Create/Open DB file
        # Create part of the schema (all tables and constraints, but no indices!)
        _logger.debug("Initializing routedb pipe for writing into %s", destination_path)
