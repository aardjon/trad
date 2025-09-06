"""
Provides the functionality of merging different data objects (e.g. from different sources) that
actually describe the same physical entity into a single one.
"""

from collections.abc import Collection
from contextlib import suppress
from logging import getLogger
from typing import Final, override

from trad.core.boundaries.pipes import Pipe
from trad.core.entities import UNDEFINED_GEOPOSITION, NormalizedName, Post, Route, Summit
from trad.core.errors import EntityNotFoundError

_logger = getLogger(__name__)


class MergingPipeDecorator(Pipe):
    """
    A special Pipe implementation which collects (and merges) all data in memory, and sends the
    merged data to the real Pipes during finalization only.

    This is an implementation of the *Decorator* design pattern (don't mix it up with Python
    decorators!).

    TODO(aardjon): Routes are not correctly merged yet because atm there is only ever one single
                   source for routes which is also retrieved last. This must be fixed!
    """

    def __init__(self, delegate_pipe: Pipe) -> None:
        """
        Create a new Pipe decorator which sends all collected data to the given `delegate_pipe`.
        """
        super().__init__()
        self._delegate = delegate_pipe
        self._summits: list[Summit] = []
        self._routes: dict[NormalizedName, list[Route]] = {}
        self._posts: dict[NormalizedName, dict[str, list[Post]]] = {}

    @override
    def initialize_pipe(self) -> None:
        self._delegate.initialize_pipe()

    @override
    def finalize_pipe(self) -> None:
        # Finally, write all collected data into the delegate pipe
        summit_count = len(self._summits)
        _logger.debug("Writing summits with %s names...", summit_count)
        for idx, summit in enumerate(self._summits):
            self._delegate.add_or_enrich_summit(summit)
            routes = self._routes.get(summit.normalized_name, [])
            _logger.debug(
                "Writing %s routes for summit %d/%d ('%s')...",
                len(routes),
                idx + 1,
                summit_count,
                summit.name,
            )
            for route in routes:
                self._delegate.add_or_enrich_route(summit.name, route)

                posts = self._posts.get(summit.normalized_name, {}).get(route.route_name, [])
                for post in posts:
                    self._delegate.add_post(summit.name, route.route_name, post)

        # Delete all in-memory data
        self._summits.clear()
        self._routes.clear()
        self._posts.clear()

        _logger.debug("Finalizing all pipes...")
        self._delegate.finalize_pipe()

    @override
    def add_or_enrich_summit(self, summit: Summit) -> None:
        new_summit_normalized_names = set(summit.get_all_normalized_names())
        # Find all alreay known Summit objects that are physically the same as the new one
        match_search_radius: Final = 200  # Radius in meters
        existing_summits_to_merge: dict[int, Summit] = {}
        for existing_summit in self._summits:
            if new_summit_normalized_names.intersection(
                existing_summit.get_all_normalized_names()
            ) and (
                (
                    existing_summit.position is UNDEFINED_GEOPOSITION
                    or summit.position is UNDEFINED_GEOPOSITION
                )
                or existing_summit.position.is_within_radius(summit.position, match_search_radius)
            ):
                existing_summits_to_merge[id(existing_summit)] = existing_summit
        summits_to_merge = [*existing_summits_to_merge.values(), summit]

        # Merge all found summits into the first one and remove them from the self._summits list (if
        # necessary)
        destination_summit = summits_to_merge[0]
        for merge_summit in summits_to_merge[1:]:
            destination_summit.enrich(merge_summit)
            with suppress(ValueError):
                self._summits.remove(merge_summit)

        # Make sure that the destination summit is contained in self._summits list, because it may
        # have been the first of its kind (without any merging happening)
        if destination_summit not in self._summits:
            self._summits.append(destination_summit)

        # TODO(aardjon): Existing routes need to be merged, too! Not necessary with only Teufelsturm
        #                and OSM data being merged, though, because we don't gather route data from
        #                OSM.

    @override
    def add_or_enrich_route(self, summit_name: str, route: Route) -> None:
        self._routes.setdefault(self._find_first_summit(summit_name).normalized_name, []).append(
            route
        )

    @override
    def add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        self._posts.setdefault(self._find_first_summit(summit_name).normalized_name, {}).setdefault(
            route_name, []
        ).append(post)

    def _find_first_summit(self, summit_name: str) -> Summit:
        """
        Find the first summit object with the given `summit_name`. Raises EntityNotFoundError if no
        such summit can be found.
        """
        normalized_name = NormalizedName(summit_name)
        try:
            return next(
                summit
                for summit in self._summits
                if normalized_name in summit.get_all_normalized_names()
            )
        except StopIteration:
            raise EntityNotFoundError(summit_name) from None

    def get_collected_summits(self) -> Collection[Summit]:
        """
        Return all Summits that have been collected and merged so far. This is meant to be used by
        unit tests only, don't use it in production code.
        """
        return self._summits

    def get_collected_routes(self, summit_name: str) -> Collection[Route]:
        """
        Return all Routes that have been collected for the requested summit so far. This is meant to
        be used by unit tests only, don't use it in production code.
        """
        return self._routes.get(NormalizedName(summit_name), [])

    def get_collected_posts(self, summit_name: str, route_name: str) -> Collection[Post]:
        """
        Return all Posts that have been collected for the requested route so far. This is meant to
        be used by unit tests only, don't use it in production code.
        """
        summit_id = NormalizedName(summit_name)
        return self._posts.get(summit_id, {}).get(route_name, [])
