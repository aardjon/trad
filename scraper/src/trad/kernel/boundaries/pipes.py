"""
Boundary interface to the `pipes` component.
"""

from abc import ABCMeta, abstractmethod

from trad.kernel.entities import Post, Route, Summit


class Pipe(metaclass=ABCMeta):
    """
    Interface to the Pipe component all Filters work on.

    The pipe is the shared storage that filters can read from and write their modified data into.
    The concrete structure and technical details of the pipe storage are hidden behind this
    interface, so that there may be different implementations (e.g. for different schema versions).
    The goal is that no Filters need to be modified in case (only) the storage structure changes.

    Because there is only one Pipe and Filters may run in parallel, all pipe operations must be
    thread-safe.

    The pipe has an internal state: It must be initialized (by calling `initialize_pipe()`) before
    any other operation is allowed, and finalized (by calling `finalize_pipe()`) after everything
    else is done. If any method is called in the wrong state, it throws an InvalidStateError.
    """

    @abstractmethod
    def initialize_pipe(self) -> None:
        """
        Initializes the pipe for creating a new route database.

        Must be called exactly once prior to any other operation.
        """

    @abstractmethod
    def finalize_pipe(self) -> None:
        """
        Finalizes the creation of a new route database, closing the pipe.

        Must be called exactly once after all other operations are done. The Pipe is not usable
        anymore afterwards.
        """

    @abstractmethod
    def add_summit(self, summit: Summit) -> None:
        """
        Add the given [summit] data to the pipe if it doesn't exist already, or enriches the
        attributes missing in the existing one with the data of [summit]. "Missing" attributes are
        the ones that are set to the special *default* or *undefined* value in the existing data.
        Existing data is never dropped or replaced.
        """

    @abstractmethod
    def add_route(self, summit_name: str, route: Route) -> None:
        """
        Add the given [route] to the pipe, assigning it to the summit [summit_name]. If the route
        already exists, it's missing attributes are enriched with the data of [route]. "Missing"
        ones are the ones that are set to the special *default* or *undefined* value in the existing
        data. Existing data is never dropped or replaced.
        """

    @abstractmethod
    def add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        """
        Add the given [post] to the pipe, assigning it to the route [route_name] on the summit
        [summit_name].
        """


class PipeFactory(metaclass=ABCMeta):
    """
    Interface to the PipeFactory component which creates Pipe instances.
    """

    @abstractmethod
    def create_pipe(self) -> Pipe:
        """
        Creates and returns the pipe to be used, according to the global application settings.
        """
