"""
Unit tests for the 'trad.application.filters.source.osm.filter' module (and therefore, most of the
'trad.application.filters.source.osm' package).
"""

from _collections_abc import Mapping
from typing import Final
from unittest.mock import Mock

import pytest

from trad.application.filters.source.osm.filter import OsmDataFilter
from trad.application.filters.source.route_data_factory import RouteDataFactory
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.routedata import Route

from .fake_network import FakeNetwork

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
        fake_network_boundary = FakeNetwork(
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

        fake_network_boundary = FakeNetwork(
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
