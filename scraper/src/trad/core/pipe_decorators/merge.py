"""
Provides the functionality of merging different data objects (e.g. from different sources) that
actually describe the same physical entity into a single one.
"""

from collections.abc import Collection
from logging import getLogger
from typing import override

from trad.core.boundaries.pipes import Pipe
from trad.core.entities import Post, Route, Summit, UniqueIdentifier
from trad.core.errors import EntityNotFoundError

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
        self._summit_name_lookup_map: dict[UniqueIdentifier, Summit] = {}
        self._routes: dict[UniqueIdentifier, list[Route]] = {}
        self._posts: list[tuple[UniqueIdentifier, str, Post]] = []

    @override
    def initialize_pipe(self) -> None:
        self._delegate.initialize_pipe()

    @override
    def finalize_pipe(self) -> None:
        # Finally, write all collected data into the delegate pipe
        _logger.debug("Writing summits with %s names...", len(self._summit_name_lookup_map))
        seen_summit_ids: set[int] = set()
        for summit in self._summit_name_lookup_map.values():
            if id(summit) not in seen_summit_ids:
                self._delegate.add_or_enrich_summit(summit)
                seen_summit_ids.add(id(summit))

        for summit_id, routes in self._routes.items():
            summit = self._summit_name_lookup_map[summit_id]
            _logger.debug("Writing %s routes for summit '%s'...", len(routes), summit.name)
            for route in routes:
                self._delegate.add_or_enrich_route(summit.name, route)

        _logger.debug("Writing %s posts...", len(self._posts))
        for summit_id, route_name, post in self._posts:
            summit = self._summit_name_lookup_map[summit_id]
            self._delegate.add_post(summit.name, route_name, post)

        # Delete all in-memory data
        self._summit_name_lookup_map.clear()
        self._routes.clear()
        self._posts.clear()

        _logger.debug("Finalizing all pipes...")
        self._delegate.finalize_pipe()

    @override
    def add_or_enrich_summit(self, summit: Summit) -> None:
        # Find all Summit objects that are physically the same as the new one (i.e. share a name)
        existing_summits_to_merge: dict[int, Summit] = {}
        for identifier in summit.get_all_possible_identifiers():
            existing_summit = self._summit_name_lookup_map.get(identifier, None)
            if existing_summit is not None:
                existing_summits_to_merge[id(existing_summit)] = existing_summit
        summits_to_merge = [*existing_summits_to_merge.values(), summit]

        # Merge all found summits into the first one
        destination_summit = summits_to_merge[0]
        for merge_summit in summits_to_merge[1:]:
            destination_summit.enrich(merge_summit)

        # Make sure that the corresponding _summit_name_lookup_map entries refer to the destination
        # object, by (re-)assing all (possibly extended) identifiers.
        for identifier in destination_summit.get_all_possible_identifiers():
            self._summit_name_lookup_map[identifier] = destination_summit

        # TODO(aardjon): Existing routes need to be merged, too! Not necessary with only Teufelsturm
        #                and OSM data being merged, though, because we don't gather route data from
        #                OSM.

    @override
    def add_or_enrich_route(self, summit_name: str, route: Route) -> None:
        self._routes.setdefault(self._get_summit_id(summit_name), []).append(route)

    @override
    def add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        self._posts.append((self._get_summit_id(summit_name), route_name, post))

    def _get_summit_id(self, summit_name: str) -> UniqueIdentifier:
        """
        Return the unique ID the of summit with the given `summit_name`. Raises EntityNotFoundError
        if no such summit can be found.
        """
        summit_id = UniqueIdentifier(summit_name)
        try:
            return self._summit_name_lookup_map[summit_id].unique_identifier
        except KeyError:
            raise EntityNotFoundError(summit_name) from None

    def get_collected_summits(self) -> Collection[Summit]:
        """
        Return all Summits that have been collected and merged so far. This is meant to be used by
        unit tests only, don't use it in production code.
        """
        all_summits = []
        seen_summit_ids = []
        for summit in self._summit_name_lookup_map.values():
            if id(summit) not in seen_summit_ids:
                seen_summit_ids.append(id(summit))
                all_summits.append(summit)
        return all_summits

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
