"""
Unit tests for the 'trad.infrastructure.filters.osm' module.
"""

import json
from collections.abc import Callable, Iterator
from typing import Final
from unittest.mock import ANY, Mock, NonCallableMock

import pytest

from trad.adapters.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.core.boundaries.filters import FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.core.entities import GeoPosition, Summit
from trad.core.errors import DataProcessingError, DataRetrievalError
from trad.crosscuttings.di import DependencyProvider
from trad.filters.osm import OsmSummitDataFilter


@pytest.fixture
def mocked_network_boundary() -> Iterator[Mock]:
    """
    Provides a mocked HttpNetworkingBoundary component which is also registered at the
    DependencyProvider, and unregisters it after the test execution.
    """
    # Note: Lidi decides whether a given implementation has to be executed (again) or not by
    #     checking callable(), which is always True for normals Mocks. That's why we have to use
    #     NonCallableMock instead.
    mocked_boundary = NonCallableMock(HttpNetworkingBoundary)
    DependencyProvider().register_singleton(HttpNetworkingBoundary, lambda: mocked_boundary)
    yield mocked_boundary
    DependencyProvider().shutdown()


class TestOsmSummitDataFilter:
    @pytest.mark.usefixtures("mocked_network_boundary")
    def test_metadata(self) -> None:
        """
        Ensures the current return values of the "metadata" methods like filter name and filter
        stage.
        """
        assert OsmSummitDataFilter.get_stage() == FilterStage.IMPORTING
        osm_filter = OsmSummitDataFilter(DependencyProvider())
        assert "OpenStreetMap" in osm_filter.get_name()

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
        mocked_network_boundary: Mock,
    ) -> None:
        """
        Ensures the correct behaviour in case of errors during the Nominatim request.
        """
        mocked_network_boundary.retrieve_json_resource.side_effect = [nominatim_response]
        osm_filter = OsmSummitDataFilter(DependencyProvider())

        with pytest.raises(expected_exception):
            osm_filter.execute_filter(pipe=Mock(Pipe))
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
        mocked_network_boundary: Mock,
    ) -> None:
        """
        Ensures the correct behaviour in case of errors during the Overpass request.
        """
        valid_nominatim_response: Final = '[{"osm_id": 42}]'
        expected_network_request_count: Final = 2

        mocked_network_boundary.retrieve_json_resource.side_effect = [
            valid_nominatim_response,
            overpass_response,
        ]
        osm_filter = OsmSummitDataFilter(DependencyProvider())

        with pytest.raises(expected_exception):
            osm_filter.execute_filter(pipe=Mock(Pipe))
        # Make sure there were exactly two network requests in total
        assert (
            mocked_network_boundary.retrieve_json_resource.call_count
            == expected_network_request_count
        )

    @pytest.mark.parametrize(
        ("nominatim_response_factory", "overpass_response", "expected_summits"),
        [
            (  # Minimal valid response data, no summits at all
                lambda area_id: [{"osm_id": area_id}],
                {"elements": []},
                [],
            ),
            (  # Nominatim response contains additional fields
                lambda area_id: [{"copyright": "OSM contributors", "osm_id": area_id}],
                {"elements": []},
                [],
            ),
            (  # Single summit (minimal data)
                lambda area_id: [{"osm_id": area_id}],
                {
                    "elements": [
                        {
                            "id": 42,
                            "type": "node",
                            "lat": 13.37,
                            "lon": 47.11,
                            "tags": {"name": "Mt Mock"},
                        }
                    ]
                },
                [Summit("Mt Mock", position=GeoPosition.from_decimal_degree(13.37, 47.11))],
            ),
            (  # Single summit with additional data
                lambda area_id: [{"osm_id": area_id}],
                {
                    "elements": [
                        {
                            "type": "node",
                            "lat": 13.37,
                            "lon": 47.11,
                            "id": 42,
                            "user": "nobody",
                            "tags": {"name": "Mt Mock", "climbing:summit_log": "yes"},
                        }
                    ],
                    "osm3s": {"copyright": "OSM constributors"},
                },
                [Summit("Mt Mock", position=GeoPosition.from_decimal_degree(13.37, 47.11))],
            ),
            (  # Multiple summits
                lambda area_id: [{"osm_id": area_id}],
                {
                    "elements": [
                        {
                            "id": 1,
                            "type": "node",
                            "lat": 12.34,
                            "lon": 9.87,
                            "tags": {"name": "Einserspitze"},
                        },
                        {
                            "id": 2,
                            "type": "node",
                            "lat": 56.78,
                            "lon": 65.43,
                            "tags": {"name": "Zweierturm"},
                        },
                        {
                            "id": 3,
                            "type": "node",
                            "lat": 90.00,
                            "lon": 21.10,
                            "tags": {"name": "Dreierwand"},
                        },
                    ]
                },
                [
                    Summit("Einserspitze", position=GeoPosition.from_decimal_degree(12.34, 9.87)),
                    Summit("Zweierturm", position=GeoPosition.from_decimal_degree(56.78, 65.43)),
                    Summit("Dreierwand", position=GeoPosition.from_decimal_degree(90.00, 21.10)),
                ],
            ),
            # Summits with multiple names (in different variants)
            (
                lambda area_id: [{"osm_id": area_id}],
                {
                    "elements": [
                        {
                            "id": 11,
                            "type": "node",
                            "lat": 13.37,
                            "lon": 47.11,
                            "tags": {
                                "name": "name",
                                "alt_name": "alt",
                                "official_name": "official",
                                "nickname": "nick",
                                "short_name": "short",
                                "loc_name": "loc",
                            },
                        },
                    ]
                },
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt", "official", "nick", "short", "loc"],
                        position=GeoPosition.from_decimal_degree(13.37, 47.11),
                    )
                ],
            ),
            (
                lambda area_id: [{"osm_id": area_id}],
                {
                    "elements": [
                        {
                            "id": 22,
                            "type": "node",
                            "lat": 13.37,
                            "lon": 47.11,
                            "tags": {
                                "name": "name",
                                "alt_name": "alt1; alt2 ; alt3",
                            },
                        },
                    ]
                },
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt1", "alt2", "alt3"],
                        position=GeoPosition.from_decimal_degree(13.37, 47.11),
                    )
                ],
            ),
        ],
    )
    def test_normal_execution(
        self,
        nominatim_response_factory: Callable[[int], list[dict[str, object]]],
        overpass_response: dict[str, object],
        expected_summits: list[Summit],
        mocked_network_boundary: Mock,
    ) -> None:
        """
        Ensure the correct bevahiour if no errors occur:
         - All network boundary calls get the expected parameters
         - The correct number of summits is sent to the Pipe
         - The Summit data is correctly parsed and forwarded
        """
        dummy_area_id: Final = 1337
        expected_network_request_count: Final = 2

        mocked_pipe = Mock(Pipe)
        mocked_network_boundary.retrieve_json_resource.side_effect = [
            json.dumps(nominatim_response_factory(dummy_area_id)),  # Nominatim response
            json.dumps(overpass_response),  # Overpass response
        ]

        osm_filter = OsmSummitDataFilter(DependencyProvider())
        osm_filter.execute_filter(pipe=mocked_pipe)

        # Check the number of network requests
        assert (
            mocked_network_boundary.retrieve_json_resource.call_count
            == expected_network_request_count
        )
        # Check the Nominatim request parameters
        mocked_network_boundary.retrieve_json_resource.assert_any_call(
            url="https://nominatim.openstreetmap.org/search",
            url_params={"q": "Sächsische Schweiz", "limit": 1, "format": "jsonv2"},
        )
        # Check the Overpass request parameters (this was the most recent request)
        mocked_network_boundary.retrieve_json_resource.assert_called_with(
            url="https://overpass-api.de/api/interpreter",
            url_params={},
            query_content=ANY,
        )
        # Do some checks on the query content (i.e. the OverpassQL string):
        actual_query_content = mocked_network_boundary.retrieve_json_resource.call_args_list[
            -1
        ].kwargs["query_content"]
        # The body must start with "data="
        assert actual_query_content.startswith("data=")
        # The query must request the area ID provided by Nominatim
        assert f"area({dummy_area_id})->.searchArea;" in actual_query_content
        # The query must contain the necessary tag filters
        assert '["natural"="peak"]' in actual_query_content
        assert '["climbing:trad"="yes"]' in actual_query_content

        # Make sure that the expected number of summits has been sent to the Pipe
        assert mocked_pipe.add_or_enrich_summit.call_count == len(expected_summits)
        # Make sure all sent summit data matches our expectation
        stored_summits: list[Summit] = sorted(
            (call.args[0] for call in mocked_pipe.add_or_enrich_summit.call_args_list),
            key=lambda s: s.name,
        )
        assert all(
            self._summits_equal(s1, s2)
            for s1, s2 in zip(
                sorted(expected_summits, key=lambda s: s.name), stored_summits, strict=True
            )
        )

    @staticmethod
    def _summits_equal(summit1: Summit, summit2: Summit) -> bool:
        """
        Returns True if the given summits are equal (by value), otherwise False.
        This compares by value, i.e. two different instances with the same values are equal.
        """
        return (
            summit1.official_name == summit2.official_name
            and sorted(summit1.alternate_names) == sorted(summit2.alternate_names)
            and sorted(summit1.unspecified_names) == sorted(summit2.unspecified_names)
            and summit1.position.latitude_int == summit2.position.latitude_int
            and summit1.position.longitude_int == summit2.position.longitude_int
        )
