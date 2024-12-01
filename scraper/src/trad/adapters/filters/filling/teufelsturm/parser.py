"""
Teufelsturm route page content parser.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd
from bs4 import BeautifulSoup

from trad.core.entities import Post, Route, Summit

if TYPE_CHECKING:
    from pandas.core.frame import DataFrame
    from pandas.core.series import Series

warnings.simplefilter(action="ignore", category=FutureWarning)


@dataclass
class PageData:
    peak: Summit
    route: Route
    posts: list[Post]


def parse_user_name(user_as_string: str) -> tuple[str, datetime]:
    result = re.search(r"^(.*?)((\|\|\|)|(\|.*?\|\|\|))(.*)$", user_as_string)
    if len(result.groups()) != 5:
        raise Exception("User name could not be parsed")

    user_name = result.group(1)
    post_date = datetime.strptime(result.group(5), "%d.%m.%Y %H:%M")

    return user_name, post_date


def parse_rating(rating_as_string: str) -> int:
    rating_map = {
        "--- (Kamikaze)": -3,
        "-- (sehr schlecht)": -2,
        "- (schlecht)": -1,
        "+++ (Herausragend)": 3,
        "++ (sehr gut)": 2,
        "+ (gut)": 1,
    }

    return rating_map.get(rating_as_string, 0)


def parse_posts(post_table: DataFrame) -> list[Post]:
    result = []
    for i in range(1, len(post_table)):
        result.append(parse_post(post_table.loc[i]))
    return result


def parse_post(post: Series[Any]) -> Post:
    user = parse_user_name(post[0])
    comment = post[1]
    rating = parse_rating(post[2])
    return Post(user_name=user[0], post_date=user[1], comment=comment, rating=rating)


def parse_page(page_text: str) -> PageData:
    soup = BeautifulSoup(page_text, "html.parser")

    title_result = re.search(r"(.*) - (.*)", soup.title.string)

    if len(title_result.groups()) != 2:
        raise Exception("Page has no valid title.")

    peak = title_result.group(1)
    route = title_result.group(2)

    paragraphs = soup.find("p").getText()
    grade_result = re.search(r".*?\[(.*?)\].*", paragraphs)
    if len(grade_result.groups()) != 1:
        raise Exception("Page has no valid grade.")

    grade = grade_result.group(1).strip()

    df_list = pd.read_html(
        page_text.replace("<br>", "|")
    )  # this parses all the tables in webpages to a list
    df = df_list[3]
    posts = parse_posts(df)
    return PageData(peak=Summit(name=peak), route=Route(route_name=route, grade=grade), posts=posts)
