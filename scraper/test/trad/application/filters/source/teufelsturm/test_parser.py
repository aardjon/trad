"""
Unit tests for the trad.application.filters.source.teufelsturm.parser module.
"""

import datetime
from pathlib import Path
from typing import Final

import pandas as pd
import pytest
import pytz

from trad.application.filters.source.teufelsturm.parser import (
    SummitCache,
    parse_page,
    parse_post,
    parse_posts,
    parse_rating,
    parse_route_list,
    parse_user_name,
)
from trad.infrastructure.grade_regex import RegexBasedParser
from trad.kernel.entities import UNDEFINED_GEOPOSITION, GeoPosition, Post

posts_test_dict: Final = {
    0: {
        0: "Benutzer",
        1: "Ruth Madden|Wohnort: Zioncester|||23.11.2023 14:12",
        2: "Brenda Hutchinson|||04.07.2021 09:27",
        3: "Kenneth Mcintyre|Authentifizierter Benutzer|Wohnort: auf Asylsuche|||03.11.2018 16:31",
        4: "Abraham Castro|Wohnort: Abilene|||18.05.2009 11:54",
        5: "Carter Perez|||02.04.2008 20:47",
        6: "Althea Goodwin|Authentifizierter Benutzer|Wohnort: West Zolaville|||08.02.2008 11:10",
        7: "Wing William|Authentifizierter Benutzer|||30.10.2007 12:21",
        8: "Alice Chaney|Moderator|Authentifizierter Benutzer|||22.11.2007 15:04",
        9: "Kay Säller|Authentifizierter Benutzer|Wohnort: North Gracie|||27.05.2001 19:07",
        10: "Anthony Calhoun|||22.04.2001 11:22",
        11: "Claire Cline|Authentifizierter Benutzer|||24.04.2001 14:32",
        12: "Kuame Vinson|Co-Administrator|Authentifizierter Benutzer|||25.01.2001 13:43",
        13: "Ebony Edwards|Webmaster|Authentifizierter Benutzer|Wohnort: Fort Kallie|||02.10.2000 19:13",
        14: "Yeo Lambert|Authentifizierter Benutzer|Wohnort: http://example.com|||23.08.2000 15:01",
    },
    1: {
        0: "Kommentar",
        1: "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam.",
        2: "Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et.",
        3: "Sed ut perspiciatis unde omnis.",
        4: "Natus error sit voluptatem accusantium doloremque laudantium, totam rem.",
        5: "Li Europan lingues es membres del sam familie. Lor separat existentie es un myth.",
        6: "Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur?",
        7: "Et harum quidem rerum facilis est et expedita distinctio.",
        8: "Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere.",
        9: "In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo.",
        10: "Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur.",
        11: "Vel illum qui dolorem eum fugiat quo voluptas nulla pariatur.",
        12: "Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi.",
        13: "Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo.",
        14: "Sed consequat, leo eget bibendum sodales, augue velit cursus nunc.",
    },
    2: {
        0: "Bewertung",
        1: "(Normal)",
        2: "+++ (Herausragend)",
        3: "+ (gut)",
        4: "+++ (Herausragend)",
        5: "++ (sehr gut)",
        6: "(Normal)",
        7: "++ (sehr gut)",
        8: "++ (sehr gut)",
        9: "++ (sehr gut)",
        10: "++ (sehr gut)",
        11: "+ (gut)",
        12: "+++ (Herausragend)",
        13: "+++ (Herausragend)",
        14: "+++ (Herausragend)",
    },
}

timezone_berlin: Final = pytz.timezone("Europe/Berlin")


def test_parse_post() -> None:
    raw_data_index: Final = 2
    user_column_content = posts_test_dict[0][raw_data_index]
    expected_result_post = Post(
        user_name=user_column_content.split("|", maxsplit=1)[0],
        post_date=timezone_berlin.localize(
            datetime.datetime.strptime(
                user_column_content.rsplit("|", maxsplit=1)[-1],
                "%d.%m.%Y %H:%M",
            )
        ),
        comment=posts_test_dict[1][raw_data_index],
        rating=posts_test_dict[2][raw_data_index].count("+"),
    )
    posts_table = pd.DataFrame.from_dict(posts_test_dict)

    post = parse_post(posts_table.loc[2])

    assert post == expected_result_post


def test_parse_posts() -> None:
    expected_results = [
        Post(
            user_name=posts_test_dict[0][i].split("|")[0],
            post_date=timezone_berlin.localize(
                datetime.datetime.strptime(posts_test_dict[0][i].split("|")[-1], "%d.%m.%Y %H:%M")
            ),
            comment=posts_test_dict[1][i],
            rating=posts_test_dict[2][i].count("+"),
        )
        for i in range(1, len(posts_test_dict[0]))
    ]
    posts_table = pd.DataFrame.from_dict(posts_test_dict)

    # Parse post table
    results = parse_posts(posts_table)

    assert len(results) == len(expected_results)
    assert results == expected_results


