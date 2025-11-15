"""
Provides the functionality of merging different data objects (e.g. from different sources) that
actually describe the same physical entity into a single one.
"""

from collections.abc import Collection
from contextlib import suppress
from logging import getLogger
from typing import Final, override

from trad.kernel.boundaries.filters import Filter, FilterStage
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import UNDEFINED_GEOPOSITION, NormalizedName, Post, Route, Summit
from trad.kernel.errors import EntityNotFoundError

_logger = getLogger(__name__)


class MergeFilter(Filter):
    """
    A Filter for merging Summit (and Route) instances that are actually describing the same physical
    object into a single instance.

    TODO(aardjon): Routes are not correctly merged yet because atm there is only ever one single
                   source for routes which is also retrieved last. This must be fixed!
    """

    def __init__(self) -> None:
        """
        Create a new MergeFilter instance.
        """
        self._summits: list[Summit] = []
        self._routes: dict[NormalizedName, list[Route]] = {}
        self._posts: dict[NormalizedName, dict[str, list[Post]]] = {}

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.OPTIMIZATION

    @override
    def get_name(self) -> str:
        return "DataMerge"

    @override
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        for summit_id, summit in input_pipe.iter_summits():
            self._add_summit(summit)
            for route_id, route in input_pipe.iter_routes_of_summit(summit_id):
                self._add_route(summit.name, route)
                for post in input_pipe.iter_posts_of_route(route_id):
                    self._add_post(summit.name, route.route_name, post)
        self._write_merged_data(output_pipe)

    def _write_merged_data(self, output_pipe: Pipe) -> None:
        # Write all collected data into the output pipe
        summit_count = len(self._summits)
        _logger.debug("Writing summits with %s names...", summit_count)
        for idx, summit in enumerate(self._summits):
            summit_id = output_pipe.add_summit(summit)
            routes = self._routes.get(summit.normalized_name, [])
            _logger.debug(
                "Writing %s routes for summit %d/%d ('%s')...",
                len(routes),
                idx + 1,
                summit_count,
                summit.name,
            )
            for route in routes:
                route_id = output_pipe.add_route(summit_id, route)

                posts = self._posts.get(summit.normalized_name, {}).get(route.route_name, [])
                for post in posts:
                    output_pipe.add_post(route_id, post)

        # Delete all in-memory data
        self._summits.clear()
        self._routes.clear()
        self._posts.clear()

    def _add_summit(self, summit: Summit) -> None:
        new_summit_normalized_names = set(summit.get_all_normalized_names())
        # Find all already known Summit objects that are physically the same as the new one
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

    def _add_route(self, summit_name: str, route: Route) -> None:
        self._routes.setdefault(self._find_first_summit(summit_name).normalized_name, []).append(
            route
        )

    def _add_post(self, summit_name: str, route_name: str, post: Post) -> None:
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
