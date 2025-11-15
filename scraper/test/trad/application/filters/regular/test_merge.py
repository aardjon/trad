"""
Unit tests for the trad.application.filters.regular.merge module.
"""

from datetime import UTC, datetime

import pytest

from trad.application.filters.regular.merge import MergeFilter
from trad.application.pipe import CollectedData
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
    def test_add_summit(
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
    def test_add_summit_merge_conflict(
        self, input_summits: list[Summit], expected_error: type[Exception]
    ) -> None:
        """
        Ensures that add_summit() raises in case of unsolvable merge conflicts.

        :param input_summits: List of Summits that are stored in the input pipe.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        for summit in input_summits:
            input_pipe.add_summit(summit)

        merge_filter = MergeFilter()
        with pytest.raises(expected_error):
            merge_filter.execute_filter(input_pipe, output_pipe)

    def test_add_route(self) -> None:
        """
        Ensures that add_route() collects and merges Route data properly.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        dummy_route = Route(route_name="Example Trail", grade="I")
        summit_id = input_pipe.add_summit(Summit("Summit"))
        route_id = input_pipe.add_route(summit_id, dummy_route)

        merge_filter = MergeFilter()

        merge_filter.execute_filter(input_pipe, output_pipe)
        assert list(output_pipe.iter_routes_of_summit(summit_id)) == [(route_id, dummy_route)]

    def test_add_post(self) -> None:
        """
        Ensures that add_post() collects Post data properly.
        """
        input_pipe = CollectedData()
        output_pipe = CollectedData()

        summit_id = input_pipe.add_summit(Summit("Summit"))
        route_id = input_pipe.add_route(summit_id, Route(route_name="Route", grade="III"))
        dummy_post = Post(
            user_name="johndoe",
            comment="",
            rating=1,
            post_date=datetime(2020, 7, 15, tzinfo=UTC),
        )
        input_pipe.add_post(route_id, dummy_post)

        merge_filter = MergeFilter()

        merge_filter.execute_filter(input_pipe, output_pipe)
        assert list(output_pipe.iter_posts_of_route(route_id)) == [dummy_post]
