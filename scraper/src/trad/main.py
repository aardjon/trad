"""
The 'main' component of the trad scraper application.

This component is the main entry point which initializes and ties together all system parts and
starts the actual application.
"""

import logging
from functools import partial
from typing import TYPE_CHECKING

from trad.adapters.boundaries.database import RelationalDatabaseBoundary
from trad.adapters.boundaries.http import HttpNetworkingBoundary
from trad.adapters.cli import CliSettings
from trad.core.boundaries.filters import FilterFactory
from trad.core.boundaries.pipes import PipeFactory
from trad.core.boundaries.settings import SettingsBoundary
from trad.core.usecases import ScraperUseCases
from trad.crosscuttings.appmeta import APPLICATION_NAME, APPLICATION_VERSION
from trad.crosscuttings.di import DependencyProvider
from trad.crosscuttings.logging import configure_logging
from trad.filters.factory import AllFiltersFactory
from trad.infrastructure.http_recorder import TrafficRecorder
from trad.infrastructure.requests import RequestsHttp
from trad.infrastructure.sqlite3db import Sqlite3Database
from trad.pipes.factory import AllPipesFactory

if TYPE_CHECKING:
    from collections.abc import Callable

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
        _logger.info(
            "Initializing the %s application version %s...", APPLICATION_NAME, APPLICATION_VERSION
        )
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

        if settings.is_verbose():
            # Disable some log channels even in debug mode because they are still too chatty
            # The statement_creator logs all executed SQL statements on DEBUG level
            sql_statement_logger = logging.getLogger(
                "trad.infrastructure.sqlite3db.statement_creator"
            )
            sql_statement_logger.setLevel(logging.INFO)
            # urllib3 logs every single HTTP request
            urllib3_logger = logging.getLogger("urllib3")
            urllib3_logger.setLevel(logging.WARNING)

    def __setup_dependencies(self) -> None:
        """
        Setup all components (dependencies).
        """
        settings = self.__dependency_provider.provide(SettingsBoundary)

        # Initialize all [adapters] components
        self.__dependency_provider.register_factory(
            PipeFactory, lambda: AllPipesFactory(self.__dependency_provider)
        )
        self.__dependency_provider.register_factory(
            FilterFactory, lambda: AllFiltersFactory(self.__dependency_provider)
        )

        # Initialize all [infrastructure] components
        self.__dependency_provider.register_singleton(RelationalDatabaseBoundary, Sqlite3Database)

        traffic_recording_path = settings.get_traffic_recordings_path()
        network_factory: Callable[[], HttpNetworkingBoundary] = RequestsHttp
        if traffic_recording_path is not None and settings.is_record_traffic_mode():
            network_factory = partial(TrafficRecorder, traffic_recording_path, RequestsHttp())
        self.__dependency_provider.register_singleton(HttpNetworkingBoundary, network_factory)

    def run_application(self) -> None:
        """
        Runs the application, must be called after init_application().
        """
        _logger.info("Running the %s application...", APPLICATION_NAME)
        usecase = ScraperUseCases(self.__dependency_provider)
        usecase.produce_routedb()

        _logger.info("The %s application has finished, terminating gracefully...", APPLICATION_NAME)
        self.__dependency_provider.shutdown()
