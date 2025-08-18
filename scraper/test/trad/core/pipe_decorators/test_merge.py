"""
Unit tests for the trad.core.proxy_pipes.merge module.
"""

from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from trad.core.boundaries.pipes import Pipe
from trad.core.entities import GeoPosition, Post, Route, Summit
from trad.core.errors import MergeConflictError
from trad.core.pipe_decorators.merge import MergingPipeDecorator


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
            # Merge position data into an existing summit
            (
                [Summit("Summit 1")],
                Summit("Summit 1", GeoPosition(504620000, 147390000)),
                [Summit("Summit 1", GeoPosition(504620000, 147390000))],
                nullcontext(),
            ),
            # Merge different name variants
            (
                [Summit("Mons Permuta")],
                Summit("Permuta, Mons", GeoPosition(504620000, 147390000)),
                [Summit("Mons Permuta", GeoPosition(504620000, 147390000))],
                nullcontext(),
            ),
            # Don't change other existing summits
            (
                [Summit("S1"), Summit("S2", GeoPosition(404620000, 247390000))],
                Summit("S3", GeoPosition(504620000, 147390000)),
                [
                    Summit("S1"),
                    Summit("S2", GeoPosition(404620000, 247390000)),
                    Summit("S3", GeoPosition(504620000, 147390000)),
                ],
                nullcontext(),
            ),
            (
                [Summit("S1"), Summit("S2"), Summit("S3", GeoPosition(404620000, 247390000))],
                Summit("S2", GeoPosition(504620000, 147390000)),
                [
                    Summit("S1"),
                    Summit("S2", GeoPosition(504620000, 147390000)),
                    Summit("S3", GeoPosition(404620000, 247390000)),
                ],
                nullcontext(),
            ),
            # Error case: Conflicting position data, existing data must not be changed!
            (
                [Summit("Summit", GeoPosition(504620000, 147390000))],
                Summit("Summit", GeoPosition(404620000, 247390000)),
                [Summit("Summit", GeoPosition(504620000, 147390000))],
                pytest.raises(MergeConflictError),
            ),
            (
                [
                    Summit("S1"),
                    Summit("S2", GeoPosition(304620000, 547390000)),
                    Summit("S3", GeoPosition(404620000, 247390000)),
                ],
                Summit("S2", GeoPosition(504620000, 147390000)),
                [
                    Summit("S1"),
                    Summit("S2", GeoPosition(304620000, 547390000)),
                    Summit("S3", GeoPosition(404620000, 247390000)),
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
        Ensures that add_or_enrich_summit() collects and merges Summit data properly.
        """
        inner_pipe = Mock(Pipe)

        proxy_pipe = MergingPipeDecorator(inner_pipe)
        for summit in existing_summits:
            proxy_pipe.add_or_enrich_summit(summit)

        # The actual test case: Adding another summit
        with failure_context:
            proxy_pipe.add_or_enrich_summit(add_summit)

        # Check the resulting summit list and data
        for real, expected in zip(
            proxy_pipe.get_collected_summits(),
            expected_summit_list,
            strict=True,
        ):
            assert real.name == expected.name
            assert real.position.latitude_int == expected.position.latitude_int
            assert real.position.longitude_int == expected.position.longitude_int

    def test_add_or_enrich_route(self) -> None:
        """
        Ensures that add_or_enrich_route() collects and merges Route data properly.
        """
        inner_pipe = Mock(Pipe)
        proxy_pipe = MergingPipeDecorator(inner_pipe)
        dummy_route = Route(route_name="Example Trail", grade="I")

        proxy_pipe.add_or_enrich_route("Summit", dummy_route)

        assert list(proxy_pipe.get_collected_routes("Summit")) == [dummy_route]

    def test_add_post(self) -> None:
        """
        Ensures that add_post() collects Post data properly.
        """
        inner_pipe = Mock(Pipe)
        proxy_pipe = MergingPipeDecorator(inner_pipe)
        dummy_post = Post(
            user_name="johndoe",
            comment="",
            rating=1,
            post_date=datetime(2020, 7, 15, tzinfo=UTC),
        )

        proxy_pipe.add_post("Summit", "Route", dummy_post)

        assert list(proxy_pipe.get_collected_posts("Summit", "Route")) == [dummy_post]
