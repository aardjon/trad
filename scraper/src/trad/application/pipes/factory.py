"""
Implementation of the PipeFactory component.
"""

from typing import override

from trad.application.boundaries.database import RelationalDatabaseBoundary
from trad.application.filters.db_v1 import DbSchemaV1Pipe
from trad.kernel.boundaries.pipes import Pipe, PipeFactory
from trad.kernel.boundaries.settings import SettingsBoundary
from trad.kernel.di import DependencyProvider


class AllPipesFactory(PipeFactory):
    """
    PipeFactory implementation that simply creates all available pipes.
    """

    def __init__(self, dependency_provider: DependencyProvider):
        """Create the factory instance."""
        self.__settings = dependency_provider.provide(SettingsBoundary)
        self.__database_boundary = dependency_provider.provide(RelationalDatabaseBoundary)

    @override
    def create_pipe(self) -> Pipe:
        destination_path = self.__settings.get_output_dir()
        return DbSchemaV1Pipe(destination_path, self.__database_boundary)
