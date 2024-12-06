"""
Filter for importing data from Teufelsturm.de.
"""

from logging import getLogger
from typing import Final, override

from trad.adapters.boundaries.http import HttpNetworkingBoundary
from trad.adapters.filters.filling.teufelsturm.parser import parse_page
from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class TeufelsturmDataFilter(Filter):
    """
    Filter for importing data from https://www.teufelsturm.de the pipe.

    This filter imports Summit, Route and Posting data, but doesn't overwrite them if already
    available.
    """

    _BASE_URL: Final = "https://www.teufelsturm.de/wege/bewertungen/anzeige.php?wegnr={}"

    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Constructor.
        """
        self._http_boundary = dependency_provider.provide(HttpNetworkingBoundary)

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.FILLING

    @override
    def get_name(self) -> str:
        return "teufelsturm.de"

    @override
    def execute_filter(self, pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        self._perform_scan(pipe, 11000, 13500)
        _logger.debug("'%s' filter finished", self.get_name())

    def _perform_scan(self, pipe: Pipe, start_id: int, end_id: int) -> None:
        count: Final = end_id - start_id + 1
        for page_id in range(start_id, end_id + 1):
            _logger.debug("Importing route %d (%d of %d)", page_id, page_id - start_id + 1, count)
            page_text = self._get_page_text(page_id)
            post_data = parse_page(page_text)
            if post_data.peak:
                pipe.add_summit_data(post_data.peak)
                pipe.add_route_data(summit_name=post_data.peak.name, route=post_data.route)
                for post in post_data.posts:
                    pipe.add_post_data(
                        summit_name=post_data.peak.name,
                        route_name=post_data.route.route_name,
                        post=post,
                    )

    def _get_page_text(self, route_id: int) -> str:
        """Returns the (text) content of the details page for the route with ID [route_id]."""
        url = self._BASE_URL.format(route_id)
        return self._http_boundary.retrieve_text_resource(url)
