"""
Unit tests for the 'trad.application.filters.source.osm.filter' module (and therefore, most of the
'trad.application.filters.source.osm' package).
"""

import json
from typing import Final
from unittest.mock import Mock

import pytest

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.application.filters.source.osm.filter import OsmDataFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.errors import DataProcessingError, DataRetrievalError

from .fake_network import FakeNetwork


class TestOsmDataFilter:
    """
    General (i.e. not data kind specific) test cases for the OsmDataFilter class.
    """

    def test_name(self) -> None:
        """
        Ensures the filter name to be correct.
        """
        osm_filter = OsmDataFilter(Mock(HttpNetworkingBoundary))
        assert "OpenStreetMap" in osm_filter.get_name()

    @pytest.mark.parametrize("summit_count", [1, 3, 0])
    def test_external_sources(self, summit_count: int) -> None:
        """
        Ensure that an external source is added along with imported data:
         - The source definition must contain the correct data
         - There must be exactly one source

        :param summit_count: The number of Summits being imported.
        """
        fake_network_boundary = FakeNetwork(
            nominatim_response=[{"osm_id": 4711}],
            overpass_area_query_response={
                "elements": [
                    {
                        "id": i,
                        "type": "node",
                        "lat": 13.37,
                        "lon": 47.11,
                        "tags": {
                            "natural": "peak",
                            "name": f"Summit{i}",
                        },
                    }
                    for i in range(summit_count)
                ]
            },
            overpass_parent_relations_query_response={
                "elements": [
                    {
                        "id": 123,
                        "type": "relation",
                        "tags": {"name": "Test Sector"},
                        "members": [{"type": "relation", "ref": i} for i in range(summit_count)],
                    },
                ]
            },
        )
        osm_filter = OsmDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        # The resulting Pipe must contain exactly one external source definition
        actual_sources = list(output_pipe.get_sources())
        assert len(actual_sources) == 1
        assert actual_sources[0].label == "OpenStreetMap"
        assert actual_sources[0].url == "https://www.openstreetmap.org"
        assert actual_sources[0].attribution == "OSM Contributors"
        assert actual_sources[0].license_name == "ODbL"

    @pytest.mark.parametrize(
        ("nominatim_response", "expected_exception"),
        [
            (  # Network error
                HttpRequestError("Fake network error"),
                DataRetrievalError,
            ),
            (  # Empty response
                "",
                DataProcessingError,
            ),
            (  # Invalid JSON response
                "invalid_json",
                DataProcessingError,
            ),
            (  # Empty result list, i.e. no matching area found
                "[]",
                DataProcessingError,
            ),
        ],
    )
    def test_nominatim_error(
        self,
        nominatim_response: str | Exception,
        expected_exception: type[Exception],
    ) -> None:
        """
        Ensures the correct behaviour in case of errors during the Nominatim request.
        """
        mocked_network_boundary = Mock(HttpNetworkingBoundary)
        mocked_network_boundary.retrieve_json_resource.side_effect = [nominatim_response]
        osm_filter = OsmDataFilter(mocked_network_boundary)

        with pytest.raises(expected_exception):
            osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=Mock(Pipe))
        # Make sure there was only one network request in total
        mocked_network_boundary.retrieve_json_resource.assert_called_once()

    @pytest.mark.parametrize(
        ("overpass_response", "expected_exception"),
        [
            (  # Network Error
                HttpRequestError("Fake network error"),
                DataRetrievalError,
            ),
            (  # Empty JSON response
                "",
                DataProcessingError,
            ),
            (  # Invalid JSON response
                "invalid json data",
                DataProcessingError,
            ),
        ],
    )
    def test_overpass_error(
        self,
        overpass_response: str | Exception,
        expected_exception: type[Exception],
    ) -> None:
        """
        Ensures the correct behaviour in case of errors during the Overpass request.
        """
        valid_nominatim_response: Final = '[{"osm_id": 42}]'
        expected_network_request_count: Final = 2

        mocked_network_boundary = Mock(HttpNetworkingBoundary)
        mocked_network_boundary.retrieve_json_resource.side_effect = [
            valid_nominatim_response,
            overpass_response,
        ]
        osm_filter = OsmDataFilter(mocked_network_boundary)

        with pytest.raises(expected_exception):
            osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=Mock(Pipe))
        # Make sure there were exactly two network requests in total
        assert (
            mocked_network_boundary.retrieve_json_resource.call_count
            == expected_network_request_count
        )

    def test_network_usage(self) -> None:
        """
        Ensure that the OSM filter uses the external network correctly (in the "happy path" case):
         - All network boundary calls go to the expected endpoint
         - The correct query parameters are sent, if important (esp. for limiting ones)
         - The number of network requests is as expected (don't DOS a service due to a bug ^^)
         - All Overpass queries contain the expected tag filters
        """
        dummy_area_id: Final = 1337
        expected_network_request_count: Final = 4  # 1x Nomination + 2x Overpass

        retrieve_json_resource_side_effects = [
            json.dumps([{"osm_id": dummy_area_id}]),  # Nominatim response
            json.dumps(
                # Response of the Overpass area query
                {
                    "elements": [
                        {
                            "id": 42,
                            "type": "relation",
                            "tags": {"natural": "peak", "name": "Mt Mock"},
                            "members": [{"type": "node", "ref": 43}],
                        },
                    ]
                },
            ),
            json.dumps(
                # Response of the Overpass parent relations ID query
                {
                    "elements": [
                        {
                            "id": 123,
                            "type": "relation",
                            "tags": {"name": "Mock Area"},
                            "members": [{"type": "relation", "ref": 42}],
                        },
                    ]
                },
            ),
            json.dumps(
                # Response of the Overpass node ID query
                {
                    "elements": [
                        {
                            "id": 43,
                            "type": "node",
                            "lat": 13.37,
                            "lon": 47.11,
                            "tags": {"natural": "peak", "name": "Mt Mock"},
                        },
                    ]
                },
            ),
        ]

        mocked_network_boundary = Mock(HttpNetworkingBoundary)
        mocked_network_boundary.retrieve_json_resource.side_effect = (
            retrieve_json_resource_side_effects
        )

        osm_filter = OsmDataFilter(mocked_network_boundary)
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=Mock(Pipe))

        expected_nominatim_endpoint: Final = "https://nominatim.openstreetmap.org/search"
        expected_overpass_endpoint: Final = "https://overpass-api.de/api/interpreter"
        expected_nominatim_search_string: Final = "Sächsische Schweiz"

        # Check the total number of network requests
        assert (
            mocked_network_boundary.retrieve_json_resource.call_count
            == expected_network_request_count
        )
        # Check the Nominatim request parameters: Request the correct area and limit the result
        # count to one
        mocked_network_boundary.retrieve_json_resource.assert_any_call(
            url=expected_nominatim_endpoint,
            url_params={"q": expected_nominatim_search_string, "limit": 1, "format": "jsonv2"},
        )

        # Check the Overpass requests

        # 1. Overpass area query
        area_query = mocked_network_boundary.retrieve_json_resource.call_args_list[1]

        # The query must have been sent to the expected endpoint
        assert area_query.kwargs["url"] == expected_overpass_endpoint

        area_query_content = area_query.kwargs["query_content"]
        # The body must start with "data="
        assert area_query_content.startswith("data=")
        # The query must request the area ID provided by Nominatim
        assert f"area({dummy_area_id})->.searchArea;" in area_query_content
        # The query must contain the requested element types
        assert "node" in area_query_content
        assert "relation" in area_query_content
        # The query must contain the necessary tag filters
        assert '["natural"="peak"]' in area_query_content
        assert '["type"="site"]' in area_query_content
        assert '["climbing:trad"="yes"]' in area_query_content
        assert '["sport"="climbing"]' in area_query_content

        # 2. Overpass parent relation query
        parent_query = mocked_network_boundary.retrieve_json_resource.call_args_list[2]

        # The query must have been sent to the expected endpoint
        assert parent_query.kwargs["url"] == expected_overpass_endpoint

        parent_query_content = parent_query.kwargs["query_content"]
        # The body must start with "data="
        assert parent_query_content.startswith("data=")
        # The query must contain the requested element type
        assert "node" in parent_query_content
        assert "relation" in parent_query_content
        # The query must contain the necessary tag filters
        assert '["climbing"="area"]' in parent_query_content
        assert '["type"="site"]' in parent_query_content

        # 3. Overpass node ID query
        id_query = mocked_network_boundary.retrieve_json_resource.call_args_list[3]

        # The query must have been sent to the expected endpoint
        assert id_query.kwargs["url"] == expected_overpass_endpoint

        id_query_content = id_query.kwargs["query_content"]
        # The body must start with "data="
        assert id_query_content.startswith("data=")
        # The query must contain the requested element type
        assert "node" in id_query_content
