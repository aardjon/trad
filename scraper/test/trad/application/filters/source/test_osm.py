"""
Unit tests for the 'trad.application.filters.source.osm' module.
"""

import json
from typing import Final, override
from unittest.mock import Mock

import pytest

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError, JsonData
from trad.application.filters.source.osm import OsmSummitDataFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.routedata import Summit
from trad.kernel.errors import DataProcessingError, DataRetrievalError


class TestOsmSummitDataFilter:
    def test_name(self) -> None:
        """
        Ensures the filter name to be correct.
        """
        osm_filter = OsmSummitDataFilter(Mock(HttpNetworkingBoundary))
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
    ) -> None:
        """
        Ensures the correct behaviour in case of errors during the Nominatim request.
        """
        mocked_network_boundary = Mock(HttpNetworkingBoundary)
        mocked_network_boundary.retrieve_json_resource.side_effect = [nominatim_response]
        osm_filter = OsmSummitDataFilter(mocked_network_boundary)

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
        osm_filter = OsmSummitDataFilter(mocked_network_boundary)

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
                            "tags": {"name": "Mt Mock"},
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
                            "tags": {"name": "Mt Mock"},
                        },
                    ]
                },
            ),
        ]

        mocked_network_boundary = Mock(HttpNetworkingBoundary)
        mocked_network_boundary.retrieve_json_resource.side_effect = (
            retrieve_json_resource_side_effects
        )

        osm_filter = OsmSummitDataFilter(mocked_network_boundary)
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
        # The query must contain the necessary tag filters
        assert '["natural"="peak"]' in id_query_content

    @pytest.mark.parametrize(
        ("nominatim_response"),
        [
            # Minimal valid Nominatim response data
            [{"osm_id": 1337}],
            # Nominatim response containing additional fields
            [{"copyright": "OSM contributors", "osm_id": 1337}],
        ],
    )
    @pytest.mark.parametrize(
        ("overpass_responses", "expected_summits"),
        [
            (  # Minimal valid response data, no summits at all
                [{"elements": []}],
                [],
            ),
            # Single summit (minimal data)
            (
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
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Mock Area"},
                                "members": [{"type": "node", "ref": 42}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                        sector="Mock Area",
                    )
                ],
            ),
            (
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
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Mock Area"},
                                "members": [{"type": "node", "ref": 42}],
                            },
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
                        "Mt Mock",
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                        sector="Mock Area",
                    )
                ],
            ),
            (  # Relation summit for which the referenced node is already available
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
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Mock Area"},
                                "members": [{"type": "node", "ref": 42}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                        sector="Mock Area",
                    )
                ],
            ),
            (  # Single summit with additional data
                [
                    {
                        "elements": [
                            {
                                "type": "node",
                                "lat": 13.37,
                                "lon": 47.11,
                                "id": 42,
                                "user": "nobody",
                                "tags": {
                                    "name": "Mt Mock",
                                    "climbing:summit_log": "yes",
                                    "some_other_tag": "value",
                                },
                            }
                        ],
                        "osm3s": {"copyright": "OSM constributors"},
                    },
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Mock Area"},
                                "members": [{"type": "node", "ref": 42}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                        sector="Mock Area",
                    )
                ],
            ),
            (  # Multiple summits
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
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Zahlengebiet"},
                                "members": [{"type": "node", "ref": i} for i in range(1, 4)],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Einserspitze",
                        high_grade_position=GeoPosition.from_decimal_degree(12.34, 9.87),
                        sector="Zahlengebiet",
                    ),
                    Summit(
                        "Zweierturm",
                        high_grade_position=GeoPosition.from_decimal_degree(56.78, 65.43),
                        sector="Zahlengebiet",
                    ),
                    Summit(
                        "Dreierwand",
                        high_grade_position=GeoPosition.from_decimal_degree(90.00, 21.10),
                        sector="Zahlengebiet",
                    ),
                ],
            ),
            # Summits with multiple names (in different variants)
            (
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
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Mock Area"},
                                "members": [{"type": "node", "ref": 11}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt", "official", "nick", "short", "loc"],
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                        sector="Mock Area",
                    )
                ],
            ),
            (
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
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Mock Area"},
                                "members": [{"type": "node", "ref": 22}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt1", "alt2", "alt3"],
                        high_grade_position=GeoPosition.from_decimal_degree(13.37, 47.11),
                        sector="Mock Area",
                    )
                ],
            ),
        ],
    )
    def test_normal_execution(
        self,
        nominatim_response: list[dict[str, object]],
        overpass_responses: list[dict[str, object]],
        expected_summits: list[Summit],
    ) -> None:
        """
        Ensure the correct behaviour if no errors occur:
         - The correct number of summits is sent to the Pipe
         - The Summit data is correctly parsed and forwarded
         - It must work with nodes, with relations, and both
         - Everything must still work if the Nominatim response contains additional (ignored) data
        """
        fake_network_boundary = _FakeNetwork(
            nominatim_response,
            *overpass_responses,
        )
        osm_filter = OsmSummitDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        # Make sure that the expected number of summits has been sent to the Pipe
        actual_summits = list(output_pipe.iter_summits())
        assert len(actual_summits) == len(expected_summits)

        # Make sure all imported summits match our expectation
        stored_summits: list[Summit] = sorted(
            (summit for _id, summit in actual_summits),
            key=lambda s: s.name,
        )
        assert all(
            self._summits_equal(s1, s2)
            for s1, s2 in zip(
                sorted(expected_summits, key=lambda s: s.name),
                stored_summits,
                strict=True,
            )
        )

    @pytest.mark.parametrize("access_tag", ["no", "private"])
    def test_ignore_inaccessible_summits(self, access_tag: str) -> None:
        """
        Ensure that peak nodes that are not accessible at all are not imported.

        Note: We currently don't expect totally forbidden peaks to be a relation, because they won't
        have any routes or other infrastructure that needs to be grouped. That's why checking for
        forbidden "relation peaks" is not tested.
        """
        json_peak_node = {
            "id": 22,
            "type": "node",
            "lat": 13.37,
            "lon": 47.11,
            "tags": {"name": "Mock Summit", "access": access_tag},
        }
        json_parent_relation = {
            "id": 32,
            "type": "relation",
            "tags": {"name": "Mock Area"},
            "members": [{"type": "node", "ref": 22}],
        }

        fake_network_boundary = _FakeNetwork(
            nominatim_response=[{"osm_id": 1337}],
            overpass_area_query_response={"elements": [json_peak_node]},
            overpass_parent_relations_query_response={"elements": [json_parent_relation]},
        )
        osm_filter = OsmSummitDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        imported_summits = [s for _id, s in output_pipe.iter_summits()]
        assert not imported_summits

    @pytest.mark.parametrize("summit_count", [1, 3, 0])
    def test_external_sources(self, summit_count: int) -> None:
        """
        Ensure that an external source is added along with imported data:
         - The source definition must contain the correct data
         - There must be exactly one source

        :param summit_count: The number of Summits being imported.
        """
        fake_network_boundary = _FakeNetwork(
            nominatim_response=[{"osm_id": 4711}],
            overpass_area_query_response={
                "elements": [
                    {
                        "id": i,
                        "type": "node",
                        "lat": 13.37,
                        "lon": 47.11,
                        "tags": {
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
        osm_filter = OsmSummitDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        # The resulting Pipe must contain exactly one external source definition
        actual_sources = list(output_pipe.get_sources())
        assert len(actual_sources) == 1
        assert actual_sources[0].label == "OpenStreetMap"
        assert actual_sources[0].url == "https://www.openstreetmap.org"
        assert actual_sources[0].attribution == "OSM Contributors"
        assert actual_sources[0].license_name == "ODbL"

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
            and summit1.sector == summit2.sector
        )


class _FakeNetwork(HttpNetworkingBoundary):
    """
    Fake HTTP networking component to be used by unit test cases.

    Allow to inject certain HTTP query response data.
    """

    def __init__(
        self,
        nominatim_response: list[dict[str, object]],
        overpass_area_query_response: dict[str, object] | None = None,
        overpass_parent_relations_query_response: dict[str, object] | None = None,
        overpass_missing_nodes_query_response: dict[str, object] | None = None,
    ):
        self._nominatim_response = JsonData(json.dumps(nominatim_response))
        self._overpass_responses = [
            JsonData(json.dumps(response)) if response is not None else JsonData("")
            for response in (
                overpass_area_query_response,
                overpass_parent_relations_query_response,
                overpass_missing_nodes_query_response,
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
