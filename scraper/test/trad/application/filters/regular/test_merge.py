"""
Unit tests for the trad.application.filters.regular.merge module.
"""

from datetime import UTC, datetime
from typing import Final

import pytest

from trad.application.filters.regular.merge import MergeFilter
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
                    [Route("AW", grade="")],
                    [
                        Route(
                            "AW",
                            grade_af=9,
                            grade_ou=8,
                            grade_rp=7,
                            grade_jump=6,
                            star_count=0,
                            dangerous=True,
                            grade="",
                        )
                    ],
                ],
                [
                    Route(
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    )
                ],
                id="Merge two routes (first one without data)",
            ),
            pytest.param(
                [
                    [
                        Route(
                            "AW",
                            grade_af=9,
                            grade_ou=8,
                            grade_rp=7,
                            grade_jump=6,
                            star_count=0,
                            dangerous=True,
                            grade="",
                        )
                    ],
                    [Route("AW", grade="")],
                ],
                [
                    Route(
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    )
                ],
                id="Merge two routes (second one without data)",
            ),
            pytest.param(
                [
                    [
                        Route(
                            "AW",
                            star_count=2,
                            grade="",
                        )
                    ],
                    [Route("AW", grade="")],
                ],
                [
                    Route(
                        "AW",
                        star_count=2,
                        grade="",
                    )
                ],
                id="Merge two routes (star count only)",
            ),
            pytest.param(
                [
                    [
                        Route(
                            "AW",
                            dangerous=True,
                            grade="",
                        )
                    ],
                    [Route("AW", grade="")],
                ],
                [
                    Route(
                        "AW",
                        dangerous=True,
                        grade="",
                    )
                ],
                id="Merge two routes (danger only)",
            ),
            pytest.param(
                [
                    [
                        Route(
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
                ]
                * 2,
                [
                    Route(
                        "AW",
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                        grade="",
                    )
                ],
                id="Merge two routes with equal data",
            ),
            pytest.param(
                [
                    [Route("AW", grade="", star_count=1), Route("Talweg", grade="")],
                    [Route("AW", grade=""), Route("SO-Rinne", grade="", star_count=2)],
                ],
                [
                    Route(
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                    Route("Talweg", grade=""),
                    Route("SO-Rinne", grade="", star_count=2),
                ],
                id="Merge some of many routes",
            ),
            pytest.param(
                [
                    [Route("AW", grade="")],
                    [Route("AW", grade="", star_count=1)],
                    [Route("AW", grade="")],
                ],
                [
                    Route(
                        "AW",
                        star_count=1,
                        grade="",
                    ),
                ],
                id="Merge more than two Summit instances",
            ),
        ],
    )
    def test_merge_routes_same_summit(
        self,
        input_routes: list[list[Route]],
        expected_output_routes: list[Route],
    ) -> None:
        """
        Ensures that Route data on a single summit (but different Summit instances) is merged
        properly. Each `input_routes` item is a list of Routes of a single Summit instance, but all
        Summit instances (and therefore, all routes) represent the same geographical object. That's
        why `expected_output_routes` is a simple list of (merged) routes.
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

    def test_merge_routes_different_summits(self) -> None:
        """Ensure that two routes with the same name on different summits are not merged."""
        route1 = Route(
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
            "AW",
            grade_af=9,
            grade_ou=8,
            grade_rp=7,
            grade_jump=6,
            star_count=0,
            dangerous=True,
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
        ("input_routes", "expected_error"),
        [
            pytest.param(
                [
                    Route("AW", grade_af=4, grade=""),
                    Route("AW", grade_af=2, grade=""),
                ],
                MergeConflictError,
                id="Conflicting af grade",
            ),
            pytest.param(
                [
                    Route("AW", grade_ou=4, grade=""),
                    Route("AW", grade_rp=2, grade=""),
                ],
                MergeConflictError,
                id="Conflicting ou/rp grade",
            ),
            pytest.param(
                [
                    Route("AW", star_count=2, grade=""),
                    Route("AW", star_count=1, grade=""),
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
                    Post(
                        user_name="johndoe",
                        comment="some comment",
                        rating=0,
                        post_date=datetime(2019, 4, 13, tzinfo=UTC),
                    ),
                    Post(
                        user_name="maxmu",
                        comment="some other ocmment",
                        rating=2,
                        post_date=datetime(2021, 8, 5, tzinfo=UTC),
                    ),
                ],
                id="Two different posts",
            ),
            pytest.param(
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
                ],
                id="Identical post data",
            ),
        ],
    )
    def test_merge_posts(self, input_posts: list[Post]) -> None:
        """
        Ensures that all posts are kept when merging route data. Posts are not actually merged but
        just added to the target route.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for post in input_posts:
            summit_id = input_pipe.add_summit(Summit("Summit"))
            route_id = input_pipe.add_route(summit_id, Route(route_name="Route", grade=""))
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
        output_posts = list(output_pipe.iter_posts_of_route(output_route_ids[0]))
        assert output_posts == input_posts
