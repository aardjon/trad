"""
Unit tests for the trad.application.filters.regular.merge module merging Routes.
"""

from typing import Any, Final

import pytest

from trad.application.filters.regular.merge import (
    MergeFilter,
)
from trad.application.pipes import CollectedData
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import Route, RouteDirections, RouteRating, Summit
from trad.kernel.errors import MergeConflictError

# Not using the DataFactory in this test because for merging, we often want control over the ranks


def _create_position(lat: int, lon: int, rank: int) -> RankedValue[GeoPosition]:
    return RankedValue.create_valid(GeoPosition(lat, lon), rank)


def _create_rating(rank: int, *args: Any, **kwargs: Any) -> RankedValue[RouteRating]:
    return RankedValue.create_valid(
        RouteRating(*args, **kwargs),
        rank,
    )


@pytest.mark.parametrize(
    ("input_routes", "expected_output_routes"),
    [
        pytest.param(
            [
                [
                    Route("AW", rating=_create_rating(1, star_count=1)),
                    Route("Talweg"),
                ],
                [
                    Route("AW"),
                    Route("SO-Rinne", rating=_create_rating(1, star_count=2)),
                ],
            ],
            [
                Route("AW", rating=_create_rating(1, star_count=1)),
                Route("Talweg"),
                Route("SO-Rinne", rating=_create_rating(1, star_count=2)),
            ],
            id="Merge only some of many routes",
        ),
        pytest.param(
            [
                [
                    Route("Bergweg", rating=_create_rating(1, star_count=1)),
                    Route("Talweg"),
                ],
            ],
            [
                Route("Bergweg", rating=_create_rating(1, star_count=1)),
                Route("Talweg"),
            ],
            id="Don't merge different routes on the same Summit",
        ),
        pytest.param(
            [
                [
                    Route("AW", rating=_create_rating(1, star_count=1)),
                    Route("AW", rating=_create_rating(1, star_count=1)),
                ],
            ],
            [
                Route("AW", rating=_create_rating(1, star_count=1)),
            ],
            id="Merge equal routes on one Summit (single instance)",
        ),
        pytest.param(
            [
                [
                    Route("AW", rating=_create_rating(1, star_count=1)),
                    Route("AW", rating=_create_rating(1, star_count=1)),
                ],
                [Route("AW", rating=_create_rating(rank=2))],
            ],
            [
                Route("AW", rating=_create_rating(1, star_count=1)),
            ],
            id="Merge equal routes on one Summit (multiple instances)",
        ),
        pytest.param(
            [
                [
                    Route("AW", rating=_create_rating(1, star_count=1)),
                    Route("AW", rating=_create_rating(1, star_count=1)),
                ],
                [Route("AW", rating=_create_rating(2))],
                [Route("AW", rating=_create_rating(2))],
            ],
            [
                Route("AW", rating=_create_rating(1, star_count=1)),
            ],
            id="Merge equal Routes on two Summits",
        ),
        pytest.param(
            [
                [
                    Route("AW", rating=_create_rating(1, star_count=1)),
                ],
                [Route("AW", rating=_create_rating(2))],
                [Route("AW", rating=_create_rating(2))],
            ],
            [
                Route("AW", rating=_create_rating(1, star_count=1)),
            ],
            id="Merge multiple equal Routes from one second Summit",
        ),
    ],
)
def test_merge_multiple_routes_per_summit(
    input_routes: list[list[Route]], expected_output_routes: list[Route]
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


def test_dont_merge_routes_of_different_summits() -> None:
    """
    Ensure that two routes with the same name and data on different physical summits (=Summit
    instances with different names) are not merged.
    """
    route1 = Route(
        "AW",
        rating=_create_rating(
            1,
            grade_af=1,
            grade_ou=2,
            grade_rp=3,
            grade_jump=0,
            star_count=1,
            dangerous=False,
        ),
    )
    route2 = Route(
        "AW",
        rating=_create_rating(
            1,
            grade_af=1,
            grade_ou=2,
            grade_rp=3,
            grade_jump=0,
            star_count=1,
            dangerous=False,
        ),
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
            Route("Talweg", rating=_create_rating(1, grade_af=3)),
            Route("Bergweg", rating=_create_rating(1, grade_af=3)),
            False,
            id="Different names (same af and rank)",
        ),
        pytest.param(
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=5,
                ),
            ),
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=5,
                ),
            ),
            True,
            id="Same name, same af, same rank",
        ),
        pytest.param(
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=5,
                ),
            ),
            Route(
                "AW",
                rating=_create_rating(
                    2,
                    grade_af=5,
                ),
            ),
            True,
            id="Same name, same af, different rank",
        ),
        pytest.param(
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=5,
                ),
            ),
            Route(
                "AW",
                rating=_create_rating(
                    2,
                    grade_af=6,
                ),
            ),
            True,
            id="Same name, different af, different rank",
        ),
        pytest.param(
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=5,
                ),
            ),
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=6,
                ),
            ),
            False,
            id="Same name, different af, same rank",
        ),
        pytest.param(
            Route(
                "AW",
                directions=[RouteDirections("Example1", "Source 2")],
                rating=_create_rating(
                    1,
                    grade_af=4,
                    grade_ou=5,
                    grade_rp=6,
                    grade_jump=1,
                    star_count=2,
                    dangerous=True,
                ),
            ),
            Route(
                "AW",
                directions=[RouteDirections("Example2", "Source 3")],
                rating=_create_rating(
                    2,
                    grade_af=4,
                    grade_ou=3,
                    grade_rp=2,
                    grade_jump=5,
                    star_count=1,
                    dangerous=False,
                ),
            ),
            True,
            id="Other data differs",
        ),
        pytest.param(
            Route("alter weg"),
            Route("Alter Weg"),
            True,
            id="Name Normalization: Case-insensitivity",
        ),
        pytest.param(
            Route("Alter Weg"),
            Route("Weg, Alter"),
            True,
            id="Name Normalization: Permutation",
        ),
        pytest.param(
            Route("Spieglein, Spieglein?"),
            Route("Spieglein Spieglein"),
            True,
            id="Name Normalization: Punctuation",
        ),
    ]
    + [
        pytest.param(
            Route(abbr),
            Route(fullname),
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
    ]
    + [
        pytest.param(
            Route(name1),
            Route(name2),
            True,
            id=f"Umlauts: '{name1}'=='{name2}'",
        )
        for name1, name2 in (
            ("Ostriss", "Ostriß"),
            ("Übers Gewölbe", "Uebers Gewoelbe"),
            ("ÄÖÜ", "AEOEUE"),
            ("äöü", "aeoeue"),
        )
    ]
    + [
        pytest.param(
            Route("S-Riß"),
            Route("südriss"),
            True,
            id="Combination: 'S-Riß'=='südriss'",
        )
    ],
)
def test_merge_routes_equality_check(
    input_route1: Route,
    input_route2: Route,
    *,
    expect_merge: bool,
) -> None:
    """
    Ensures that testing if several Route objects are actually the same physical route works as
    expected. For this test, all given Route objects are from different Summit instances.

    Whether two routes are actually "the same" is determined by their (normalized) name, the "af"
    grade and its rank.
    - If the names differ, they are not equal
    - For same names:
        - If the 'af' grades are equal, they are equal regardless of its rank
        - If the 'af' grades differ but the ranks are different, they are equal
    - Names are normalized before comparing, eliminating:
        - Common abbreviations ("NW")
        - Slightly different spellings (e.g. lower-/uppercase, punctuation)
        - Permutations
        - Umlauts (ä, ß)
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
    output_routes = [route for _id, route in output_pipe.iter_routes_of_summit(output_summit_id)]
    assert len(output_routes) == 1 if expect_merge else 2


@pytest.mark.parametrize(
    ("input_routes", "expected_output_route"),
    [
        pytest.param(
            [
                Route("AW", rating=_create_rating(2, grade_af=9)),
                Route(
                    "AW",
                    rating=_create_rating(
                        1,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                ),
            ],
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                ),
            ),
            id="Ratings: Missing on lower rank (lower first)",
        ),
        pytest.param(
            [
                Route(
                    "AW",
                    rating=_create_rating(
                        1,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                ),
                Route(
                    "AW",
                    rating=_create_rating(2, grade_af=9),
                ),
            ],
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                ),
            ),
            id="Ratings: Missing on lower rank (higher first)",
        ),
        pytest.param(
            [
                Route(
                    "AW",
                    rating=_create_rating(
                        2,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                ),
                Route("AW"),
            ],
            Route(
                "AW",
                rating=_create_rating(
                    2,
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                ),
            ),
            id="Ratings: Null value (second)",
        ),
        pytest.param(
            [
                Route("AW"),
                Route(
                    "AW",
                    rating=_create_rating(
                        2,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                ),
            ],
            Route(
                "AW",
                rating=_create_rating(
                    2,
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                ),
            ),
            id="Ratings: Null value (first)",
        ),
        pytest.param(
            [
                Route(
                    "AW",
                    rating=_create_rating(
                        1,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                )
            ]
            * 2,
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                ),
            ),
            id="Ratings: Equal data, same ranks",
        ),
        pytest.param(
            [
                Route(
                    "AW",
                    rating=_create_rating(
                        1,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                ),
                Route(
                    "AW",
                    rating=_create_rating(
                        2,
                        grade_af=9,
                        grade_ou=8,
                        grade_rp=7,
                        grade_jump=6,
                        star_count=0,
                        dangerous=True,
                    ),
                ),
            ],
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_af=9,
                    grade_ou=8,
                    grade_rp=7,
                    grade_jump=6,
                    star_count=0,
                    dangerous=True,
                ),
            ),
            id="Ratings: Equal data, different ranks",
        ),
        pytest.param(
            [
                Route(
                    "My Route",
                    rating=_create_rating(
                        1,
                        grade_jump=1,
                        grade_af=2,
                        grade_ou=3,
                        grade_rp=4,
                        dangerous=True,
                        star_count=1,
                    ),
                ),
                Route(
                    "My Route",
                    rating=_create_rating(
                        2,
                        grade_jump=4,
                        grade_af=3,
                        grade_ou=2,
                        grade_rp=1,
                        dangerous=False,
                        star_count=2,
                    ),
                ),
            ],
            Route(
                "My Route",
                rating=_create_rating(
                    1,
                    grade_jump=1,
                    grade_af=2,
                    grade_ou=3,
                    grade_rp=4,
                    dangerous=True,
                    star_count=1,
                ),
            ),
            id="Ratings: Conflicting data, different ranks #1",
        ),
        pytest.param(
            [
                Route(
                    "My Route",
                    rating=_create_rating(
                        2,
                        grade_jump=1,
                        grade_af=2,
                        grade_ou=3,
                        grade_rp=4,
                        dangerous=True,
                        star_count=1,
                    ),
                ),
                Route(
                    "My Route",
                    rating=_create_rating(
                        1,
                        grade_jump=4,
                        grade_af=3,
                        grade_ou=2,
                        grade_rp=1,
                        dangerous=False,
                        star_count=2,
                    ),
                ),
            ],
            Route(
                "My Route",
                rating=_create_rating(
                    1,
                    grade_jump=4,
                    grade_af=3,
                    grade_ou=2,
                    grade_rp=1,
                    dangerous=False,
                    star_count=2,
                ),
            ),
            id="Ratings: Conflicting data, different ranks #2",
        ),
        pytest.param(
            [
                Route("AW"),
                Route("AW", directions=[RouteDirections("Dummy Text", "Test")]),
            ],
            Route(
                "AW",
                directions=[RouteDirections("Dummy Text", "Test")],
            ),
            id="Directions: First value empty",
        ),
        pytest.param(
            [
                Route("AW", directions=[RouteDirections("Dummy Text", "Test")]),
                Route("AW"),
            ],
            Route("AW", directions=[RouteDirections("Dummy Text", "Test")]),
            id="Directions: Second value empty",
        ),
        pytest.param(
            [
                Route("AW", directions=[RouteDirections("Dummy Text 1", "Source 1")]),
                Route("AW", directions=[RouteDirections("Dummy Text 2", "Source 2")]),
            ],
            Route(
                "AW",
                directions=[
                    RouteDirections("Dummy Text 1", "Source 1"),
                    RouteDirections("Dummy Text 2", "Source 2"),
                ],
            ),
            id="Directions: Merge multiple directions",
        ),
        pytest.param(
            [
                Route("AW"),
                Route("AW", entry_position=_create_position(1000000, 2000000, 1)),
            ],
            Route(
                "AW",
                entry_position=_create_position(1000000, 2000000, 1),
            ),
            id="Position: First value missing",
        ),
        pytest.param(
            [
                Route("AW", entry_position=_create_position(1000000, 2000000, 1)),
                Route("AW"),
            ],
            Route("AW", entry_position=_create_position(1000000, 2000000, 1)),
            id="Position: Second value missing",
        ),
        pytest.param(
            [
                Route("AW"),
                Route("AW", rating=_create_rating(1, grade_ou=1)),
                Route("AW"),
            ],
            Route(
                "AW",
                rating=_create_rating(
                    1,
                    grade_ou=1,
                ),
            ),
            id="More than two instances",
        ),
    ],
)
def test_merge_routes_data_transfer(
    input_routes: list[Route], expected_output_route: Route
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
    output_route: Route = output_routes[0]

    assert output_route.route_name == expected_output_route.route_name
    assert output_route.directions == expected_output_route.directions

    assert output_route.rating.is_null() == output_route.rating.is_null()
    assert output_route.rating.rank == output_route.rating.rank
    if not output_route.rating.is_null():
        assert output_route.rating.value == expected_output_route.rating.value

    assert output_route.entry_position.is_null() == output_route.entry_position.is_null()
    assert output_route.entry_position.rank == output_route.entry_position.rank
    if not output_route.entry_position.is_null():
        assert output_route.entry_position.value.is_equal_to(
            expected_output_route.entry_position.value
        )


@pytest.mark.parametrize(
    ("input_routes", "expected_error"),
    [
        pytest.param(
            [
                Route("AW", rating=_create_rating(1, grade_ou=4)),
                Route("AW", rating=_create_rating(1, grade_rp=2)),
            ],
            MergeConflictError,
            id="Conflicting ou/rp grade",
        ),
        pytest.param(
            [
                Route("AW", rating=_create_rating(1, star_count=2)),
                Route("AW", rating=_create_rating(1, star_count=1)),
            ],
            MergeConflictError,
            id="Conflicting star count",
        ),
        pytest.param(
            [
                Route("AW", entry_position=_create_position(1000000, 2000000, 3)),
                Route("AW", entry_position=_create_position(2000000, 1000000, 3)),
            ],
            MergeConflictError,
            id="Conflicting entry position",
        ),
    ],
)
def test_route_merge_conflict(input_routes: list[Route], expected_error: type[Exception]) -> None:
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
