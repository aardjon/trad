"""
Boundary interface to the `pipes` component.
"""

from abc import ABCMeta, abstractmethod
from typing import NewType

from trad.kernel.entities import Post, Route, Summit

SummitInstanceId = NewType("SummitInstanceId", int)
"""
Identifier for a certain Summit object within the current Pipe (not the summit itself!). This ID is
only valid within a single Pipe instance, i.e. only for the Filter that got it.
"""

RouteInstanceId = NewType("RouteInstanceId", int)
"""
Identifier for a certain Route object within the current Pipe (not the route itself!). This ID is
only valid within a single Pipe instance, i.e. only for the Filter that got it.
"""


class Pipe(metaclass=ABCMeta):
    """
    Interface to the Pipe component all Filters work on.

    The pipe is the shared storage that filters can read from and write their modified data into.
    A new Pipe is created for each stage, that's why Filters can get an input and an output pipe.
    The concrete structure and technical details of the storage is hidden behind this interface,
    though.

    Because several Filters may access tze same Pipe in parallel, all pipe operations are
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
    def add_summit(self, summit: Summit) -> SummitInstanceId:
        """
        Add the given [summit] data to the pipe. Returns the assigned ID for the newly added summit.
        Existing data is never dropped or replaced.

        The returned ID is only valid for the current Filter!
        """

    @abstractmethod
    def add_route(self, summit_id: SummitInstanceId, route: Route) -> RouteInstanceId:
        """
        Add the given [route] to the pipe, assigning it to the summit identified by [summit_id].
        Returns the assigned ID for the newly added route. Existing data is never dropped or
        replaced.
        Raises EntityNotFoundError if the given `summit_id` doesn't exist.

        The returned ID is only valid for the current Filter!
        """

    @abstractmethod
    def add_post(self, route_id: RouteInstanceId, post: Post) -> None:
        """
        Add the given [post] to the pipe, assigning it to the route identified by [route_id].
        Existing data is never dropped or replaced.
        Raises EntityNotFoundError if the given `route_id` doesn't exist.
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
