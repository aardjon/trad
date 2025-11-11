"""
Boundary interface to the `pipes` component.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
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

    The pipe is the shared storage that filters can read from or write their modified data into.
    The concrete structure and technical details of the storage is hidden behind this interface,
    though.
    For each stage, two Pipe instances are created and handed to all of its Filters, that's why
    Filters get an input and an output pipe. Because several Filters may access the same Pipe in
    parallel, all pipe operations are thread-safe.
    """

    @abstractmethod
    def add_summit(self, summit: Summit) -> SummitInstanceId:
        """
        Add the given [summit] data to the pipe. Returns the assigned ID for the newly added summit.
        Existing data is never dropped or replaced.

        The returned ID is only valid for the current Filter and Pipe instances!
        """

    @abstractmethod
    def add_route(self, summit_id: SummitInstanceId, route: Route) -> RouteInstanceId:
        """
        Add the given [route] to the pipe, assigning it to the summit identified by [summit_id].
        Returns the assigned ID for the newly added route. Existing data is never dropped or
        replaced.
        Raises EntityNotFoundError if the given `summit_id` doesn't exist.

        The returned ID is only valid for the current Filter and Pipe instances!
        """

    @abstractmethod
    def add_post(self, route_id: RouteInstanceId, post: Post) -> None:
        """
        Add the given [post] to the pipe, assigning it to the route identified by [route_id].
        Existing data is never dropped or replaced.
        Raises EntityNotFoundError if the given `route_id` doesn't exist.
        """

    @abstractmethod
    def iter_summits(self) -> Iterator[tuple[SummitInstanceId, Summit]]:
        """
        Return all stored summits together with their instance IDs. The returned IDs are only valid
        for the current Filter and Pipe instances!
        """

    @abstractmethod
    def iter_routes_of_summit(
        self, summit_id: SummitInstanceId
    ) -> Iterator[tuple[RouteInstanceId, Route]]:
        """
        Return all routes together with their instance ID, that belong to the summit with the given
        `summit_id`. The returned IDs are only valid for the current Filter and Pipe instances!
        Returns an empty iterator if `summit_id` doesn't exist.
        """

    @abstractmethod
    def iter_posts_of_route(self, route_id: RouteInstanceId) -> Iterator[Post]:
        """
        Return all posts that belong to the route with the given `route_id`, or an empty iterator if
        `route_id` doesn't exist.
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
