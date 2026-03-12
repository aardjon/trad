"""
Unit tests for the trad.application.filters.source.sandsteinklettern filter implementation testing
common/crosscutting usecases. It also provides some commonly used tools and definitions.

TODO: Test Cases:
 - Error cases (exception)
"""

import pytest

from .conftest import JsonTestData, PreparedFilterRunner


def test_import_happy_path(
    full_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Test importing a real-world like data set with several areas and sectors that contain several
    summits, routes and posts. The used sample JSON file contains the following cases:
     - Multiple areas (only one of them being used)
     - Multiple sectors, summits, routes and posts (all must be imported)
     - A sector that is not imported but contains a summit (which must be ignored)
     - Multiple sectors, summits, routes and posts that are not used because their parent is ignored
     - Sector without any summits (e.g. sector 24 "Affensteine")
     - Summit without any routes (e.g. summit 3)
     - Route without any posts (e.g. route 2)
    """
    output_pipe = run_prepared_filter(full_data_sample)

    retrieved_summit_names: list[str] = []
    retrieved_route_names: list[str] = []
    retrieved_post_authors: list[str] = []

    for summit_id, summit in output_pipe.iter_summits():
        retrieved_summit_names.append(summit.name)
        for route_id, route in output_pipe.iter_routes_of_summit(summit_id):
            retrieved_route_names.append(route.route_name)
            retrieved_post_authors.extend(
                post.user_name for post in output_pipe.iter_posts_of_route(route_id)
            )

    assert sorted(retrieved_summit_names) == [f"Summit {n}" for n in range(1, 5)]
    assert sorted(retrieved_route_names) == [f"Route {n}" for n in range(1, 7)]
    assert sorted(retrieved_post_authors) == [f"Author {n}" for n in range(1, 8)]


@pytest.mark.parametrize(
    ("summit_count", "expect_source_def"),
    [
        (1, True),
        (3, True),
        (0, False),
    ],
)
def test_external_sources(
    summit_count: int,
    *,
    expect_source_def: bool,
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that an external source is added along with imported data:
     - The source definition must contain the correct data
     - There must be exactly one source (if data was added at all)
     - If no summit was added, the source must be omitted

    :param summit_count: The number of Summits being imported.
    :param expect_source_def: Whether an external source definition is expected to be added (True)
        or not (False).
    """
    minimal_data_sample["summits"] = [
        {
            "sektorid": "2",
            "gipfel_ID": str(i),
            "gipfelname_d": f"Summit{i}",
            "gipfelname_cz": "",
            "status": "",
            "typ": "G",
            "vgrd": "14.04544",
            "ngrd": "50.84041",
        }
        for i in range(summit_count)
    ]
    minimal_data_sample["routes"] = []
    minimal_data_sample["posts"] = []

    output_pipe = run_prepared_filter(minimal_data_sample)

    # The resulting Pipe must contain either one external source definition or none at all
    actual_sources = list(output_pipe.get_sources())
    if expect_source_def:
        assert len(actual_sources) == 1
        assert actual_sources[0].label == "Sandsteinklettern"
        assert actual_sources[0].url == "http://sandsteinklettern.de"
        assert actual_sources[0].attribution == "Jörg Brutscher"
        assert actual_sources[0].license_name is None
    else:
        assert not actual_sources
