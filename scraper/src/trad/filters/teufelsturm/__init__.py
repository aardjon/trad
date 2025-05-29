"""
Filter for importing data from Teufelsturm.de.
"""

from logging import getLogger
from typing import Final, override

from trad.adapters.boundaries.http import HttpNetworkingBoundary
from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.crosscuttings.di import DependencyProvider
from trad.filters.teufelsturm.parser import parse_page, parse_route_list

_logger = getLogger(__name__)


class TeufelsturmDataFilter(Filter):
    """
    Filter for importing data from https://www.teufelsturm.de into the pipe.

    This filter imports Summit, Route and Posting data, but doesn't overwrite them if already
    available.
    """

    _BASE_URL: Final = "https://www.teufelsturm.de/wege/"
    _ROUTE_LIST_URL: Final = _BASE_URL + "suche.php?start={start}&anzahl={count}"
    _ROUTE_DETAILS_URL: Final = _BASE_URL + "bewertungen/anzeige.php?wegnr={}"

    @override
    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Constructor.
        """
        super().__init__(dependency_provider)
        self._http_boundary = dependency_provider.provide(HttpNetworkingBoundary)

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.IMPORTING

    @override
    def get_name(self) -> str:
        return "teufelsturm.de"

    @override
    def execute_filter(self, pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        route_ids = self._collect_route_ids()
        self._perform_scan(pipe, route_ids)
        _logger.debug("'%s' filter finished", self.get_name())

    def _collect_route_ids(self) -> list[int]:
        """Returns the IDs of all available routes, collecting them from the routes list page."""
        chunk_size: Final = 15000
        route_ids: list[int] = []
        while True:
            start_idx = len(route_ids) + 1  # The remote site starts counting at 1
            _logger.debug("Requesting %d route IDs, starting with %d", chunk_size, start_idx)
            routelist_page = self._http_boundary.retrieve_text_resource(
                self._ROUTE_LIST_URL.format(
                    start=start_idx,
                    count=chunk_size,
                ),
            )
            chunk_ids = parse_route_list(routelist_page)
            route_ids.extend(chunk_ids)
            if len(chunk_ids) < chunk_size:
                break

        return route_ids

    def _perform_scan(self, pipe: Pipe, page_ids: list[int]) -> None:
        count: Final = len(page_ids)
        for idx, page_id in enumerate(page_ids):
            _logger.debug("Importing route %d of %d", idx + 1, count)
            page_text = self._get_page_text(page_id)
            post_data = parse_page(page_text)
            if post_data.peak:
                pipe.add_or_enrich_summit(post_data.peak)
                pipe.add_or_enrich_route(summit_name=post_data.peak.name, route=post_data.route)
                for post in post_data.posts:
                    pipe.add_post(
                        summit_name=post_data.peak.name,
                        route_name=post_data.route.route_name,
                        post=post,
                    )

    def _get_page_text(self, route_id: int) -> str:
        """Returns the (text) content of the details page for the route with ID [route_id]."""
        url = self._ROUTE_DETAILS_URL.format(route_id)
        return self._http_boundary.retrieve_text_resource(url)
