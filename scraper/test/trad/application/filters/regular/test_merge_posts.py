"""
Unit tests for the trad.application.filters.regular.merge module merging Posts.
"""

from datetime import UTC, datetime

import pytest

from trad.application.filters.regular.merge import MergeFilter
from trad.application.pipes import CollectedData
from trad.kernel.entities import Post, Route, Summit


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
def test_merge_posts(input_posts: list[list[Post]]) -> None:
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
