"""
Unit tests for the trad.application.filters.source.sandsteinklettern filter implementation testing
the processing of posts.

TODO: Test Cases:
 - Error cases (exception)
"""

from datetime import UTC, datetime
from unittest.mock import ANY

import pytest

from trad.kernel.entities.routedata import Post

from .conftest import JsonTestData, PreparedFilterRunner


@pytest.mark.parametrize(
    ("post_json_data", "expected_post"),
    [  # All ratings must be mapped correctly
        pytest.param(
            {
                "komment_ID": "11833",
                "datum": "2004-05-13 00:04:06",
                "qual": src_rating,
                "kommentar": "Some comment",
                "username": "DonJ",
            },
            Post(
                user_name="DonJ",
                post_date=ANY,
                comment="Some comment",
                rating=dest_rating,
                source_label="Unit Test",
            ),
            id=f"rating='{src_rating}'",
        )
        for src_rating, dest_rating in (
            # Neutral ratings
            ("0", 0),
            ("3", 0),
            # Positive ratings
            ("1", 3),
            ("2", 2),
            # Negative ratings
            ("5", -3),
            ("4", -2),
        )
    ]
    + [
        pytest.param(
            {
                "komment_ID": "11833",
                "datum": "2004-05-13 00:04:06",
                "qual": "2",
                "kommentar": "Some other comment",
                "username": "Me",
            },
            Post(
                user_name="Me",
                post_date=datetime(2004, 5, 12, 22, 4, 6, tzinfo=UTC),
                comment="Some other comment",
                rating=2,
                source_label="Unit Test",
            ),
            id="correct timezone",
        ),
        pytest.param(
            {
                "komment_ID": "11833",
                "datum": "2004-05-13 00:04:06",
                "qual": "2",
                "additional_field": "API extension",
                "kommentar": "Yet another comment",
                "username": "You",
            },
            Post(
                user_name="You",
                post_date=ANY,
                comment="Yet another comment",
                rating=2,
                source_label="Unit Test",
            ),
            id="additional JSON field",
        ),
    ],
)
def test_import_post(
    post_json_data: dict[str, str],
    expected_post: Post,
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that all aspects of (valid) post data can be imported correctly:
     - Comment and user name are retrieved correctly (checked implicitly with other test cases)
     - Date is retrieved with the correct time zone information
     - All possible ratings are mapped correctly

    The 'post_json_data' input parameter is the (external) JSON representaion of the post being
    imported (the 'sektorid' and 'wegid' attributes are added automatically), the 'expected_post'
    parameter is the expected Post object.
    """
    post_json_data.update({"sektorid": "2", "wegid": "4"})
    minimal_data_sample["posts"] = [post_json_data]

    output_pipe = run_prepared_filter(minimal_data_sample)

    # There must be exactly one summit
    actual_summit_ids = [sid for sid, _s in output_pipe.iter_summits()]
    assert len(actual_summit_ids) == 1
    summit_id = actual_summit_ids[0]

    # There must be exactly one route for this summit
    actual_route_ids = [rid for rid, _r in output_pipe.iter_routes_of_summit(summit_id=summit_id)]
    assert len(actual_route_ids) == 1
    route_id = actual_route_ids[0]

    # There must be exactly one posts on this route
    actual_posts = list(output_pipe.iter_posts_of_route(route_id))
    assert len(actual_posts) == 1
    actual_post = actual_posts[0]
    assert actual_post.post_date == expected_post.post_date
    assert actual_post.comment == expected_post.comment
    assert actual_post.user_name == expected_post.user_name
    assert actual_post.rating == expected_post.rating


@pytest.mark.parametrize(
    "post_json_data",
    [
        pytest.param(
            {
                "komment_ID": "11833",
                "datum": "2004-05-13 18:25:18",
                "wegid": "0",
                "qual": "2",
                "kommentar": "Some comment",
                "username": "DonJ",
            },
            id="comment of summit",
        )
    ],
)
def test_ignore_post(
    post_json_data: dict[str, str],
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that posts with certain attributes are ignored:
     - Posts that are assigned to the summit (instead of a route)

    Input parameter is the (external) JSON representation of a single post that must be ignored.
    The 'sektorid' attribute added automatically by the test.
    """
    post_json_data.update({"sektorid": "2"})
    minimal_data_sample["posts"] = [post_json_data]

    output_pipe = run_prepared_filter(minimal_data_sample)

    # There must be exactly one summit
    actual_summit_ids = [sid for sid, _s in output_pipe.iter_summits()]
    assert len(actual_summit_ids) == 1
    summit_id = actual_summit_ids[0]

    # There must be exactly one route for this summit
    actual_route_ids = [rid for rid, _r in output_pipe.iter_routes_of_summit(summit_id=summit_id)]
    assert len(actual_route_ids) == 1
    route_id = actual_route_ids[0]

    # There must be no posts on this route
    assert not list(output_pipe.iter_posts_of_route(route_id))
