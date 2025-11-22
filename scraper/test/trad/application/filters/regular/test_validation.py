"""
Unit tests for the trad.application.filters.regular.validation module
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from trad.application.filters.regular.validation import DataValidationFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe, RouteInstanceId, SummitInstanceId
from trad.kernel.entities import Post, Route, Summit
from trad.kernel.errors import IncompleteDataError


def _prepare_pipe(
    input_summits: list[Summit],
    input_routes: list[tuple[Route, int]],
    input_posts: list[tuple[Post, int]],
) -> Pipe:
    """
    Create a new Pipe() with the given data. The second tuple component of the `input_routes` items
    is the corresponding index in the `input_summits` list. The second tuple component in the
    `input_posts` items is the corresponding index in the `input_routes` list.
    """
    pipe = CollectedData()
    summit_idx_to_id: dict[int, SummitInstanceId] = {}
    for summit_idx, summit in enumerate(input_summits):
        summit_id = pipe.add_summit(summit)
        summit_idx_to_id[summit_idx] = summit_id

    route_idx_to_id: dict[int, RouteInstanceId] = {}
    for route_idx, (route, summit_idx) in enumerate(input_routes):
        route_id = pipe.add_route(summit_id=summit_idx_to_id[summit_idx], route=route)
        route_idx_to_id[route_idx] = route_id

    for post, route_idx in input_posts:
        pipe.add_post(route_id=route_idx_to_id[route_idx], post=post)
    return pipe


def _compare_pipes(actual_pipe: Pipe, expected_pipe: Pipe) -> None:
    """
    Compare the contents of the given Pipes using assert(). The entity IDs may be different, but the
    actual entity objects must be equal.
    """
    for (actual_summit_id, actual_summit), (expected_summit_id, expected_summit) in zip(
        actual_pipe.iter_summits(),
        expected_pipe.iter_summits(),
        strict=True,
    ):
        assert actual_summit == expected_summit

        for (actual_route_id, actual_route), (expected_route_id, expected_route) in zip(
            actual_pipe.iter_routes_of_summit(actual_summit_id),
            expected_pipe.iter_routes_of_summit(expected_summit_id),
            strict=True,
        ):
            assert actual_route == expected_route

            for actual_post, expected_post in zip(
                actual_pipe.iter_posts_of_route(actual_route_id),
                expected_pipe.iter_posts_of_route(expected_route_id),
                strict=True,
            ):
                assert actual_post == expected_post


def _create_example_route(route_number: int) -> Route:
    return Route(f"Route No. {route_number}", grade="III")


def _create_example_post(post_number: int) -> Post:
    dt = datetime.now(tz=UTC)
    return Post(
        user_name="Some User",
        comment=f"This is comment #{post_number}",
        rating=0,
        post_date=datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0, tzinfo=dt.tzinfo),
    )


@dataclass
class PipeData:
    """
    Content definition of a single Pipe (test case parameter).
    """

    summits: list[Summit]
    """ List of written Summits. """
    routes: list[tuple[Route, int]]
    """
    List of written Routes and their corresponding Summits (the `int` value is an index into the
    `summits` list).
    """
    posts: list[tuple[Post, int]]
    """
    List of written Posts and their corresponding Routes (the `int` value is an index into the
    `routes` list).
    """


@pytest.mark.parametrize(
    ("input_pipe_data", "output_pipe_data"),
    [
        # Happy paths, i.e. valid data
        (  # Empty Pipe
            PipeData([], [], []),
            PipeData([], [], []),
        ),
        (  # Single summit with a route and and post
            PipeData(
                [Summit("Example Summit")],
                [(_create_example_route(13), 0)],
                [(_create_example_post(42), 0)],
            ),
            PipeData(
                [Summit("Example Summit")],
                [(_create_example_route(13), 0)],
                [(_create_example_post(42), 0)],
            ),
        ),
        (  # Multiple summits and routes
            PipeData(
                [Summit("Summit 1"), Summit("Summit 2"), Summit("Summit 3")],
                [
                    (_create_example_route(1), 0),
                    (_create_example_route(2), 0),
                    (_create_example_route(3), 2),
                ],
                [
                    (_create_example_post(1), 0),
                    (_create_example_post(2), 1),
                    (_create_example_post(3), 1),
                ],
            ),
            PipeData(
                [Summit("Summit 1"), Summit("Summit 2"), Summit("Summit 3")],
                [
                    (_create_example_route(1), 0),
                    (_create_example_route(2), 0),
                    (_create_example_route(3), 2),
                ],
                [
                    (_create_example_post(1), 0),
                    (_create_example_post(2), 1),
                    (_create_example_post(3), 1),
                ],
            ),
        ),
        # Invalid data: Summit must be ignored
        (  # Invalid Summit data
            PipeData(
                [
                    Mock(
                        Summit,
                        **{
                            "fix_invalid_data.side_effect": IncompleteDataError(
                                Mock(Summit), "name"
                            )
                        },
                    )
                ],
                [],
                [],
            ),
            PipeData(
                [],
                [],
                [],
            ),
        ),
        (  # Invalid Route data (ignore the whole summit)
            PipeData(
                [Summit("Summit")],
                [
                    (
                        Mock(
                            Route,
                            **{
                                "fix_invalid_data.side_effect": IncompleteDataError(
                                    Mock(Route), "name"
                                )
                            },
                        ),
                        0,
                    )
                ],
                [],
            ),
            PipeData(
                [],
                [],
                [],
            ),
        ),
        (  # Other (valid) summits must still be written
            PipeData(
                [
                    Mock(
                        Summit,
                        **{
                            "fix_invalid_data.side_effect": IncompleteDataError(
                                Mock(Summit), "name"
                            )
                        },
                    ),
                    Summit("Good Summit"),
                ],
                [],
                [],
            ),
            PipeData(
                [Summit("Good Summit")],
                [],
                [],
            ),
        ),
    ],
)
def test_valid_data(
    input_pipe_data: PipeData,
    output_pipe_data: PipeData,
) -> None:
    """
    Ensure that the validation ignores the summits with any invalid (and not fixable) data, but
    writes all valid ones.
    Auto-fixing is tested on the entity directly, so there are no extra test cases for it here.
    """
    input_pipe = _prepare_pipe(
        input_pipe_data.summits, input_pipe_data.routes, input_pipe_data.posts
    )
    output_pipe = CollectedData()

    data_filter = DataValidationFilter()
    data_filter.execute_filter(input_pipe, output_pipe)

    expected_output_pipe = _prepare_pipe(
        output_pipe_data.summits,
        output_pipe_data.routes,
        output_pipe_data.posts,
    )

    _compare_pipes(output_pipe, expected_output_pipe)
