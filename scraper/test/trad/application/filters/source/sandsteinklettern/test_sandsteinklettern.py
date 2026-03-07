"""
Unit tests for the trad.applicaiton.filters.source.sandsteinklettern filter implementation.

The tests in this module use static test data from the JSON files in the same directory:
 - minimal_data_sample.json: A minimal data set containing a single route on a single summit.
 - full_data_sample.json: A more complex data set containing several sectors, summits, routes and
   posts.

TODO: Test Cases:
 - Error cases (exception)
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, cast, override
from unittest.mock import ANY, Mock

import pytest

from trad.application.boundaries.http import HttpNetworkingBoundary, JsonData
from trad.application.filters.source.sandsteinklettern.api import (
    JsonGipfelStatus,
    JsonGipfelTyp,
    JsonWegStatus,
)
from trad.application.filters.source.sandsteinklettern.filter import SandsteinkletternDataFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import GeoPosition, Post, Route, Summit

_AREAS_ENDPOINT: Final = "jsongebiet.php"
_SECTORS_ENDPOINT = "jsonteilgebiet.php"
_SUMMITS_ENDPOINT = "jsongipfel.php"
_ROUTES_ENDPOINT = "jsonwege.php"
_POSTS_ENDPOINT = "jsonkomment.php"


_EXPECTED_CONFLICT_RANK = 3
""" Conflict rank value the sandsteinklettern filter should set. """


def test_import_happy_path() -> None:
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
    dir_name = Path(__file__).parent
    sample_json = json.loads(dir_name.joinpath("full_data_sample.json").read_text(encoding="utf-8"))

    fake_network = _FakeNetwork()

    fake_network.add_json_response(
        _AREAS_ENDPOINT,
        required_url_param="land",
        response=sample_json["areas"],
    )
    fake_network.add_json_response(
        _SECTORS_ENDPOINT,
        required_url_param="gebietid",
        response=sample_json["sectors"],
    )
    fake_network.add_json_response(
        _SUMMITS_ENDPOINT,
        required_url_param="sektorid",
        response=sample_json["summits"],
    )
    fake_network.add_json_response(
        _ROUTES_ENDPOINT,
        required_url_param="sektorid",
        response=sample_json["routes"],
    )
    fake_network.add_json_response(
        _POSTS_ENDPOINT,
        required_url_param="sektorid",
        response=sample_json["posts"],
    )

    data_filter = SandsteinkletternDataFilter(fake_network)
    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

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
def test_external_sources(summit_count: int, *, expect_source_def: bool) -> None:
    """
    Ensure that an external source is added along with imported data:
     - The source definition must contain the correct data
     - There must be exactly one source (if data was added at all)
     - If no summit was added, the source must be omitted

    :param summit_count: The number of Summits being imported.
    :param expect_source_def: Whether an external source definition is expected to be added (True)
        or not (False).
    """
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["summits"] = [
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
    sample_json["routes"] = []
    sample_json["posts"] = []
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)

    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

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


_allowed_summit_types: Final = (JsonGipfelTyp.REGULAR, JsonGipfelTyp.CRAG)
_allowed_summit_status: Final = (
    JsonGipfelStatus.OPEN,
    JsonGipfelStatus.PARTIALLY_CLOSED,
    JsonGipfelStatus.OCCASIONALLY_CLOSED,
)


@pytest.mark.parametrize(
    ("summit_json_data", "expected_summit"),
    [  # All summit names must be respected
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                low_grade_position=GeoPosition.from_decimal_degree(50.89023, 14.04374),
            ),
            id="single name (german)",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "",
                "gipfelname_cz": "Mons Exempli",
                "status": "",
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                low_grade_position=GeoPosition.from_decimal_degree(50.89023, 14.04374),
            ),
            id="single name (czech)",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Einserturm (Zweierturm)",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Einserturm", "Zweierturm"],
                low_grade_position=GeoPosition.from_decimal_degree(50.89023, 14.04374),
            ),
            id="multiple names",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Schneekoppe",
                "gipfelname_cz": "Sněžka",
                "status": "",
                "typ": "G",
                "vgrd": "15.73965",
                "ngrd": "50.735989",
            },
            Summit(
                unspecified_names=["Schneekoppe", "Sněžka"],
                low_grade_position=GeoPosition.from_decimal_degree(50.735989, 15.73965),
            ),
            id="different languages",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Schneekoppe (Riesenkoppe)",
                "gipfelname_cz": "Sněžka (Śnieżka)",
                "status": "",
                "typ": "G",
                "vgrd": "15.73965",
                "ngrd": "50.735989",
            },
            Summit(
                unspecified_names=["Schneekoppe", "Riesenkoppe", "Sněžka", "Śnieżka"],
                low_grade_position=GeoPosition.from_decimal_degree(50.735989, 15.73965),
            ),
            id="multiple languages and names",
        ),
    ]
    + [  # All allowed summit types
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": typ.value,
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                low_grade_position=GeoPosition.from_decimal_degree(50.89023, 14.04374),
            ),
            id=f"typ={typ.value}",
        )
        for typ in _allowed_summit_types
    ]
    + [  # All allowed summit status
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": status.value,
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                low_grade_position=GeoPosition.from_decimal_degree(50.89023, 14.04374),
            ),
            id=f"status={status.value}",
        )
        for status in _allowed_summit_status
    ]
    + [  # Fix wrong summit names (only a single example)
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Zwergfels",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.1106220",
                "ngrd": "50.9013408",
            },
            Summit(
                unspecified_names=["Zwerg"],
                low_grade_position=GeoPosition.from_decimal_degree(50.9013408, 14.1106220),
            ),
            id="fix wrong name",
        )
    ]
    + [  # Ignore future API extensions
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Schneekoppe",
                "gipfelname_cz": "Sněžka",
                "status": "",
                "typ": "G",
                "new_attribute": "test",
                "vgrd": "15.73965",
                "ngrd": "50.735989",
            },
            Summit(
                unspecified_names=["Schneekoppe", "Sněžka"],
                low_grade_position=GeoPosition.from_decimal_degree(50.735989, 15.73965),
            ),
            id="additional JSON field",
        ),
    ],
)
def test_import_summit(summit_json_data: dict[str, str], expected_summit: Summit) -> None:
    """
    Ensure that all aspects of (valid) summit data can be imported correctly:
     - Summit names in different variants and combinations
     - All status value for at least sometimes accessible
     - "regular" and "crag" summit types
     - Summit position (tested implicitly with oter test cases, because coordinates are mandatory)
     - Certain summit names are known to be wrong in the external source, and thus must be fixed

    The 'summit_json_data' input parameter is the (external) JSON representaion of the summit being
    imported (the 'sektorid' attribute is added automatically), the 'expected_summit'
    parameter is the expected Summit object.
    """
    summit_json_data.update({"sektorid": "2"})
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["summits"] = [summit_json_data]
    sample_json["routes"] = []
    sample_json["posts"] = []
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)

    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

    # The resulting list must contain exactly one (the expected) Summit
    actual_summit_list = [summit for _id, summit in output_pipe.iter_summits()]
    assert len(actual_summit_list) == 1
    actual_summit = actual_summit_list[0]
    assert actual_summit.official_name == expected_summit.official_name
    assert sorted(actual_summit.alternate_names) == sorted(expected_summit.alternate_names)
    assert sorted(actual_summit.unspecified_names) == sorted(expected_summit.unspecified_names)
    assert actual_summit.high_grade_position.is_equal_to(expected_summit.high_grade_position)
    assert actual_summit.low_grade_position.is_equal_to(expected_summit.low_grade_position)


@pytest.mark.parametrize(
    "summit_json_data",
    [  # Ignore all summit types except "regular" and "crag"
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": typ.value,
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id=f"typ='{typ.value}'",
        )
        for typ in JsonGipfelTyp
        if typ not in _allowed_summit_types
    ]
    + [  # Ignore externally new (=unknown) summit types
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": "NEW_AND_UNKNOWN",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id="externally new 'typ'",
        )
    ]
    + [  # Ignore all summits that are not at least partially opened ("status")
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": status.value,
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id=f"status='{status.value}'",
        )
        for status in JsonGipfelStatus
        if status not in _allowed_summit_status
    ]
    + [  # Ignore externally new (=unknown) summit status
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "NEW_AND_UNKNOWN",
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id="externally new 'status'",
        )
    ]
    + [  # Ignore summits without any name
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id="no name",
        )
    ]
    + [  # Ignore summits with certain names
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": f"Übungsstelle {nr}",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id=f"name=Übungsstelle {nr}",
        )
        for nr in ("A", "B", "C")
    ],
)
def test_ignore_summit(summit_json_data: dict[str, str]) -> None:
    """
    Ensure that items with certain attributes must be ignored from the retrived summits list:
     - Most known summit types
     - Summits with a status that is not explicitly allowed
     - Summits that are never accessible
     - Summits whose name start with certain strings (no real summits that are not tagged separately
       in the external source)
     - Summits without a name
     - New summit types and status we don't know about (in case the external API is extended)

    Input parameter is the (external) JSON representation of s single summit that must be ignored.
    The 'sektorid' attribute is added automatically by the test.
    """
    summit_json_data.update({"sektorid": "2"})
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["summits"] = [summit_json_data]
    sample_json["routes"] = []
    sample_json["posts"] = []
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)

    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

    # The resulting list of Summits must be empty
    assert not list(output_pipe.iter_summits())


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
def test_import_route(route_json_data: dict[str, str], expected_route: Route) -> None:
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
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["routes"] = [route_json_data]
    sample_json["posts"] = []
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)
    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

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
def test_ignore_route(route_json_data: dict[str, str]) -> None:
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
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["routes"] = [route_json_data]
    sample_json["posts"] = []
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)

    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

    # There must be exactly one summit
    actual_summit_ids = [sid for sid, _s in output_pipe.iter_summits()]
    assert len(actual_summit_ids) == 1
    summit_id = actual_summit_ids[0]

    # There must be no route for this summit
    assert not list(output_pipe.iter_routes_of_summit(summit_id=summit_id))


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
def test_import_post(post_json_data: dict[str, str], expected_post: Post) -> None:
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
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["posts"] = [post_json_data]
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)

    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

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
def test_ignore_post(post_json_data: dict[str, str]) -> None:
    """
    Ensure that posts with certain attributes are ignored:
     - Posts that are assigned to the summit (instead of a route)

    Input parameter is the (external) JSON representation of a single post that must be ignored.
    The 'sektorid' attribute added automatically by the test.
    """
    post_json_data.update({"sektorid": "2"})
    sample_json = _load_prepared_test_data("minimal_data_sample.json")
    sample_json["posts"] = [post_json_data]
    fake_network = _create_fake_network(sample_json)

    data_filter = SandsteinkletternDataFilter(fake_network)

    output_pipe = CollectedData()
    data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)

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


_RawJsonData = list[dict[str, str]]
""" A single JSON data set that can be returned by the (fake) remote API). """

_JsonTestData = dict[Literal["areas", "sectors", "summits", "routes", "posts"], _RawJsonData]
""" The JSON data loaded from the prepared data files. """


def _load_prepared_test_data(data_file: str) -> _JsonTestData:
    """
    Load and return the prepared test JSON data from the given `data_file`.
    """
    dir_name = Path(__file__).parent
    return cast(_JsonTestData, json.loads(dir_name.joinpath(data_file).read_text(encoding="utf-8")))


def _create_fake_network(json_response_data: _JsonTestData) -> HttpNetworkingBoundary:
    """
    Returns a new, _FakeNetwork instance preconfigured to provide the given 'json_response_data'
    (which can be loaded from the prepared test data files).
    """
    fake_network = _FakeNetwork()
    fake_network.add_json_response(
        _AREAS_ENDPOINT,
        required_url_param="land",
        response=json_response_data["areas"],
    )
    fake_network.add_json_response(
        _SECTORS_ENDPOINT,
        required_url_param="gebietid",
        response=json_response_data["sectors"],
    )

    fake_network.add_json_response(
        _SUMMITS_ENDPOINT,
        required_url_param="sektorid",
        response=json_response_data["summits"],
    )
    fake_network.add_json_response(
        _ROUTES_ENDPOINT,
        required_url_param="sektorid",
        response=json_response_data["routes"],
    )
    fake_network.add_json_response(
        _POSTS_ENDPOINT,
        required_url_param="sektorid",
        response=json_response_data["posts"],
    )
    return fake_network


class _FakeNetwork(HttpNetworkingBoundary):
    """
    Fake networking component that doesn't do any real network requests but responds with
    pre-configured data.

    It also ensures some general request attributes, e.g. that no request contains any content, or
    that all requests contain the API key.
    """

    _EXPECTED_BASE_URL: Final = "http://db-sandsteinklettern.gipfelbuch.de/"
    """ The API URL expected to be requested. All other URL will cause an error. """

    def __init__(self) -> None:
        self._predefined_responses: dict[str, dict[str, _RawJsonData]] = {}

    def _ensure_url_parameters(self, url_params: dict[str, str | int]) -> None:
        """
        Ensure that the necessary API key is sent with the given request, along with other parameter
        conditions.
        """
        expected_parameter_count = 2

        assert url_params.get("app", "") == "trad"
        assert len(url_params) == expected_parameter_count

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        assert url.startswith(self._EXPECTED_BASE_URL)
        # Make sure that URL params are always provided and contain the API key
        assert url_params
        self._ensure_url_parameters(url_params)
        # Make sure no content is sent with requests
        assert not query_content

        predefined_responses = self._predefined_responses.get(url.split("/")[-1], None)
        assert predefined_responses is not None, f"Requesting an unexpected API end point '{url}'"

        del url_params["app"]
        url_param_key, url_param_value = next(iter(url_params.items()))
        responses = predefined_responses[url_param_key]
        return JsonData(
            json.dumps(
                [response for response in responses if response[url_param_key] == url_param_value]
            )
        )

    def add_json_response(
        self,
        api_endpoint: str,
        required_url_param: str,
        response: list[dict[str, str]],
    ) -> None:
        """
        Register the given `response` to be sent when `api_endpoint` is requested with the
        `required_url_param` URL parameter. Any previous registration for this request is replaced.
        """
        self._predefined_responses.setdefault(api_endpoint, {})[required_url_param] = response

    @override
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        # This method must not be called by the filter
        pytest.fail("Filter is not supposed to retrieve any text resources")
