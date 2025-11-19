"""
Unit tests for the trad.application.pipes module.
"""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from trad.application.pipes import AllPipesFactory, CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import Post, Route, Summit
from trad.kernel.errors import EntityNotFoundError


class TestCollectedData:
    """
    Unit tests for the CollectedData Pipe class.
    """

    @pytest.mark.parametrize("summit_count", [0, 1, 3])
    def test_summit_storage_roundtrip(self, summit_count: int) -> None:
        """
        Ensure that all added summits can be retrieved again.

        :param summit_count: Number of summits to add.
        """
        pipe = CollectedData()

        summits = [Summit(f"Summit #{i}") for i in range(summit_count)]
        for summit in summits:
            pipe.add_summit(summit)

        returned_summits = [s for i, s in pipe.iter_summits()]
        assert returned_summits == summits

    @pytest.mark.parametrize(
        "route_count_per_summit",
        [
            [0, 0],  # Summits without routes
            [4, 1, 3, 2],  # Different number of routes
            [2, 0],  # Some summits without routes
            [2],  # One summit only
        ],
    )
    def test_route_storage_roundtrip(self, route_count_per_summit: list[int]) -> None:
        """
        Ensure that all added routes can be retrieved again, and are assigned to the correct
        summits.

        :param route_count_per_summit: List of route counts per summit, i.e. each list item
            represents a summit, and its value is the number of routes on it.
        """
        pipe = CollectedData()

        routes_of_summits = {}
        route_number_base = 0
        for summit_idx, route_count in enumerate(route_count_per_summit):
            summit_id = pipe.add_summit(Mock(Summit, name=f"Summit #{summit_idx}"))

            routes_of_summits[summit_id] = [
                Route(f"Route #{route_number_base + i}", "I") for i in range(route_count)
            ]
            for route in routes_of_summits[summit_id]:
                pipe.add_route(summit_id, route)
            route_number_base += route_count

        assert len(routes_of_summits) == len(route_count_per_summit)

        for summit_id, expected_routes in routes_of_summits.items():
            returned_routes = [r for _i, r in pipe.iter_routes_of_summit(summit_id)]
            assert returned_routes == expected_routes

    @pytest.mark.parametrize(
        "post_count_per_route",
        [
            [0, 0],  # Route without any posts
            [4, 1, 3, 2],  # Different number of posts
            [2, 0],  # Some routes without posts
            [2],  # One post only
        ],
    )
    def test_post_storage_roundtrip(self, post_count_per_route: list[int]) -> None:
        """
        Ensure that all added posts can be retrieved again, and are assigned to the correct
        routes.

        :param post_count_per_route: List of post counts per route, i.e. each list item
            represents a route, and its value is the number of posts for it.
        """
        pipe = CollectedData()
        summit_id = pipe.add_summit(Mock(Summit, name="Summit"))

        posts_of_routes = {}
        post_number_base = 0
        for route_idx, post_count in enumerate(post_count_per_route):
            route_id = pipe.add_route(summit_id, route=Mock(Route, name=f"Route #{route_idx}"))

            posts_of_routes[route_id] = [
                Post(
                    user_name="Some User",
                    comment=f"Post #{post_number_base + i}",
                    post_date=datetime.now(tz=UTC),
                    rating=0,
                )
                for i in range(post_count)
            ]
            for post in posts_of_routes[route_id]:
                pipe.add_post(route_id, post)
            post_number_base += post_count

        assert len(posts_of_routes) == len(post_count_per_route)

        for route_id, expected_posts in posts_of_routes.items():
            returned_posts = list(pipe.iter_posts_of_route(route_id))
            assert returned_posts == expected_posts

    @pytest.mark.parametrize(
        ("invalid_id_operation", "expected_error_message"),
        [
            (
                lambda pipe: pipe.add_route(summit_id=1337, route=Route("Route 1", "V")),
                "Summit",
            ),
            (
                lambda pipe: pipe.add_post(
                    route_id=1337, post=Post("John Doe", datetime.now(tz=UTC), "", 0)
                ),
                "Route",
            ),
        ],
    )
    def test_write_operation_invalid_ids(
        self, invalid_id_operation: Callable[[Pipe], None], expected_error_message: str
    ) -> None:
        """
        Ensures that writing methods taking an ID parameter raise as expected when an invalid ID is
        provided.

        :param invalid_id_operation: Callable that retrieves the Pipe instance to test and executes
            the failing operation on this pipe.
        :param expected_error_message: Regexp the error message of the raised EntityNotFoundError
            is expected to match with.
        """
        pipe = CollectedData()
        with pytest.raises(EntityNotFoundError, match=expected_error_message):
            invalid_id_operation(pipe)

    @pytest.mark.parametrize(
        "invalid_id_operation",
        [
            lambda pipe: pipe.iter_routes_of_summit(summit_id=1337),
            lambda pipe: pipe.iter_posts_of_route(route_id=1337),
        ],
    )
    def test_read_operation_invalid_ids(
        self, invalid_id_operation: Callable[[Pipe], Iterator[object]]
    ) -> None:
        """
        Ensures that reading methods taking an ID parameter return an empty iterator when an invalid
        ID is provided.

        :param invalid_id_operation: Callable that retrieves the Pipe instance to test and executes
            the failing operation on this pipe.
        """
        pipe = CollectedData()
        full_result_data = list(invalid_id_operation(pipe))
        assert not full_result_data


def test_pipe_factory() -> None:
    """Ensures that the AllPipesFactory creates a new instance on each create_pipe() call."""
    factory = AllPipesFactory()
    pipe1 = factory.create_pipe()
    pipe2 = factory.create_pipe()
    assert pipe1 is not pipe2
