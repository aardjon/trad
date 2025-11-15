"""
Filter for importing data from Teufelsturm.de.
"""

from logging import getLogger
from typing import Final, override

from trad.application.boundaries.http import HttpNetworkingBoundary
from trad.application.filters._base import SourceFilter
from trad.application.filters.teufelsturm.parser import SummitCache, parse_page, parse_route_list
from trad.kernel.boundaries.filters import FilterStage
from trad.kernel.boundaries.pipes import Pipe, SummitInstanceId
from trad.kernel.entities import Summit

_logger = getLogger(__name__)


class TeufelsturmDataFilter(SourceFilter):
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
    def __init__(self, network_boundary: HttpNetworkingBoundary) -> None:
        """
        Create a new TeufelsturmDataFilter instance that retrieves data via the given
        [network_boundary].
        """
        super().__init__()
        self._http_boundary = network_boundary
        self._summit_cache = SummitCache(retrieve_summit_details_page=self._get_summit_page_text)
        self._added_peak_name_hashes: dict[int, SummitInstanceId] = {}
        """
        Peak/summit name hashes that were already added to the Pipe, and their assigned IDs.

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
    def _execute_source_filter(self, output_pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        route_ids = self._collect_route_ids()
        self._perform_scan(output_pipe, route_ids)
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
                summit_id = self._added_peak_name_hashes.get(hash(post_data.peak.name))
                if summit_id is None:
                    # Each summit must be added to the pipe only once (for performance)
                    summit_id = pipe.add_summit(post_data.peak)
                    self._added_peak_name_hashes[hash(post_data.peak.name)] = summit_id
                route_id = pipe.add_route(summit_id=summit_id, route=post_data.route)
                for post in post_data.posts:
                    pipe.add_post(
                        route_id=route_id,
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
