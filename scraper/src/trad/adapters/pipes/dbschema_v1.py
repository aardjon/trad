"""
Concrete pipe implementation writing a route database with schema version 1.
"""

from logging import getLogger
from pathlib import Path
from typing import override

from trad.core.boundaries.pipes import Pipe

_logger = getLogger(__name__)


class DbSchemaV1Pipe(Pipe):
    """
    Pipe implementation for creating a route database file (schema version 1) that can be used with
    the trad mobile app.

    This class encapsulates all knowledge about the structure of the route database in this
    particular schema version.
    """

    def __init__(self, output_directory: Path):
        """
        Create a new pipe that writes the generated database file into the given [output_directory].
        """
        self.__output_directory = output_directory

    @override
    def initialize_pipe(self) -> None:
        # Create/Open DB file
        # Create part of the schema (all tables and constraints, but no indices!)
        _logger.debug("Initializing routedb pipe for writing into %s", self.__output_directory)
