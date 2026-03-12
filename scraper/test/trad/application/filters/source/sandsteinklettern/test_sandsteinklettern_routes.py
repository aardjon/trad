"""
Unit tests for the trad.application.filters.source.sandsteinklettern filter implementation testing
the processing of routes.

TODO: Test Cases:
 - Error cases (exception)
"""

from typing import Final

import pytest

from trad.application.filters.source.sandsteinklettern.api import JsonWegStatus
from trad.kernel.entities import Route

from .conftest import JsonTestData, PreparedFilterRunner

_allowed_route_status: Final = (JsonWegStatus.ACKNOWLEDGED, JsonWegStatus.TEMP_CLOSED)


@pytest.mark.parametrize(
    ("route_json_data", "expected_route"),
    [  # All respected route status values
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "V",
                "wegbeschr_d": "Some description",
                "wegname_d": "Musterweg",
                "wegname_cz": "",
                "wegstatus": status.value,
            },
            Route(conflict_rank=3, route_name="Musterweg", grade_af=5),
            id=f"status='{status.value}'",
        )
        for status in JsonWegStatus
        if status in _allowed_route_status
    ]
    + [  # status "0" is handled the same as "1"
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "V",
                "wegbeschr_d": "Some description",
                "wegname_d": "Musterweg",
                "wegname_cz": "",
                "wegstatus": "0",
            },
            Route(conflict_rank=3, route_name="Musterweg", grade_af=5),
            id="status='0'",
        )
    ]
    + [  # All grades and danger information must be retrieved
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "!3/V (VI) RP IV",
                "wegbeschr_d": "Some description",
                "wegname_d": "Schwierig...",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            Route(
                conflict_rank=3,
                route_name="Schwierig...",
                grade_jump=3,
                grade_af=5,
                grade_ou=6,
                grade_rp=4,
                dangerous=True,
                star_count=0,
            ),
            id="full grade information",
        )
    ]
    + [  # Stars are taken from the route name, not the grade
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "**VIIa",
                "wegbeschr_d": "Some description",
                "wegname_d": "Testing",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            Route(
                conflict_rank=3,
                route_name="Testing",
                grade_af=7,
                star_count=0,
            ),
            id="ignore grade stars",
        ),
        pytest.param(
            {
                "weg_ID": "123",
                "gipfelid": "13",
                "schwierigkeit": "VIIa",
                "wegbeschr_d": "Some description",
                "wegname_d": "*Testing",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            Route(
                conflict_rank=3,
                route_name="Testing",
                grade_af=7,
                star_count=1,
            ),
            id="use stars from name: 1",
        ),
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "VIIa",
                "wegbeschr_d": "Some description",
                "wegname_d": "**Testing",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            Route(
                conflict_rank=3,
                route_name="Testing",
                grade_af=7,
                star_count=2,
            ),
            id="use stars from name: 2",
        ),
    ]
    + [  # Invalid grade
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "//",
                "wegbeschr_d": "Some description",
                "wegname_d": "Test Route",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            Route(
                conflict_rank=3,
                route_name="Test Route",
            ),
            id="invalid grade",
        ),
    ]
    + [  # Ignore future API extensions
        pytest.param(
            {
                "weg_ID": "123",
                "schwierigkeit": "//",
                "wegbeschr_d": "Some description",
                "wegname_d": "Test Route",
                "unknown_field": "This is new!",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            Route(
                conflict_rank=3,
                route_name="Test Route",
            ),
            id="additional JSON field",
        ),
    ],
)
def test_import_route(
    route_json_data: dict[str, str],
    expected_route: Route,
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that all aspects of (valid) route data can be imported correctly:
     - All official routes that can (by their status) be accessed sometimes
     - Route name
     - All grade information (complete or partially)
     - Invalid grade information
     - Stars and danger marks
     - All route data has conflict rank 3 (tested implicitly because it is mandatory)

    The 'route_json_data' input parameter is the (external) JSON representaion of the route being
    imported (the 'sektorid' attribute is added automatically), the 'expected_route'
    parameter is the expected Route object.
    """
    route_json_data.update({"sektorid": "2", "gipfelid": "3"})
    minimal_data_sample["routes"] = [route_json_data]
    minimal_data_sample["posts"] = []

    output_pipe = run_prepared_filter(minimal_data_sample)

    # There must be exactly one summit
    actual_summit_ids = [sid for sid, _s in output_pipe.iter_summits()]
    assert len(actual_summit_ids) == 1
    summit_id = actual_summit_ids[0]

    # There must be exactly one (the expected) route
    actual_routes = [r for _rid, r in output_pipe.iter_routes_of_summit(summit_id=summit_id)]
    assert len(actual_routes) == 1
    route = actual_routes[0]

    assert route.route_name == expected_route.route_name
    assert route.grade_jump == expected_route.grade_jump
    assert route.grade_af == expected_route.grade_af
    assert route.grade_ou == expected_route.grade_ou
    assert route.grade_rp == expected_route.grade_rp
    assert route.star_count == expected_route.star_count
    assert route.dangerous == expected_route.dangerous


@pytest.mark.parametrize(
    "route_json_data",
    [  # Ignore all routes (by status) except the officially allowed ones
        pytest.param(
            {
                "weg_ID": "123",
                "gipfelid": "13",
                "schwierigkeit": "V",
                "wegbeschr_d": "Some description",
                "wegname_d": "Musterweg",
                "wegname_cz": "",
                "wegstatus": status.value,
            },
            id=f"status='{status.value}'",
        )
        for status in JsonWegStatus
        if status not in _allowed_route_status
    ]
    + [  # Ignore routes with a new, unknown status value
        pytest.param(
            {
                "weg_ID": "123",
                "gipfelid": "13",
                "schwierigkeit": "V",
                "wegbeschr_d": "Some description",
                "wegname_d": "Musterweg",
                "wegname_cz": "",
                "wegstatus": "NEW_AND_UNKNOWN",
            },
            id="new/unknown status",
        )
        for status in JsonWegStatus
        if status not in _allowed_route_status
    ]
    + [  # Ignore routes without a name
        pytest.param(
            {
                "weg_ID": "123",
                "gipfelid": "13",
                "schwierigkeit": "V",
                "wegbeschr_d": "Some description",
                "wegname_d": "",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            id="no name",
        )
    ]
    + [  # Always ignore certain routes because they are somehow wrong on external site
        pytest.param(
            {
                "weg_ID": "77482",
                "gipfelid": "13",
                "schwierigkeit": "V",
                "wegbeschr_d": "Some description",
                "wegname_d": "CAPTION:",
                "wegname_cz": "",
                "wegstatus": "1",
            },
            id="hard coded ignore list",
        )
    ],
)
def test_ignore_route(
    route_json_data: dict[str, str],
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that routes with certain attributes are ignored:
     - Routes that are closed completely and unconditionally
     - Routes that are not officially approved
     - Routes with a new status value we don't know about (because the external API was extended)
     - Routes without a name
     - Routes which are somehow wrong in the external source and must therefore not be included

    Input parameter is the (external) JSON representation of a single route that must be ignored.
    The 'sektorid' attribute is added automatically by the test.
    """
    route_json_data.update({"sektorid": "2", "gipfelid": "3"})
    minimal_data_sample["routes"] = [route_json_data]
    minimal_data_sample["posts"] = []

    output_pipe = run_prepared_filter(minimal_data_sample)

    # There must be exactly one summit
    actual_summit_ids = [sid for sid, _s in output_pipe.iter_summits()]
    assert len(actual_summit_ids) == 1
    summit_id = actual_summit_ids[0]

    # There must be no route for this summit
    assert not list(output_pipe.iter_routes_of_summit(summit_id=summit_id))