@pytest.mark.parametrize(
    ("rating_text", "expected_rating"),
    [
        ("--- (Kamikaze)", -3),
        ("-- (sehr schlecht)", -2),
        ("- (schlecht)", -1),
        ("(Normal)", 0),
        ("+ (gut)", 1),
        ("++ (sehr gut)", 2),
        ("+++ (Herausragend)", 3),
    ],
)
def test_parse_rating(rating_text: str, expected_rating: int) -> None:
    assert parse_rating(rating_text) == expected_rating


@pytest.mark.parametrize(
    "input_text",
    [
        "Ruth Madden|Wohnort: Zioncester|||23.11.2023 14:12",
        "Brenda Hutchinson|||04.07.2021 09:27",
        "Kenneth Mcintyre|Authentifizierter Benutzer|Wohnort: auf Asylsuche|||03.11.2018 16:31",
        "Abraham Castro|Wohnort: Abilene|||18.05.2009 11:54",
        "Carter Perez|||02.04.2008 20:47",
        "Althea Goodwin|Authentifizierter Benutzer|Wohnort: West Zolaville|||08.02.2008 11:10",
        "Wing William|Authentifizierter Benutzer|||30.10.2007 12:21",
        "Alice Chaney|Moderator|Authentifizierter Benutzer|||22.11.2007 15:04",
        "Kay Säller|Authentifizierter Benutzer|Wohnort: North Gracie|||27.05.2001 19:07",
        "Anthony Calhoun|||22.04.2001 11:22",
        "Claire Cline|Authentifizierter Benutzer|||24.04.2001 14:32",
        "Kuame Vinson|Co-Administrator|Authentifizierter Benutzer|||25.01.2001 13:43",
        "Ebony Edwards|Webmaster|Authentifizierter Benutzer|Wohnort: Fort Kallie|||02.10.2000 19:13",
        "Yeo Lambert|Authentifizierter Benutzer|Wohnort: http://example.com|||23.08.2000 15:01",
    ],
)
def test_parse_user(input_text: str) -> None:
    expected_name = input_text.split("|")[0]
    expected_date = input_text.split("|")[-1]

    parsed_name, parsed_date = parse_user_name(input_text)

    assert parsed_name == expected_name
    assert f"{parsed_date:%d.%m.%Y %H:%M}" == expected_date


@pytest.mark.parametrize(
    "sample_route_page_file",
    ["route_page_sample_simple.html", "route_page_sample_extended.html"],
)
def test_parse_page(sample_route_page_file: str) -> None:
    """
    Tests that the HTML page parser returns the expected (hard coded) results from the example
    files. The difference between the "simple" and the "extended" route page file is, that the
    "extended" variant contains additional information (e.g. "Erstbegeher") and therefore has a
    slightly different DOM structure.
    """
    # The summit ID value is taken from the route_page_sample.html file
    expected_summit_id: Final = 42
    # Summit data (name and position) must be taken from the summit_details_page_sample.html file
    expected_summit_name: Final = "Beispielwand"
    expected_summit_position: Final = GeoPosition.from_decimal_degree(50.95105, 14.06769)

    def mocked_retrieve_summit_details_page(peak_id: int) -> str:
        assert peak_id == expected_summit_id
        with dir_name.joinpath("summit_details_page_sample.html").open(
            "rt", encoding="iso-8859-1"
        ) as file:
            return file.read()

    summit_cache = SummitCache(mocked_retrieve_summit_details_page)

    dir_name = Path(__file__).parent
    with dir_name.joinpath(sample_route_page_file).open("rt", encoding="iso-8859-1") as file:
        page_text = file.read()
    page_data = parse_page(page_text, summit_cache, RegexBasedParser())

    assert page_data.peak.name == expected_summit_name
    assert page_data.peak.high_grade_position is UNDEFINED_GEOPOSITION
    assert page_data.peak.low_grade_position.is_equal_to(expected_summit_position)
    assert page_data.route.route_name == "Loremweg"
    assert page_data.route.grade == "** II"
    assert len(page_data.posts) == 1
    assert page_data.posts[0].user_name == "Max Mustermann"
    assert page_data.posts[0].comment.startswith("Lorem ipsum")
    assert page_data.posts[0].rating == 0


def test_parse_route_list() -> None:
    """
    Ensures that the route IDs are extracted correctly from the route list HTML page.
    """
    dir_name = Path(__file__).parent
    page_text = dir_name.joinpath("route_list_sample.html").read_text(encoding="iso-8859-1")
    route_ids = parse_route_list(page_text)

    expected_route_ids = {
        13336,
        13583,
        277,
        11524,
        6118,
        13582,
        3293,
        11040,
        8361,
        3143,
    }
    assert route_ids == expected_route_ids
