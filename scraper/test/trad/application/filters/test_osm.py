"""
Unit tests for the 'trad.application.filters.osm' module.
"""

import json
from collections.abc import Callable, Iterator
from typing import Final
from unittest.mock import ANY, Mock, NonCallableMock

import pytest

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.application.filters.osm import OsmSummitDataFilter
from trad.kernel.boundaries.filters import FilterStage
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.di import DependencyProvider
from trad.kernel.entities import GeoPosition, Summit
from trad.kernel.errors import DataProcessingError, DataRetrievalError


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
        ("nominatim_response_factory", "overpass_responses", "expected_summits"),
        [
            (  # Minimal valid response data, no summits at all
                lambda area_id: [{"osm_id": area_id}],
                [{"elements": []}],
                [],
            ),
            (  # Nominatim response contains additional fields
                lambda area_id: [{"copyright": "OSM contributors", "osm_id": area_id}],
                [{"elements": []}],
                [],
            ),
            # Single summit (minimal data)
            (
                lambda area_id: [{"osm_id": area_id}],
                [
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
                ],
                [
                    Summit(
                        "Mt Mock", high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11)
                    )
                ],
            ),
            (
                lambda area_id: [{"osm_id": area_id}],
                [
                    {
                        "elements": [
                            {
                                "id": 42,
                                "type": "relation",
                                "tags": {"name": "Mt Mock"},
                                "members": [{"type": "node", "ref": 1}],
                            }
                        ]
                    },
                    {
                        "elements": [
                            {
                                "id": 1,
                                "type": "node",
                                "lat": 13.37,
                                "lon": 47.11,
                                "tags": {"name": "Mt Mock"},
                            }
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock", high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11)
                    )
                ],
            ),
            (  # Relation summit for which the referenced node is already available
                lambda area_id: [{"osm_id": area_id}],
                [
                    {
                        "elements": [
                            {
                                "id": 42,
                                "type": "relation",
                                "tags": {"name": "Mt Mock"},
                                "members": [{"type": "node", "ref": 43}],
                            },
                            {
                                "id": 43,
                                "type": "node",
                                "lat": 13.37,
                                "lon": 47.11,
                                "tags": {"name": "Mt Mock"},
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock", high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11)
                    )
                ],
            ),
            (  # Single summit with additional data
                lambda area_id: [{"osm_id": area_id}],
                [
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
                ],
                [
                    Summit(
                        "Mt Mock", high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11)
                    )
                ],
            ),
            (  # Multiple summits
                lambda area_id: [{"osm_id": area_id}],
                [
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
                ],
                [
                    Summit(
                        "Einserspitze",
                        high_grade_position=GeoPosition.from_decimal_degree(12.34, 9.87),
                    ),
                    Summit(
                        "Zweierturm",
                        high_grade_position=GeoPosition.from_decimal_degree(56.78, 65.43),
                    ),
                    Summit(
                        "Dreierwand",
                        high_grade_position=GeoPosition.from_decimal_degree(90.00, 21.10),
                    ),
                ],
            ),
            # Summits with multiple names (in different variants)
            (
                lambda area_id: [{"osm_id": area_id}],
                [
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
                ],
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt", "official", "nick", "short", "loc"],
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                    )
                ],
            ),
            (
                lambda area_id: [{"osm_id": area_id}],
                [
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
                ],
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt1", "alt2", "alt3"],
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                    )
                ],
            ),
        ],
    )
    def test_normal_execution(
        self,
        nominatim_response_factory: Callable[[int], list[dict[str, object]]],
        overpass_responses: list[dict[str, object]],
        expected_summits: list[Summit],
        mocked_network_boundary: Mock,
    ) -> None:
        """
        Ensure the correct behaviour if no errors occur:
         - All network boundary calls get the expected parameters
         - The correct number of summits is sent to the Pipe
         - The Summit data is correctly parsed and forwarded
         - It must work with nodes, with relations, and both
        """
        dummy_area_id: Final = 1337
        expected_network_request_count: Final = len(overpass_responses) + 1

        mocked_pipe = Mock(Pipe)
        retrieve_json_resource_side_effects = [
            json.dumps(nominatim_response_factory(dummy_area_id)),  # Nominatim response
            json.dumps(overpass_responses[0]),  # Response of the Overpass area query
        ]
        if len(overpass_responses) > 1:
            # Response of the Overpass node ID query, if any
            retrieve_json_resource_side_effects.append(json.dumps(overpass_responses[1]))
        mocked_network_boundary.retrieve_json_resource.side_effect = (
            retrieve_json_resource_side_effects
        )

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
        # Check the Overpass requests parameters
        mocked_network_boundary.retrieve_json_resource.assert_called_with(
            url="https://overpass-api.de/api/interpreter",
            url_params={},
            query_content=ANY,
        )

        # Do some checks on the query contents (i.e. the OverpassQL strings)
        area_query_content = mocked_network_boundary.retrieve_json_resource.call_args_list[
            1
        ].kwargs["query_content"]
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

        if len(overpass_responses) > 1:
            id_query_content = mocked_network_boundary.retrieve_json_resource.call_args_list[
                2
            ].kwargs["query_content"]
            # The body must start with "data="
            assert id_query_content.startswith("data=")
            # The query must contain the requested element type
            assert "node" in id_query_content
            # The query must contain the necessary tag filters
            assert '["natural"="peak"]' in id_query_content

        # Make sure that the expected number of summits has been sent to the Pipe
        assert mocked_pipe.add_summit.call_count == len(expected_summits)
        # Make sure all sent summit data matches our expectation
        stored_summits: list[Summit] = sorted(
            (call.args[0] for call in mocked_pipe.add_summit.call_args_list),
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
            and summit1.high_grade_position.is_equal_to(summit2.high_grade_position)
            and summit1.low_grade_position.is_equal_to(summit2.low_grade_position)
        )
