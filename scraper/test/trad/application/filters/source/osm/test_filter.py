"""
Unit tests for the 'trad.application.filters.source.osm.filter' module (and therefore, most of the
'trad.application.filters.source.osm' package).
"""

import json
from collections.abc import Mapping, Sequence
from typing import Final, override
from unittest.mock import Mock

import pytest

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError, JsonData
from trad.application.filters.source.osm.filter import OsmDataFilter
from trad.application.filters.source.route_data_factory import RouteDataFactory
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import Route, Summit
from trad.kernel.errors import DataProcessingError, DataRetrievalError

_data_factory = RouteDataFactory(
    source_label="OpenStreetMap",
    summit_sector_rank=1,
    summit_position_rank=1,
    route_grade_conflict_rank=5,
    route_entry_position_rank=1,
)
"""
Data factory for creating the expected entity objects. The label and rank values are what we expect
from the OSM filter (they are always the same), so they is ensured implicitly with all test cases.
"""


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


class TestOsmDataFilterSummits:
    """
    Summit related test cases for the OsmDataFilter class.
    """

    _expected_sector_rank: Final = 1
    """
    The expected rank of the summit.sector attribute.
    """

    _expected_position_rank: Final = 1
    """
    The expected rank of the summit.position attribute.
    """

    # Some example sector value as expected to be created by the OSM filter.
    _example_sector1: Final = RankedValue[str].create_valid("Mock Area", _expected_sector_rank)
    _example_sector2: Final = RankedValue[str].create_valid("Zahlengebiet", _expected_sector_rank)

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
                                "tags": {"name": "Mt Mock", "natural": "peak"},
                            }
                        ]
                    },
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": _example_sector1.value},
                                "members": [{"type": "node", "ref": 42}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(13.37, 47.11),
                            _expected_position_rank,
                        ),
                        sector=_example_sector1,
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
                                "tags": {"name": _example_sector1.value},
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
                                "tags": {"name": "Mt Mock", "natural": "peak"},
                            }
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(13.37, 47.11),
                            _expected_position_rank,
                        ),
                        sector=_example_sector1,
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
                                "tags": {"name": "Mt Mock", "natural": "peak"},
                            },
                        ]
                    },
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": _example_sector1.value},
                                "members": [{"type": "node", "ref": 42}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(13.37, 47.11),
                            _expected_position_rank,
                        ),
                        sector=_example_sector1,
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
                                    "natural": "peak",
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
                                "tags": {"name": _example_sector1.value},
                                "members": [{"type": "node", "ref": 42}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Mt Mock",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(13.37, 47.11),
                            _expected_position_rank,
                        ),
                        sector=_example_sector1,
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
                                "tags": {"name": "Einserspitze", "natural": "peak"},
                            },
                            {
                                "id": 2,
                                "type": "node",
                                "lat": 56.78,
                                "lon": 65.43,
                                "tags": {"name": "Zweierturm", "natural": "peak"},
                            },
                            {
                                "id": 3,
                                "type": "node",
                                "lat": 90.00,
                                "lon": 21.10,
                                "tags": {"name": "Dreierwand", "natural": "peak"},
                            },
                        ]
                    },
                    {
                        "elements": [
                            {
                                "id": 123,
                                "type": "relation",
                                "tags": {"name": "Zahlengebiet", "natural": "peak"},
                                "members": [{"type": "node", "ref": i} for i in range(1, 4)],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        "Einserspitze",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(12.34, 9.87), _expected_position_rank
                        ),
                        sector=_example_sector2,
                    ),
                    Summit(
                        "Zweierturm",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(56.78, 65.43), _expected_position_rank
                        ),
                        sector=_example_sector2,
                    ),
                    Summit(
                        "Dreierwand",
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(90.00, 21.10), _expected_position_rank
                        ),
                        sector=_example_sector2,
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
                                    "natural": "peak",
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
                                "tags": {"name": _example_sector1.value},
                                "members": [{"type": "node", "ref": 11}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt", "official", "nick", "short", "loc"],
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(13.37, 47.11),
                            _expected_position_rank,
                        ),
                        sector=_example_sector1,
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
                                    "natural": "peak",
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
                                "tags": {"name": _example_sector1.value, "natural": "peak"},
                                "members": [{"type": "node", "ref": 22}],
                            },
                        ]
                    },
                ],
                [
                    Summit(
                        official_name="name",
                        alternate_names=["alt1", "alt2", "alt3"],
                        position=RankedValue.create_valid(
                            GeoPosition.from_decimal_degree(13.37, 47.11),
                            _expected_position_rank,
                        ),
                        sector=_example_sector1,
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
        osm_filter = OsmDataFilter(fake_network_boundary)

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
            "tags": {"natural": "peak", "name": "Mock Summit", "access": access_tag},
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
        osm_filter = OsmDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        imported_summits = [s for _id, s in output_pipe.iter_summits()]
        assert not imported_summits

    @staticmethod
    def _summits_equal(summit1: Summit, summit2: Summit) -> bool:
        """
        Returns True if the given summits are equal (by value), otherwise False.
        This compares by value, i.e. two different instances with the same values are equal.
        """
        ret_val = (
            summit1.official_name == summit2.official_name
            and sorted(summit1.alternate_names) == sorted(summit2.alternate_names)
            and sorted(summit1.unspecified_names) == sorted(summit2.unspecified_names)
            and summit1.sector == summit2.sector
        )
        if ret_val:
            if summit1.position.is_null() == summit2.position.is_null():
                ret_val = True
            else:
                ret_val = summit1.position.value.is_equal_to(summit2.position.value)
        return ret_val


class TestOsmDataFilterRoutes:
    """
    Route related test casess for the OsmDataFilter class.
    """

    _NOMINATIM_RESPONSE: Final = [{"osm_id": 4711}]

    _OVERPASS_SECTOR_RESPONSE: Final = {
        "elements": [
            {
                "id": 987,
                "type": "relation",
                "tags": {"name": "Dummy Sector"},
                "members": [{"type": "relation", "ref": 13}],
            },
        ]
    }

    def _create_overpass_element_responses(
        self,
        relation_members: list[dict[str, object]],
    ) -> list[Mapping[str, object]]:
        """
        Creates the Overpass JSON responses for the given relation members.

        The created responses define a single peak relation (ID: 1000) with a single peak node
        (ID: 1001) and all members given by `relation_members`.
        """
        summit_name: Final = "Dummy Rock with Routes"
        relation_members.append(
            {
                "id": 1001,
                "type": "node",
                "lat": 13.5372854,
                "lon": 50.8254129,
                "tags": {
                    "natural": "peak",
                    "name": summit_name,
                },
            },
        )
        member_refs = [{"type": m["type"], "ref": m["id"]} for m in relation_members]

        return [
            {
                "elements": [
                    {  # relation defining a single summit
                        "id": 1000,
                        "type": "relation",
                        "tags": {"name": summit_name},
                        "members": member_refs,
                    },
                ]
            },
            self._OVERPASS_SECTOR_RESPONSE,
            {"elements": relation_members},
        ]

    @pytest.mark.parametrize(
        ("relation_members", "expected_routes"),
        [
            pytest.param([], [], id="Relation without any routes"),
            pytest.param(
                [
                    {
                        "id": 1,
                        "type": "node",
                        "lat": 13.53728,
                        "lon": 50.82542,
                        "tags": {
                            "climbing": "route",
                            "name": "Rocky Road",
                        },
                    },
                ],
                [
                    _data_factory.create_route(
                        route_name="Rocky Road",
                        entry_position=GeoPosition.from_decimal_degree(13.53728, 50.82542),
                    )
                ],
                id="Single route, minimal data",
            ),
            pytest.param(
                [
                    {
                        "id": 1,
                        "type": "node",
                        "lat": 13.53728,
                        "lon": 50.82542,
                        "tags": {
                            "climbing": "route_bottom",
                            "name": "Rocky Road",
                        },
                    },
                ],
                [
                    _data_factory.create_route(
                        route_name="Rocky Road",
                        entry_position=GeoPosition.from_decimal_degree(13.53728, 50.82542),
                    )
                ],
                id="Single route_bottom, minimal data",
            ),
            pytest.param(
                [
                    {
                        "id": 1,
                        "type": "node",
                        "lat": 13.53728,
                        "lon": 50.82542,
                        "tags": {
                            "climbing": "route",
                            "name": "Extended Route",
                            "climbing:dummy_tag": "ignore",
                            "climbing:grade:french": "5a",
                        },
                    },
                ],
                [
                    _data_factory.create_route(
                        route_name="Extended Route",
                        entry_position=GeoPosition.from_decimal_degree(13.53728, 50.82542),
                    )
                ],
                id="Ignore additional route data",
            ),
            pytest.param(
                [
                    {
                        "id": 1,
                        "type": "node",
                        "lat": 13.53728,
                        "lon": 50.82542,
                        "tags": {
                            "climbing:bolt": "abseil",
                        },
                    },
                    {
                        "id": 2,
                        "type": "node",
                        "lat": 13.53728,
                        "lon": 50.82542,
                        "tags": {
                            "climbing": "route",
                            "name": "Extended Route",
                        },
                    },
                ],
                [
                    _data_factory.create_route(
                        route_name="Extended Route",
                        entry_position=GeoPosition.from_decimal_degree(13.53728, 50.82542),
                    )
                ],
                id="Ignore non-route members",
            ),
            pytest.param(
                [
                    {
                        "id": 1,
                        "type": "node",
                        "lat": 13.53728,
                        "lon": 50.82542,
                        "tags": {
                            "climbing": "route",
                            "name": "Route 1",
                        },
                    },
                    {
                        "id": 2,
                        "type": "node",
                        "lat": 13.53782,
                        "lon": 50.82554,
                        "tags": {
                            "climbing": "route_bottom",
                            "name": "Route 2",
                        },
                    },
                    {
                        "id": 3,
                        "type": "node",
                        "lat": 13.53738,
                        "lon": 50.82512,
                        "tags": {
                            "climbing": "route",
                            "name": "Route 3",
                        },
                    },
                ],
                [
                    _data_factory.create_route(
                        route_name="Route 1",
                        entry_position=GeoPosition.from_decimal_degree(13.53728, 50.82542),
                    ),
                    _data_factory.create_route(
                        route_name="Route 2",
                        entry_position=GeoPosition.from_decimal_degree(13.53782, 50.82554),
                    ),
                    _data_factory.create_route(
                        route_name="Route 3",
                        entry_position=GeoPosition.from_decimal_degree(13.53738, 50.82512),
                    ),
                ],
                id="Multiple routes",
            ),
        ],
    )
    def test_normal_execution_single_summit(
        self,
        relation_members: list[dict[str, object]],
        expected_routes: list[Route],
    ) -> None:
        """
        Ensure the correct behaviour if no errors occur:
         - The correct number of routes is sent to the Pipe
         - All Route data is correctly parsed and forwarded
         - It works with both 'route' and 'route_bottom' nodes
         - Additional, unused route data is simply ignored
         - There may be relations without any routes at all

        These test cases always import exactly one summit with different route data. Summit
        processing is tested by `TestOsmDataFilterSummits` already, so there's no need for any
        summit related validation here.
        """
        fake_network_boundary = _FakeNetwork(
            self._NOMINATIM_RESPONSE,
            *self._create_overpass_element_responses(relation_members),
        )
        osm_filter = OsmDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        summit_id, _ = next(output_pipe.iter_summits())

        # Make sure that the expected number of routes has been sent to the Pipe
        actual_routes = list(output_pipe.iter_routes_of_summit(summit_id))
        assert len(actual_routes) == len(expected_routes)

        # Make sure all imported routes match our expectation
        stored_routes: list[Route] = sorted(
            (route for _id, route in actual_routes),
            key=lambda r: r.route_name,
        )
        assert all(
            self._routes_equal(r1, r2)
            for r1, r2 in zip(
                sorted(expected_routes, key=lambda r: r.route_name),
                stored_routes,
                strict=True,
            )
        )

    def test_normal_execution_multiple_summits(self) -> None:
        """
        Make sure importing also works for routes on multiple summits:
         - All routes must be imported
         - Routes between summits must not be mixed up

        Here we have exactly two summits with two/three routes.

        - Don't mix routes of different summits --> separate test case
        - Relation summit with a full-data peak --> separate test case
            - node is not retrieved again
            - data of the relation is used
        """
        # The input route nodes and the expected output Route data
        summit1_route_data: Final = [
            {
                "id": 1,
                "type": "node",
                "lat": 13.53738,
                "lon": 50.82512,
                "tags": {
                    "climbing": "route",
                    "name": "S1R1",
                },
            },
            {
                "id": 2,
                "type": "node",
                "lat": 13.53737,
                "lon": 50.82513,
                "tags": {
                    "climbing": "route",
                    "name": "S1R2",
                },
            },
        ]
        expected_summit1_routes: Final = [
            _data_factory.create_route(
                "S1R1", entry_position=GeoPosition.from_decimal_degree(13.53738, 50.82512)
            ),
            _data_factory.create_route(
                "S1R2", entry_position=GeoPosition.from_decimal_degree(13.53737, 50.82513)
            ),
        ]

        summit2_route_data: Final = [
            {
                "id": 3,
                "type": "node",
                "lat": 13.3826541,
                "lon": 50.7427859,
                "tags": {
                    "climbing": "route",
                    "name": "S2R1",
                },
            },
            {
                "id": 4,
                "type": "node",
                "lat": 13.3826542,
                "lon": 50.7427858,
                "tags": {
                    "climbing": "route",
                    "name": "S2R2",
                },
            },
            {
                "id": 5,
                "type": "node",
                "lat": 13.3826543,
                "lon": 50.7427857,
                "tags": {
                    "climbing": "route",
                    "name": "S2R3",
                },
            },
        ]
        expected_summit2_routes: Final = [
            _data_factory.create_route(
                "S2R1", entry_position=GeoPosition.from_decimal_degree(13.3826541, 50.7427859)
            ),
            _data_factory.create_route(
                "S2R2", entry_position=GeoPosition.from_decimal_degree(13.3826542, 50.7427858)
            ),
            _data_factory.create_route(
                "S2R3", entry_position=GeoPosition.from_decimal_degree(13.3826543, 50.7427857)
            ),
        ]

        # Create all Overpass responses
        peak_elements_query_response: Final = {
            "elements": [
                {
                    "id": 1001,
                    "type": "relation",
                    "tags": {"name": "Summit 1"},
                    "members": [
                        {"type": "node", "ref": 7001},  # peak node 1
                        *[{"type": "node", "ref": m["id"]} for m in summit1_route_data],
                    ],
                },
                {
                    "id": 1002,
                    "type": "relation",
                    "tags": {"name": "Summit 2"},
                    "members": [
                        {"type": "node", "ref": 7002},  # peak node 2
                        *[{"type": "node", "ref": m["id"]} for m in summit2_route_data],
                    ],
                },
            ]
        }

        relation_members_query_response: Final = {
            "elements": [
                *summit1_route_data,
                {
                    "id": 7001,
                    "type": "node",
                    "lat": 13.5372854,
                    "lon": 50.8254129,
                    "tags": {
                        "natural": "peak",
                        "name": "Summit 1",
                    },
                },
                *summit2_route_data,
                {
                    "id": 7002,
                    "type": "node",
                    "lat": 13.3826541,
                    "lon": 50.7427859,
                    "tags": {
                        "natural": "peak",
                        "name": "Summit 2",
                    },
                },
            ]
        }

        # Mapping for checking the correct routes against the correct summit
        summit_name_to_routes_mapping = {
            "Summit 1": expected_summit1_routes,
            "Summit 2": expected_summit2_routes,
        }

        fake_network_boundary = _FakeNetwork(
            self._NOMINATIM_RESPONSE,
            peak_elements_query_response,
            self._OVERPASS_SECTOR_RESPONSE,
            relation_members_query_response,
        )
        osm_filter = OsmDataFilter(fake_network_boundary)

        output_pipe = CollectedData()
        osm_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

        for summit_id, summit in output_pipe.iter_summits():
            actual_routes = list(output_pipe.iter_routes_of_summit(summit_id))
            expected_routes = summit_name_to_routes_mapping[summit.name]

            # Make sure all imported routes match our expectation
            stored_routes: list[Route] = sorted(
                (route for _id, route in actual_routes),
                key=lambda r: r.route_name,
            )
            assert all(
                self._routes_equal(r1, r2)
                for r1, r2 in zip(
                    sorted(expected_routes, key=lambda r: r.route_name),
                    stored_routes,
                    strict=True,
                )
            )

    def _routes_equal(self, route1: Route, route2: Route) -> bool:
        """
        Returns True if the given routes are equal, otherwise False.
        This compares by value, i.e. two different instances with the same values are equal.
        """
        ret_val = (
            route1.route_name == route2.route_name
            and route1.conflict_rank == route2.conflict_rank
            and route1.grade_af == route2.grade_af
            and route1.grade_rp == route2.grade_rp
            and route1.grade_ou == route2.grade_ou
            and route1.grade_jump == route2.grade_jump
            and route1.star_count == route2.star_count
            and route1.dangerous == route2.dangerous
            and route1.directions == route2.directions
        )

        if ret_val:
            if route1.entry_position.is_null() == route2.entry_position.is_null():
                ret_val = True
            else:
                ret_val = route1.entry_position.value.is_equal_to(route2.entry_position.value)
        return ret_val


class _FakeNetwork(HttpNetworkingBoundary):
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
