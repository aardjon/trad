"""
Unit tests for the trad.application.filters.regular.merge module.
"""

from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from typing import Final

import pytest

from trad.application.filters.regular.merge import (
    MergeFilter,
    _RouteMerger,
    _RouteRelatedData,
    _SummitMerger,
)
from trad.application.pipes import CollectedData
from trad.kernel.entities import GeoPosition, Post, Route, Summit
from trad.kernel.errors import MergeConflictError


class TestMergeFilter:
    """
    Unit tests for the MergeFilter class.
    """

    @pytest.mark.parametrize(
        ("existing_summits", "add_summit", "expected_summit_list"),
        [
            # Simple adding of a new summit
            ([], Summit("Summit"), [Summit("Summit")]),
            # Don't create double entries within a list
            (
                [
                    Summit(
                        alternate_names=["Alt1", "Alt2"], unspecified_names=["Unspec1", "Unspec2"]
                    )
                ],
                Summit(alternate_names=["Alt2", "Alt3"], unspecified_names=["Unspec2", "Unspec3"]),
                [
                    Summit(
                        alternate_names=["Alt1", "Alt2", "Alt3"],
                        unspecified_names=["Unspec1", "Unspec2", "Unspec3"],
                    )
                ],
            ),
            # Merge different name variants
            (
                [Summit("Mons Permuta", low_grade_position=GeoPosition(504620000, 147390000))],
                Summit("Permuta, Mons", high_grade_position=GeoPosition(504620000, 147390000)),
                [
                    Summit(
                        "Mons Permuta",
                        high_grade_position=GeoPosition(504620000, 147390000),
                        low_grade_position=GeoPosition(504620000, 147390000),
                    )
                ],
            ),
            # Merge multiple Summits into one if new information reveals that this is necessary
            (
                [Summit(unspecified_names=["Name1"]), Summit(unspecified_names=["Name2"])],
                Summit(official_name="Name1", alternate_names=["Name2"]),
                [
                    Summit(
                        official_name="Name1",
                        alternate_names=["Name2"],
                        unspecified_names=["Name1", "Name2"],
                    )
                ],
            ),
            # ... at least it their positions are close together
            (
                [
                    Summit(
                        unspecified_names=["Name1"],
                        low_grade_position=GeoPosition(404620000, 247390000),
                    ),
                    Summit(
                        unspecified_names=["Name2"],
                        low_grade_position=GeoPosition(404621000, 247389000),
                    ),
                ],
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    high_grade_position=GeoPosition(404620000, 247390000),
                ),
                [
                    Summit(
                        official_name="Name1",
                        alternate_names=["Name2"],
                        unspecified_names=["Name1", "Name2"],
                        high_grade_position=GeoPosition(404620000, 247390000),
                        low_grade_position=GeoPosition(404620000, 247390000),
                    )
                ],
            ),
            # Two summits with the same name that are too far away from each other must not be
            # merged
            (
                [
                    Summit(
                        official_name="Name1", high_grade_position=GeoPosition(304620000, 547390000)
                    )
                ],
                Summit(
                    official_name="Name1", high_grade_position=GeoPosition(547390000, 304620000)
                ),
                [
                    Summit(
                        official_name="Name1", high_grade_position=GeoPosition(304620000, 547390000)
                    ),
                    Summit(
                        official_name="Name1", high_grade_position=GeoPosition(547390000, 304620000)
                    ),
                ],
            ),
            (
                [
                    Summit(
                        unspecified_names=["Name2"],
                        low_grade_position=GeoPosition(404630000, 247380000),
                    ),
                ],
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    high_grade_position=GeoPosition(247390000, 404620000),
                ),
                [
                    Summit(
                        unspecified_names=["Name2"],
                        low_grade_position=GeoPosition(404630000, 247380000),
                    ),
                    Summit(
                        official_name="Name1",
                        alternate_names=["Name2"],
                        high_grade_position=GeoPosition(247390000, 404620000),
                    ),
                ],
            ),
            # Don't change other existing summits
            (
                [Summit("S1"), Summit("S2", high_grade_position=GeoPosition(404620000, 247390000))],
                Summit("S3", high_grade_position=GeoPosition(504620000, 147390000)),
                [
                    Summit("S1"),
                    Summit("S2", high_grade_position=GeoPosition(404620000, 247390000)),
                    Summit("S3", high_grade_position=GeoPosition(504620000, 147390000)),
                ],
            ),
            (
                [
                    Summit("S1", low_grade_position=GeoPosition(304620000, 347390000)),
                    Summit("S2", low_grade_position=GeoPosition(504620000, 147391000)),
                    Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
                ],
                Summit("S2", high_grade_position=GeoPosition(504620000, 147390000)),
                [
                    Summit("S1", low_grade_position=GeoPosition(304620000, 347390000)),
                    Summit(
                        "S2",
                        high_grade_position=GeoPosition(504620000, 147390000),
                        low_grade_position=GeoPosition(504620000, 147391000),
                    ),
                    Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
                ],
            ),
        ],
    )
    def test_merge_summits(
        self,
        existing_summits: list[Summit],
        add_summit: Summit,
        expected_summit_list: list[Summit],
    ) -> None:
        """
        Ensures that add_summit() collects and merges Summit data properly:
         - A Summit not already available is simply added
         - An existing Summit's data is enriched
         - Unrelated existing Summits must not be changed
         - When adding additional names, several existing Summits may have to be merged into one

        :param existing_summits: List of Summits that are already stored in the input pipe.
        :param add_summit: The Summit object to add to the Pipe.
        :param expected_summit_list: List of Summits expected to be stored in the output pipe after
            the filter run.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for summit in existing_summits:
            input_pipe.add_summit(summit)
        input_pipe.add_summit(add_summit)

        # The actual test case: Run the filter
        merge_filter = MergeFilter()
        merge_filter.execute_filter(input_pipe, output_pipe)

        # Check the resulting summit list and data
        for real, expected in zip(
            (s for i, s in output_pipe.iter_summits()),
            expected_summit_list,
            strict=True,
        ):
            assert real.official_name == expected.official_name
            assert sorted(real.alternate_names) == sorted(expected.alternate_names)
            assert sorted(real.unspecified_names) == sorted(expected.unspecified_names)
            assert real.high_grade_position.is_equal_to(expected.high_grade_position)
            assert real.low_grade_position.is_equal_to(expected.low_grade_position)

    @pytest.mark.parametrize(
        ("input_summits", "expected_error"),
        [
            # Error case: Conflicting position data (same name but positions are close together),
            # existing data must not be changed!
            (
                [
                    Summit("S1"),
                    Summit("S2", high_grade_position=GeoPosition(304620000, 547390000)),
                    Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
                    Summit("S2", high_grade_position=GeoPosition(304621000, 547389000)),
                ],
                MergeConflictError,
            ),
        ],
    )
    def test_summit_merge_conflict(
        self, input_summits: list[Summit], expected_error: type[Exception]
    ) -> None:
        """
        Ensures that trying to merge summit data with unresolvable conflicts raises.

        :param input_summits: List of Summits that are stored in the input pipe.
        :param expected_error: The exception type that must be raised.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for summit in input_summits:
            input_pipe.add_summit(summit)

        merge_filter = MergeFilter()
        with pytest.raises(expected_error):
            merge_filter.execute_filter(input_pipe, output_pipe)

    @pytest.mark.parametrize(
        ("input_routes", "expected_output_routes"),
        [
            pytest.param(
                [
                    [Route(1, "AW", grade="", star_count=1), Route(1, "Talweg", grade="")],
                    [Route(1, "AW", grade=""), Route(1, "SO-Rinne", grade="", star_count=2)],
                ],
                [
                    Route(
                        1,
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                    Route(1, "Talweg", grade=""),
                    Route(1, "SO-Rinne", grade="", star_count=2),
                ],
                id="Merge only some of many routes",
            ),
            pytest.param(
                [
                    [Route(1, "Bergweg", grade="", star_count=1), Route(1, "Talweg", grade="")],
                ],
                [
                    Route(
                        1,
                        "Bergweg",
                        star_count=1,
                        grade="",
                    ),
                    Route(1, "Talweg", grade=""),
                ],
                id="Don't merge different routes on the same Summit",
            ),
            pytest.param(
                [
                    [
                        Route(1, "AW", grade="", star_count=1),
                        Route(1, "AW", grade="", star_count=1),
                    ],
                ],
                [
                    Route(
                        1,
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                ],
                id="Merge equal routes on one Summit (single instance)",
            ),
            pytest.param(
                [
                    [
                        Route(1, "AW", grade="", star_count=1),
                        Route(1, "AW", grade="", star_count=1),
                    ],
                    [Route(2, "AW", grade="")],
                ],
                [
                    Route(
                        1,
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                ],
                id="Merge equal routes on one Summit (multiple instances)",
            ),
            pytest.param(
                [
                    [
                        Route(1, "AW", grade="", star_count=1),
                        Route(1, "AW", grade="", star_count=1),
                    ],
                    [Route(2, "AW", grade="")],
                    [Route(2, "AW", grade="")],
                ],
                [
                    Route(
                        1,
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                ],
                id="Merge equal Routes on two Summits",
            ),
            pytest.param(
                [
                    [
                        Route(1, "AW", grade="", star_count=1),
                    ],
                    [Route(2, "AW", grade="")],
                    [Route(2, "AW", grade="")],
                ],
                [
                    Route(
                        1,
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                ],
                id="Merge multiple equal Routes from one second Summit",
            ),
        ],
    )
    def test_merge_multiple_routes_per_summit(
        self,
        input_routes: list[list[Route]],
        expected_output_routes: list[Route],
    ) -> None:
        """
        Tests merging of multiple Routes per Summit instance. Each `input_routes` item is a list of
        Routes of a single Summit instance, but all Summit instances represent the same geographical
        object. That's why `expected_output_routes` is a simple list of (merged) routes.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for routes in input_routes:
            summit_id = input_pipe.add_summit(Summit("Fake Summit"))
            for route in routes:
                input_pipe.add_route(summit_id=summit_id, route=route)

        merge_filter = MergeFilter()
        merge_filter.execute_filter(input_pipe, output_pipe)

        output_summit_data = list(output_pipe.iter_summits())
        assert len(output_summit_data) == 1  # All summits must have been merged into a single one

        # Make sure that the resulting routes are as expected
        output_summit_id = output_summit_data[0][0]
        output_routes = sorted(
            [route for _id, route in output_pipe.iter_routes_of_summit(output_summit_id)],
            key=lambda route: route.route_name,
        )

        assert sorted(expected_output_routes, key=lambda route: route.route_name) == output_routes

    def test_dont_merge_routes_of_different_summits(self) -> None:
        """
        Ensure that two routes with the same name and data on different physical summits (=Summit
        instances with different names) are not merged.
        """
        route1 = Route(
            1,
            "AW",
            grade_af=1,
            grade_ou=2,
            grade_rp=3,
            grade_jump=0,
            star_count=1,
            dangerous=False,
            grade="",
        )
        route2 = Route(
            1,
            "AW",
            grade_af=1,
            grade_ou=2,
            grade_rp=3,
            grade_jump=0,
            star_count=1,
            dangerous=False,
            grade="",
        )
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        summit1_id = input_pipe.add_summit(Summit("Summit 1"))
        summit2_id = input_pipe.add_summit(Summit("Summit 2"))
        input_pipe.add_route(summit_id=summit1_id, route=route1)
        input_pipe.add_route(summit_id=summit2_id, route=route2)

        merge_filter = MergeFilter()
        merge_filter.execute_filter(input_pipe, output_pipe)

        output_pipe_data = {}
        for output_summit_id, output_summit in output_pipe.iter_summits():
            output_pipe_data[output_summit.official_name or ""] = [
                route for _id, route in output_pipe.iter_routes_of_summit(output_summit_id)
            ]

        assert output_pipe_data == {"Summit 1": [route1], "Summit 2": [route2]}

    @pytest.mark.parametrize(
        ("input_route1", "input_route2", "expect_merge"),
        [
            pytest.param(
                Route(
                    1,
                    "Talweg",
                    grade_af=3,
                    grade="",
                ),
                Route(1, "Bergweg", grade_af=3, grade=""),
                False,
                id="Different names (same af and rank)",
            ),
            pytest.param(
                Route(
                    1,
                    "AW",
                    grade_af=5,
                    grade="",
                ),
                Route(
                    1,
                    "AW",
                    grade_af=5,
                    grade="",
                ),
                True,
                id="Same name, same af, same rank",
            ),
            pytest.param(
                Route(
                    1,
                    "AW",
                    grade_af=5,
                    grade="",
                ),
                Route(
                    2,
                    "AW",
                    grade_af=5,
                    grade="",
                ),
                True,
                id="Same name, same af, different rank",
            ),
            pytest.param(
                Route(
                    1,
                    "AW",
                    grade_af=5,
                    grade="",
                ),
                Route(
                    2,
                    "AW",
                    grade_af=6,
                    grade="",
                ),
                True,
                id="Same name, different af, different rank",
            ),
            pytest.param(
                Route(
                    1,
                    "AW",
                    grade_af=5,
                    grade="",
                ),
                Route(
                    1,
                    "AW",
                    grade_af=6,
                    grade="",
                ),
                False,
                id="Same name, different af, same rank",
            ),
            pytest.param(
                Route(
                    1,
                    "AW",
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    grade_jump=1,
                    star_count=2,
                    dangerous=True,
                    grade="",
                ),
                Route(
                    2,
                    "AW",
                    grade_af=4,
                    grade_ou=3,
                    grade_rp=2,
                    grade_jump=5,
                    star_count=1,
                    dangerous=False,
                    grade="",
                ),
                True,
                id="Other data differs",
            ),
            pytest.param(
                Route(
                    1,
                    "alter weg",
                    grade="",
                ),
                Route(
                    1,
                    "Alter Weg",
                    grade="",
                ),
                True,
                id="Name Normalization: Case-insensitivity",
            ),
            pytest.param(
                Route(
                    1,
                    "Alter Weg",
                    grade="",
                ),
                Route(
                    1,
                    "Weg, Alter",
                    grade="",
                ),
                True,
                id="Name Normalization: Permutation",
            ),
            pytest.param(
                Route(
                    1,
                    "Spieglein, Spieglein?",
                    grade="",
                ),
                Route(
                    1,
                    "Spieglein Spieglein",
                    grade="",
                ),
                True,
                id="Name Normalization: Punctuation",
            ),
        ]
        + [
            pytest.param(
                Route(
                    1,
                    abbr,
                    grade="",
                ),
                Route(
                    1,
                    fullname,
                    grade="",
                ),
                True,
                id=f"Name Abbreviation: {abbr}",
            )
            for abbr, fullname in (
                ("AW", "Alter Weg"),
                ("NO-Kante", "Nordostkante"),
                ("NW-Wand", "Nordwestwand"),
                ("SO-Weg", "Südostweg"),
                ("SW-Kamin", "Südwestkamin"),
                ("N-Riss", "Nordriss"),
                ("S-Weg", "Südweg"),
                ("O-Kamin", "Ostkamin"),
                ("W-Kante", "Westkante"),
            )
        ],
    )
    def test_merge_routes_equality_check(
        self,
        input_route1: Route,
        input_route2: Route,
        *,
        expect_merge: bool,
    ) -> None:
        """
        Ensures that testing if several Route objects are actually the same physical route works as
        expected. For this test, all given Route objects are from different Summit instances.
        merged properly.

        Whether two routes are actually "the same" is determined by their (normalized) name, the
        "af" grade and the conflict rank.
        - If the names differ, they are not equal
        - For same names:
            - If the 'af' grades are equal, they are equal regardless of their rank
            - If the 'af' grades differ but the ranks are different, they are equal
        - Names are normalized before comparing:
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for route in (input_route1, input_route2):
            summit_id = input_pipe.add_summit(Summit("Fake Summit"))
            input_pipe.add_route(summit_id=summit_id, route=route)

        merge_filter = MergeFilter()
        merge_filter.execute_filter(input_pipe, output_pipe)

        output_summit_data = list(output_pipe.iter_summits())
        assert len(output_summit_data) == 1  # All summits must have been merged into a single one

        # Make sure that the resulting routes are as expected
        output_summit_id = output_summit_data[0][0]
        output_routes = [
            route for _id, route in output_pipe.iter_routes_of_summit(output_summit_id)
        ]
        assert len(output_routes) == 1 if expect_merge else 2

    @pytest.mark.parametrize(
        ("input_routes", "expected_output_route"),
        [
            pytest.param(
                [
                    Route(2, "AW", grade=""),
                    Route(
                        1,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    ),
                ],
                Route(
                    1,
                    "AW",
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                    grade="",
                ),
                id="Data missing on lower rank (lower first)",
            ),
            pytest.param(
                [
                    Route(
                        1,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    ),
                    Route(2, "AW", grade=""),
                ],
                Route(
                    1,
                    "AW",
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                    grade="",
                ),
                id="Data missing on lower rank (higher first)",
            ),
            pytest.param(
                [
                    Route(
                        2,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    ),
                    Route(1, "AW", grade=""),
                ],
                Route(
                    2,
                    "AW",
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                    grade="",
                ),
                id="Data missing on higher rank (lower first)",
            ),
            pytest.param(
                [
                    Route(1, "AW", grade=""),
                    Route(
                        2,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    ),
                ],
                Route(
                    2,
                    "AW",
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                    grade="",
                ),
                id="Data missing on higher rank (higher first)",
            ),
            pytest.param(
                [
                    Route(
                        1,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    )
                ]
                * 2,
                Route(
                    1,
                    "AW",
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                    grade="",
                ),
                id="Equal data, same rank",
            ),
            pytest.param(
                [
                    Route(
                        1,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    ),
                    Route(
                        2,
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    ),
                ],
                Route(
                    1,
                    "AW",
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                    grade="",
                ),
                id="Equal data, different rank",
            ),
            pytest.param(
                [
                    Route(1, "AW", grade=""),
                    Route(1, "AW", grade="", grade_ou=1),
                    Route(1, "AW", grade=""),
                ],
                Route(
                    1,
                    "AW",
                    grade_ou=1,
                    grade="",
                ),
                id="More than two instances",
            ),
        ],
    )
    def test_merge_routes_data_transfer(
        self,
        input_routes: list[Route],
        expected_output_route: Route,
    ) -> None:
        """
        Ensures that all route data is transferred correctly when merging Routes. All given route
        objects must refer to the same physical route.

         - If data is missing on one side, the other's is taken (including its rank).
         - If both sides have conflicting data, the better-ranked "wins".
         - If both sides are completely equal (regardless of their rank), the better rank is set.

        Whether two routes are actually "the same" is determined by their name and "af" grade (must
        be equal).
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for route in input_routes:
            summit_id = input_pipe.add_summit(Summit("Fake Summit"))
            input_pipe.add_route(summit_id=summit_id, route=route)

        merge_filter = MergeFilter()
        merge_filter.execute_filter(input_pipe, output_pipe)

        output_summit_data = list(output_pipe.iter_summits())
        assert len(output_summit_data) == 1  # All summits must have been merged into a single one

        # Make sure that the resulting routes are as expected
        output_summit_id = output_summit_data[0][0]
        output_routes = sorted(
            [route for _id, route in output_pipe.iter_routes_of_summit(output_summit_id)],
            key=lambda route: route.route_name,
        )

        assert len(output_routes) == 1
        assert expected_output_route == output_routes[0]

    @pytest.mark.parametrize(
        ("input_routes", "expected_error"),
        [
            pytest.param(
                [
                    Route(1, "AW", grade_ou=4, grade=""),
                    Route(1, "AW", grade_rp=2, grade=""),
                ],
                MergeConflictError,
                id="Conflicting ou/rp grade",
            ),
            pytest.param(
                [
                    Route(1, "AW", star_count=2, grade=""),
                    Route(1, "AW", star_count=1, grade=""),
                ],
                MergeConflictError,
                id="Conflicting star count",
            ),
        ],
    )
    def test_route_merge_conflict(
        self, input_routes: list[Route], expected_error: type[Exception]
    ) -> None:
        """
        Ensures that trying to merge route data with unresolvable conflicts raises.

        :param input_routes: List of Routes that are stored in the input pipe.
        :param expected_error: The exception type that must be raised.
        """
        summit_name: Final = "Mock Peak"

        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for route in input_routes:
            summit_id = input_pipe.add_summit(Summit(summit_name))
            input_pipe.add_route(summit_id, route)

        merge_filter = MergeFilter()
        with pytest.raises(expected_error):
            merge_filter.execute_filter(input_pipe, output_pipe)

    @pytest.mark.parametrize(
        "input_posts",
        [
            pytest.param(
                [
                    [
                        Post(
                            user_name="johndoe",
                            comment="some comment",
                            rating=0,
                            post_date=datetime(2019, 4, 13, tzinfo=UTC),
                        ),
                        Post(
                            user_name="maxmu",
                            comment="some other comment",
                            rating=2,
                            post_date=datetime(2021, 8, 5, tzinfo=UTC),
                        ),
                    ]
                ],
                id="Different Posts, single Route",
            ),
            pytest.param(
                [
                    [
                        Post(
                            user_name="johndoe",
                            comment="",
                            rating=1,
                            post_date=datetime(2020, 7, 15, tzinfo=UTC),
                        ),
                        Post(
                            user_name="johndoe",
                            comment="",
                            rating=1,
                            post_date=datetime(2020, 7, 15, tzinfo=UTC),
                        ),
                    ]
                ],
                id="Identical Posts, same Route",
            ),
            pytest.param(
                [
                    [
                        Post(
                            user_name="johndoe",
                            comment="some comment",
                            rating=0,
                            post_date=datetime(2019, 4, 13, tzinfo=UTC),
                        ),
                        Post(
                            user_name="maxmu",
                            comment="some other comment",
                            rating=2,
                            post_date=datetime(2021, 8, 5, tzinfo=UTC),
                        ),
                    ]
                ],
                id="Different Posts, different Routes",
            ),
            pytest.param(
                [
                    [
                        Post(
                            user_name="johndoe",
                            comment="",
                            rating=1,
                            post_date=datetime(2020, 7, 15, tzinfo=UTC),
                        ),
                    ],
                    [
                        Post(
                            user_name="johndoe",
                            comment="",
                            rating=1,
                            post_date=datetime(2020, 7, 15, tzinfo=UTC),
                        ),
                    ],
                ],
                id="Identical Posts, different Routes",
            ),
        ],
    )
    def test_merge_posts(self, input_posts: list[list[Post]]) -> None:
        """
        Ensures that all posts are kept when merging route data. Posts are not actually merged but
        just added to the target route.

        The `input_posts` is a nested list, with the outer list being different Route objects
        (describing the same physical route) and the inner list containing all posts assigned to
        this Route object.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for route in input_posts:
            summit_id = input_pipe.add_summit(Summit("Summit"))
            route_id = input_pipe.add_route(summit_id, Route(1, route_name="Route", grade=""))
            for post in route:
                input_pipe.add_post(route_id, post)

        merge_filter = MergeFilter()
        merge_filter.execute_filter(input_pipe, output_pipe)

        output_summit_ids = [summit_id for summit_id, _summit in output_pipe.iter_summits()]
        assert len(output_summit_ids) == 1  # All summits must have been merged into a single one

        output_route_ids = [
            route_id for route_id, _route in output_pipe.iter_routes_of_summit(output_summit_ids[0])
        ]
        assert len(output_route_ids) == 1  # All routes must have been merged into a single one

        # Make sure that the resulting route contains all posts
        expected_post = [post for post in route for route in input_posts]
        output_posts = list(output_pipe.iter_posts_of_route(output_route_ids[0]))
        assert output_posts == expected_post


class TestSummitMerger:
    """Unit tests for the _SummitMerger class."""

    @pytest.mark.parametrize(
        ("existing_summit", "summit_to_merge", "expected_summit", "failure_context"),
        [
            # Merge position data into an existing summit
            (
                Summit("Summit 1"),
                Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
                nullcontext(),
            ),
            (
                Summit("Summit 1"),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                nullcontext(),
            ),
            (
                Summit("Summit 1", high_grade_position=GeoPosition(504567000, 147650000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                Summit(
                    "Summit 1",
                    high_grade_position=GeoPosition(504567000, 147650000),
                    low_grade_position=GeoPosition(504620000, 147390000),
                ),
                nullcontext(),
            ),
            (
                Summit("Summit 1", low_grade_position=GeoPosition(504567000, 147650000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504567000, 147650000)),
                nullcontext(),
            ),
            # Merging equal position datá must not raise an error
            (
                Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
                Summit(
                    "Summit 1",
                    alternate_names=["Summit 2"],
                    high_grade_position=GeoPosition(504620000, 147390000),
                ),
                Summit(
                    "Summit 1",
                    alternate_names=["Summit 2"],
                    high_grade_position=GeoPosition(504620000, 147390000),
                ),
                nullcontext(),
            ),
            # Merge multiple names in various variants
            (
                Summit(official_name="Official", alternate_names=["Alt1", "Alt2"]),
                Summit(official_name="Official", alternate_names=["Alt3"]),
                Summit(official_name="Official", alternate_names=["Alt1", "Alt2", "Alt3"]),
                nullcontext(),
            ),
            (
                Summit(official_name="Official", alternate_names=["Alt2"]),
                Summit(alternate_names=["Official", "Alt3"]),
                Summit(official_name="Official", alternate_names=["Alt2", "Alt3"]),
                nullcontext(),
            ),
            (
                Summit(unspecified_names=["Unspec"]),
                Summit(official_name="Name", alternate_names=["Alt1", "Alt2"]),
                Summit(
                    official_name="Name",
                    alternate_names=["Alt1", "Alt2"],
                    unspecified_names=["Unspec"],
                ),
                nullcontext(),
            ),
            # Error Cases
            (
                Summit("Summit", high_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit", high_grade_position=GeoPosition(404620000, 247390000)),
                Summit("Summit", high_grade_position=GeoPosition(504620000, 147390000)),
                pytest.raises(MergeConflictError),
            ),
        ],
    )
    def test_enrich_summit(
        self,
        existing_summit: Summit,
        summit_to_merge: Summit,
        expected_summit: Summit,
        failure_context: AbstractContextManager[None],
    ) -> None:
        """
        Tests the enrichment ("merge") of an existing Summit object with data from another one:

        - Position data is added if there is none already
        - The official name is set if it is not already
        - All alternate and unspecified names are added to the existing Summit
        - The official name must not be included in the alternate names list
        - Unresolvable merge conflicts raise a MergeConflictError (preserving existing data)
        """
        with failure_context:
            _SummitMerger.enrich_summit(target=existing_summit, source=summit_to_merge)

            assert existing_summit.official_name == expected_summit.official_name
            assert sorted(existing_summit.alternate_names) == sorted(
                expected_summit.alternate_names
            )
            assert sorted(existing_summit.unspecified_names) == sorted(
                expected_summit.unspecified_names
            )
            assert existing_summit.high_grade_position.is_equal_to(
                expected_summit.high_grade_position
            )

            assert existing_summit.low_grade_position.is_equal_to(
                expected_summit.low_grade_position
            )


class TestRouteMerger:
    """Unit tests for the _RouteMerger class."""

    @pytest.mark.parametrize(
        ("route1", "route2", "expected_route"),
        [
            # Completely equal data
            (
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            (
                Route(1, "My Route", ""),
                Route(1, "My Route", ""),
                Route(1, "My Route", ""),
            ),
            # Only rank differs
            (
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            (
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            # Data missing on one side
            (
                Route(1, "My Route", ""),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            (
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(1, "My Route", ""),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            # Rank is ignored for missing data
            (
                Route(1, "My Route", ""),
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            (
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
                Route(1, "My Route", ""),
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=3,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            # In case of conflicts, the rank decides
            (
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=1,
                    grade_af=2,
                    grade_ou=3,
                    grade_rp=4,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=4,
                    grade_af=3,
                    grade_ou=2,
                    grade_rp=1,
                    dangerous=False,
                    star_count=2,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=1,
                    grade_af=2,
                    grade_ou=3,
                    grade_rp=4,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            (
                Route(
                    2,
                    "My Route",
                    "",
                    grade_jump=1,
                    grade_af=2,
                    grade_ou=3,
                    grade_rp=4,
                    dangerous=True,
                    star_count=1,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=4,
                    grade_af=3,
                    grade_ou=2,
                    grade_rp=1,
                    dangerous=False,
                    star_count=2,
                ),
                Route(
                    1,
                    "My Route",
                    "",
                    grade_jump=4,
                    grade_af=3,
                    grade_ou=2,
                    grade_rp=1,
                    dangerous=False,
                    star_count=2,
                ),
            ),
        ],
    )
    def test_enrich_route(self, route1: Route, route2: Route, expected_route: Route) -> None:
        """
        Tests the enrichment ("merge") of an existing Route object with data from another one:

        - Completely equal data is just used
        - In case of a data conflict, the data with the higher 'conflict rank' is used
        - If only one objects provides data at all, it is used (regardless of its rank)
        - When using data from another object, the others rank is also applied
        - If data with different ranks is otherwise equal, the better rank is chosen
        - When using lower-rank data, the rank decreases
        """
        merger = _RouteMerger([])
        merger._merge_objects(_RouteRelatedData(route1, []), _RouteRelatedData(route2, []))
        assert route1.route_name == expected_route.route_name
        assert route1.grade_af == expected_route.grade_af
        assert route1.grade_ou == expected_route.grade_ou
        assert route1.grade_rp == expected_route.grade_rp
        assert route1.grade_jump == expected_route.grade_jump
        assert route1.dangerous == expected_route.dangerous
        assert route1.star_count == expected_route.star_count
        assert route1.conflict_rank == expected_route.conflict_rank
