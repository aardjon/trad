"""
Boundary interface to the `pipes` component.
"""

from abc import ABCMeta, abstractmethod

from trad.core.entities import Post, Route, Summit


class Pipe(metaclass=ABCMeta):
    """
    Interface to the Pipe component all Filters work on.

    The pipe is the shared storage that filters can read from and write their modified data into.
    The concrete structure and technical details of the pipe storage are hidden behind this
    interface, so that there may be different implementations (e.g. for different schema versions).
    The goal is that no Filters need to be modified in case (only) the storage structure changes.

    Because there is only one Pipe and Filters may run in parallel, all pipe operations must be
    thread-safe.

    The pipe has an internal state: It must be initialized (by calling initialize_pipe()) before any
    other operation is allowed. If any method is called in the wrong state, it throws an
    InvalidStateError.
    """

    @abstractmethod
    def initialize_pipe(self) -> None:
        """
        Initializes the pipe for creating a new route database.

        Must be called exactly once prior to any other operation.
        """

    @abstractmethod
    def collect_statistics(self) -> None:
        """
        Analyzes the storage content and collects and stores some statistical information to improve
        the performance of future data query.
        """

    @abstractmethod
    def shrink(self) -> None:
        """
        Shrinks the current route database result file to the necessary minimum, without deleting
        or compressing any data.
        """

    @abstractmethod
    def add_summit_data(self, summit: Summit) -> None:
        """
        Add the given [summit] data to the pipe.
        """

    @abstractmethod
    def add_route_data(self, summit_name: str, route: Route) -> None:
        """
        Add the given [route] to the pipe, assigning it to the summit [summit_name].
        """

    @abstractmethod
    def add_post_data(self, summit_name: str, route_name: str, post: Post) -> None:
        """
        Add the given [post] to the pipe, assigning it to the route [route_name] on the summit
        [summit_name].
        """


class PipeFactory(metaclass=ABCMeta):
    """
    Interface to the PipeFactory component which creates Pipe instances.
    """

    @abstractmethod
    def create_pipes(self) -> list[Pipe]:
        """
        Creates and returns all available pipes.

        Multiple pipes are e.g. configured to create several databases with different schema
        versions in one run.
        """
