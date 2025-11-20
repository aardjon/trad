"""
VALIDATION stage Filter implementation.
"""

from collections.abc import Collection, Mapping
from logging import getLogger
from typing import override

from trad.kernel.boundaries.filters import Filter, FilterStage
from trad.kernel.boundaries.pipes import Pipe, RouteInstanceId
from trad.kernel.entities import Post, Route, Summit
from trad.kernel.errors import IncompleteDataError

_logger = getLogger(__name__)


class DataValidationFilter(Filter):
    """
    A Filter for validating the processed data. This is done to ensure the data integrity. Found
    problems can be handled by one of these actions:
     - Fix the problem automatically
     - Ignore this data set completely (i.e. don't write it into the output pipe)
     - Cancel the whole process
    """

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.VALIDATION

    @override
    def get_name(self) -> str:
        return "DataValidation"

    @override
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        for input_summit_id, summit in input_pipe.iter_summits():
            if not self._validate_summit(summit):
                continue

            ignore_current_summit = False
            routes = {}
            posts = {}
            for route_id, route in input_pipe.iter_routes_of_summit(input_summit_id):
                if not self._validate_route(summit, route):
                    ignore_current_summit = True
                    break
                routes[route_id] = route
                posts[route_id] = list(input_pipe.iter_posts_of_route(route_id))

            if ignore_current_summit:
                continue

            # No errors, so all data of this summit seems to be valid
            self._write_summit_to_pipe(output_pipe, summit, routes, posts)

    def _validate_summit(self, summit: Summit) -> bool:
        """
        Returns True if the given Summit data is valid (either because it was already, or it could
        be fixed), False if not.
        """
        try:
            summit.fix_invalid_data()
        except IncompleteDataError as e:
            _logger.warning("Ignoring summit because of incomplete data", exc_info=e)
            return False
        return True

    def _validate_route(self, summit: Summit, route: Route) -> bool:
        """
        Returns True if the given Route data is valid (either because it was already, or it could
        be fixed), False if not.
        """
        try:
            route.fix_invalid_data()
        except IncompleteDataError as e:
            _logger.warning(
                "Ignoring summit '%s' because of incomplete route data",
                summit.name,
                exc_info=e,
            )
            return False
        return True

    def _write_summit_to_pipe(
        self,
        output_pipe: Pipe,
        summit: Summit,
        routes: Mapping[RouteInstanceId, Route],
        posts: Mapping[RouteInstanceId, Collection[Post]],
    ) -> None:
        output_summit_id = output_pipe.add_summit(summit)
        for input_route_id, route in routes.items():
            output_route_id = output_pipe.add_route(output_summit_id, route)
            for post in posts.get(input_route_id, []):
                output_pipe.add_post(output_route_id, post)
