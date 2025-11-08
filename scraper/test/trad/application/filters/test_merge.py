"""
Unit tests for the trad.application.filters.merge module.
"""

from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from trad.application.filters.merge import MergingPipeDecorator
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import GeoPosition, Post, Route, Summit
from trad.kernel.errors import MergeConflictError


class TestMergingPipeDecorator:
    """
    Unit tests for the MergingPipeDecorator class.
    """

    def test_initialize_pipe(self) -> None:
        inner_pipe = Mock(Pipe)
        proxy_pipe = MergingPipeDecorator(inner_pipe)

        proxy_pipe.initialize_pipe()
        inner_pipe.initialize_pipe.assert_called_once()

    def test_finalize_pipe(self) -> None:
        inner_pipe = Mock(Pipe)
        proxy_pipe = MergingPipeDecorator(inner_pipe)

        proxy_pipe.finalize_pipe()
        inner_pipe.finalize_pipe.assert_called_once()

    @pytest.mark.parametrize(
        ("existing_summits", "add_summit", "expected_summit_list", "failure_context"),
        [
            # Simple adding of a new summit
            ([], Summit("Summit"), [Summit("Summit")], nullcontext()),
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
                nullcontext(),
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
                nullcontext(),
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
                nullcontext(),
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
                nullcontext(),
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
                nullcontext(),
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
                nullcontext(),
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
                nullcontext(),
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
                nullcontext(),
            ),
            # Error case: Conflicting position data (same name but positions are close together),
            # existing data must not be changed!
            (
                [
                    Summit("S1"),
                    Summit("S2", high_grade_position=GeoPosition(304620000, 547390000)),
                    Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
                ],
                Summit("S2", high_grade_position=GeoPosition(304621000, 547389000)),
                [
                    Summit("S1"),
                    Summit("S2", high_grade_position=GeoPosition(304620000, 547390000)),
                    Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
                ],
                pytest.raises(MergeConflictError),
            ),
        ],
    )
    def test_add_or_enrich_summit(
        self,
        existing_summits: list[Summit],
        add_summit: Summit,
        expected_summit_list: list[Summit],
        failure_context: AbstractContextManager[None],
    ) -> None:
        """
        Ensures that add_summit() collects and merges Summit data properly:
         - A Summit not already available is simply added
         - An existing Summit's data is enriched
         - Unrelated existing Summits must not be changed
         - When adding additional names, several existing Summits may have to be merged into one
         - Unsolvable merge conflicts raise a MergeConflictError (preserving existing data)

        :param existing_summits: List of Summits that are already stored in the Pipe.
        :param add_summit: The Summit object to add to the Pipe.
        :param expected_summit_list: List of Summits expected to be stored in the Pipe after the add
            operation.
        :param failure_context: Exception context the adding is done within, can be used to expect a
            certain exception to be raised.
        """
        inner_pipe = Mock(Pipe)

        proxy_pipe = MergingPipeDecorator(inner_pipe)
        for summit in existing_summits:
            proxy_pipe.add_summit(summit)

        # The actual test case: Adding another summit
        with failure_context:
            proxy_pipe.add_summit(add_summit)

        # Check the resulting summit list and data
        for real, expected in zip(
            proxy_pipe.get_collected_summits(),
            expected_summit_list,
            strict=True,
        ):
            assert real.official_name == expected.official_name
            assert sorted(real.alternate_names) == sorted(expected.alternate_names)
            assert sorted(real.unspecified_names) == sorted(expected.unspecified_names)
            assert real.high_grade_position.is_equal_to(expected.high_grade_position)
            assert real.low_grade_position.is_equal_to(expected.low_grade_position)

    def test_add_or_enrich_route(self) -> None:
        """
        Ensures that add_route() collects and merges Route data properly.
        """
        inner_pipe = Mock(Pipe)
        proxy_pipe = MergingPipeDecorator(inner_pipe)
        proxy_pipe.add_summit(Summit("Summit"))
        dummy_route = Route(route_name="Example Trail", grade="I")

        proxy_pipe.add_route("Summit", dummy_route)

        assert list(proxy_pipe.get_collected_routes("Summit")) == [dummy_route]

    def test_add_post(self) -> None:
        """
        Ensures that add_post() collects Post data properly.
        """
        inner_pipe = Mock(Pipe)
        proxy_pipe = MergingPipeDecorator(inner_pipe)
        proxy_pipe.add_summit(Summit("Summit"))
        proxy_pipe.add_route("Summit", Route(route_name="Route", grade="III"))
        dummy_post = Post(
            user_name="johndoe",
            comment="",
            rating=1,
            post_date=datetime(2020, 7, 15, tzinfo=UTC),
        )

        proxy_pipe.add_post("Summit", "Route", dummy_post)

        assert list(proxy_pipe.get_collected_posts("Summit", "Route")) == [dummy_post]
