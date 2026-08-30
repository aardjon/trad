"""
Unit tests for the 'trad.application.filters.source.osm.filter' module (and therefore, most of the
'trad.application.filters.source.osm' package).
"""

from typing import Final
from unittest.mock import Mock

import pytest

from trad.application.filters.source.osm.filter import OsmDataFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import Summit

from .fake_network import FakeNetwork


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
        fake_network_boundary = FakeNetwork(
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

        fake_network_boundary = FakeNetwork(
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
