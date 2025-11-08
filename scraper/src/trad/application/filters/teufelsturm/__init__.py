"""
Filter for importing data from Teufelsturm.de.
"""

from logging import getLogger
from typing import Final, override

from trad.application.adapters.boundaries.http import HttpNetworkingBoundary
from trad.application.filters.teufelsturm.parser import SummitCache, parse_page, parse_route_list
from trad.kernel.boundaries.filters import Filter, FilterStage
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.di import DependencyProvider
from trad.kernel.entities import Summit

_logger = getLogger(__name__)


class TeufelsturmDataFilter(Filter):
    """
    Filter for importing data from https://www.teufelsturm.de into the pipe.

    This filter imports Summit, Route and Posting data, but doesn't overwrite them if already
    available.
    """

    _BASE_URL: Final = "https://www.teufelsturm.de/"
    _ROUTE_LIST_URL: Final = _BASE_URL + "wege/suche.php?start={start}&anzahl={count}"
    _ROUTE_DETAILS_URL: Final = _BASE_URL + "wege/bewertungen/anzeige.php?wegnr={}"
    _SUMMIT_DETAILS_URL: Final = _BASE_URL + "gipfel/details.php?gipfelnr={summit_id}"

    @override
    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Constructor.
        """
        super().__init__(dependency_provider)
        self._http_boundary = dependency_provider.provide(HttpNetworkingBoundary)
        self._summit_cache = SummitCache(retrieve_summit_details_page=self._get_summit_page_text)
        self._added_peak_name_hashes: set[int] = set()
        """
        Set of peak/summit name hashes that were already added to the Pipe.

        This Filter iterates all routes, and therefore each summit/peak occurs once for each of its
        routes (with exactly the same data every time). Adding a summit to the Pipe can be quite
        expensive, that's why we want to do this only once (on first occurence) and not over and
        over again (for each route). On Teufelsturm, summit names are unique. We store their hashes
        only to speed up the lookup.
        """

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
        self._summit_cache.clear_cache()
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
            if (idx + 1) % 25 == 0:
                # Don't log every single route index
                _logger.debug("Importing route %d of %d", idx + 1, count)
            page_text = self._get_page_text(page_id)
            post_data = parse_page(page_text, self._summit_cache)
            if not self._is_forbidden(post_data.peak):
                if hash(post_data.peak.name) not in self._added_peak_name_hashes:
                    # Each summit must be added to the pipe only once (for performance)
                    pipe.add_or_enrich_summit(post_data.peak)
                    self._added_peak_name_hashes.add(hash(post_data.peak.name))
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

    def _get_summit_page_text(self, peak_id: int) -> str:
        """Returns the (text) content of the details page for the summit with ID [peak_id]."""
        url = self._SUMMIT_DETAILS_URL.format(summit_id=peak_id)
        return self._http_boundary.retrieve_text_resource(url)

    def _is_forbidden(self, summit: Summit) -> bool:
        """
        Return True if climbing is completely forbidden on the given summit, otherwise False.
        Teufelsturm contains data for summits that were accessible in the past but have been closed
        in the meantime, and we don't want to include them.

        TODO(aardjon): This information can probably be taken from OSM, so it's probably better to
                       take it from there instead of using this hard-coded list.
        """
        forbidden_summit_names: Final = {
            "Adlerlochturm",
            "Hirschsuhlenturm",
            "Kleiner Turm",
            "Litfaßsäule",
            "Schwarze Spitze",
            "Schwarzschlüchteturm",
            "Slawe",
            "Wobstspitze",
        }
        if summit.name in forbidden_summit_names:
            _logger.debug("Ignoring forbidden summit %s", summit.name)
            return True
        return False
