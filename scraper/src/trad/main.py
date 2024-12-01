"""
The 'main' component of the trad scraper application.

This component is the main entry point which initializes and ties together all system parts and
starts the actual application.
"""

import logging

from trad.adapters.boundaries.database import RelationalDatabaseBoundary
from trad.adapters.boundaries.http import HttpNetworkingBoundary
from trad.adapters.cli import CliSettings
from trad.adapters.filters.factory import AllFiltersFactory
from trad.adapters.pipes.factory import AllPipesFactory
from trad.core.boundaries.filters import FilterFactory
from trad.core.boundaries.pipes import PipeFactory
from trad.core.boundaries.settings import SettingsBoundary
from trad.core.usecases import ScraperUseCases
from trad.crosscuttings.di import DependencyProvider
from trad.crosscuttings.logging import configure_logging
from trad.infrastructure.requests import RequestsHttp
from trad.infrastructure.sqlite3db import Sqlite3Database

_logger = logging.getLogger(__name__)


def main() -> None:
    """
    The central/main execution entry point.
    """
    bootstrap = ApplicationBootstrap()
    bootstrap.init_application()
    bootstrap.run_application()


class ApplicationBootstrap:
    """
    The application's bootstrapping process.

    An instance of this represents the startup process itself and is responsible for initializing
    the DI, i.e. for mapping concrete implementations to all boundary interfaces. After successful
    initialization, it can run the main use case.
    """

    def __init__(self) -> None:
        """Constructor."""
        self.__dependency_provider = DependencyProvider()

    def init_application(self) -> None:
        """
        Initialize the application.
        """
        self.__configure_application()
        self.__setup_logging()
        _logger.info("Initializing the trad scraper application...")
        self.__setup_dependencies()

    def __configure_application(self) -> None:
        """
        Initialize the application settings component.

        This is done separately because it may influence the other initialization steps.
        """
        self.__dependency_provider.register_singleton(SettingsBoundary, CliSettings)

    def __setup_logging(self) -> None:
        settings = self.__dependency_provider.provide(SettingsBoundary)
        configure_logging(logging.DEBUG if settings.is_verbose() else logging.INFO)

    def __setup_dependencies(self) -> None:
        """
        Setup all components (dependencies).
        """
        # Initialize all [adapters] components
        self.__dependency_provider.register_factory(
            PipeFactory, lambda: AllPipesFactory(self.__dependency_provider)
        )
        self.__dependency_provider.register_factory(
            FilterFactory, lambda: AllFiltersFactory(self.__dependency_provider)
        )

        # Initialize all [infrastructure] components
        self.__dependency_provider.register_singleton(RelationalDatabaseBoundary, Sqlite3Database)
        self.__dependency_provider.register_factory(HttpNetworkingBoundary, RequestsHttp)

    def run_application(self) -> None:
        """
        Runs the application, must be called after init_application().
        """
        _logger.info("Running the scraper application...")
        usecase = ScraperUseCases(self.__dependency_provider)
        usecase.produce_routedb()

        _logger.info("Scraper run has finished, terminating gracefully...")
        self.__dependency_provider.shutdown()
