"""
Provides a fake network component to be used by the OSM filter tests.
"""

import json
from collections.abc import Mapping, Sequence
from typing import override

from trad.application.boundaries.http import HttpNetworkingBoundary, JsonData


class FakeNetwork(HttpNetworkingBoundary):
    """
    Fake HTTP networking component to be used by unit test cases.

    Allow to inject certain HTTP query response data.
    """

    def __init__(
        self,
        nominatim_response: Sequence[Mapping[str, object]],
        overpass_area_query_response: Mapping[str, object] | None = None,
        overpass_parent_relations_query_response: Mapping[str, object] | None = None,
        overpass_relation_members_query_response: Mapping[str, object] | None = None,
    ):
        self._nominatim_response = JsonData(json.dumps(nominatim_response))
        self._overpass_responses = [
            JsonData(json.dumps(response)) if response is not None else JsonData("")
            for response in (
                overpass_area_query_response,
                overpass_parent_relations_query_response,
                overpass_relation_members_query_response,
            )
        ]
        self._overpass_query_count = 0

    @override
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        # The OSM filter shouldn't access any text resources
        raise NotImplementedError("OSM filter unexpectedly accessed a text resource")

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        if "nominatim" in url:
            return self._nominatim_response
        if "overpass" in url:
            response = self._overpass_responses[self._overpass_query_count]
            self._overpass_query_count += 1
            return response
        raise NotImplementedError(f"OSM filter requested unexpected URL {url}")
