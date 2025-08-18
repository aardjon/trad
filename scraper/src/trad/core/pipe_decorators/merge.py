"""
Provides the functionality of merging different data objects (e.g. from different sources) that
actually describe the same physical entity into a single one.
"""

from collections.abc import Collection
from logging import getLogger
from typing import override

from trad.core.boundaries.pipes import Pipe
from trad.core.entities import UNDEFINED_GEOPOSITION, Post, Route, Summit, UniqueIdentifier
from trad.core.errors import MergeConflictError

_logger = getLogger(__name__)


class MergingPipeDecorator(Pipe):
    """
    A special Pipe implementation which collects (and merges) all data in memory, and sends the
    merged data to the real Pipes during finalization only.

    This is an implementation of the *Decorator* design pattern (don't mix it up with Python
    decorators!).
    """

    def __init__(self, delegate_pipe: Pipe) -> None:
        """
        Create a new Pipe decorator which sends all collected data to the given `delegate_pipe`.
        """
        super().__init__()
        self._delegate = delegate_pipe
        self._summits: dict[UniqueIdentifier, Summit] = {}
        self._routes: dict[UniqueIdentifier, list[Route]] = {}
        self._posts: list[tuple[UniqueIdentifier, str, Post]] = []

    @override
    def initialize_pipe(self) -> None:
        self._delegate.initialize_pipe()

    @override
    def finalize_pipe(self) -> None:
        # Finally, write all collected data into the delegate pipe
        _logger.debug("Writing %s summits...", len(self._summits))
        for summit in self._summits.values():
            self._delegate.add_or_enrich_summit(summit)

        for summit_id, routes in self._routes.items():
            summit = self._summits[summit_id]
            _logger.debug("Writing %s routes for summit '%s'...", len(routes), summit.name)
            for route in routes:
                self._delegate.add_or_enrich_route(summit.name, route)

        _logger.debug("Writing %s posts...", len(self._posts))
        for summit_id, route_name, post in self._posts:
            summit = self._summits[summit_id]
            self._delegate.add_post(summit.name, route_name, post)

        # Delete all in-memory data
        self._summits.clear()
        self._routes.clear()
        self._posts.clear()

        _logger.debug("Finalizing all pipes...")
        self._delegate.finalize_pipe()

    @override
    def add_or_enrich_summit(self, summit: Summit) -> None:
        existing_summit = self._summits.get(summit.unique_identifier)
        if existing_summit is None:
            self._summits[summit.unique_identifier] = summit
            return

        if existing_summit.position == UNDEFINED_GEOPOSITION:
            existing_summit.position = summit.position
        elif summit.position != UNDEFINED_GEOPOSITION:
            raise MergeConflictError("summit", summit.name, "position")

    @override
    def add_or_enrich_route(self, summit_name: str, route: Route) -> None:
        self._routes.setdefault(UniqueIdentifier(summit_name), []).append(route)

    @override
    def add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        self._posts.append((UniqueIdentifier(summit_name), route_name, post))

    def get_collected_summits(self) -> Collection[Summit]:
        """
        Return all Summits that have been collected and merged so far. This is meant to be used by
        unit tests only, don't use it in production code.
        """
        return self._summits.values()

    def get_collected_routes(self, summit_name: str) -> Collection[Route]:
        """
        Return all Routes that have been collected for the requested summit so far. This is meant to
        be used by unit tests only, don't use it in production code.
        """
        return self._routes.get(UniqueIdentifier(summit_name), [])

    def get_collected_posts(self, summit_name: str, route_name: str) -> Collection[Post]:
        """
        Return all Posts that have been collected for the requested route so far. This is meant to
        be used by unit tests only, don't use it in production code.
        """
        summit_id = UniqueIdentifier(summit_name)
        return [
            post
            for summit, route, post in self._posts
            if summit == summit_id and route == route_name
        ]
