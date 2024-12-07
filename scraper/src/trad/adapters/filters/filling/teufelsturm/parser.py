"""
Teufelsturm route page content parser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING, Any, Final

import pandas as pd
import pytz
from bs4 import BeautifulSoup

from trad.core.entities import Post, Route, Summit
from trad.core.errors import DataProcessingError

if TYPE_CHECKING:
    from pandas.core.frame import DataFrame
    from pandas.core.series import Series


@dataclass
class PageData:
    """Parsed content of a single route page."""

    peak: Summit
    """ The summit this route belongs to. """
    route: Route
    """ The route. """
    posts: list[Post]
    """ All posts for this route. """


def parse_user_name(user_as_string: str) -> tuple[str, datetime]:
    """
    Parses a posts header data, returning the user name and the posting date.
    """
    timezone_berlin: Final = pytz.timezone("Europe/Berlin")
    header_field_count: Final = 5
    result = re.search(r"^(.*?)((\|\|\|)|(\|.*?\|\|\|))(.*)$", user_as_string)
    if not result or len(result.groups()) != header_field_count:
        raise DataProcessingError("User name could not be parsed")

    user_name = result.group(1)
    post_date = timezone_berlin.localize(datetime.strptime(result.group(5), "%d.%m.%Y %H:%M"))

    return user_name, post_date


def parse_rating(rating_as_string: str) -> int:
    """Parses a rating description and returns its integer representation."""
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
    """Parses all posts from the given raw table data."""
    return [parse_post(post_table.loc[i]) for i in range(1, len(post_table))]


def parse_post(post: Series[Any] | DataFrame) -> Post:
    """Parses a single post from the given table row data."""
    user = parse_user_name(str(post[0]))
    comment = str(post[1])
    rating = parse_rating(str(post[2]))
    return Post(user_name=user[0], post_date=user[1], comment=comment, rating=rating)


def parse_page(page_text: str) -> PageData:
    """Parses the given HTML [page_text] and returns the extracted data."""
    title_field_count: Final = 2
    grade_field_count: Final = 1

    soup = BeautifulSoup(page_text, "html.parser")

    title_result = re.search(
        r"(.*) - (.*)",
        soup.title.string if soup.title and soup.title.string else "",
    )
    if not title_result or len(title_result.groups()) != title_field_count:
        raise DataProcessingError("Page has no valid title.")

    peak = title_result.group(1)
    route = title_result.group(2)

    paragraph_elements = soup.find("p")
    paragraphs = paragraph_elements.getText() if paragraph_elements else ""
    grade_result = re.search(r".*?\[(.*?)\].*", paragraphs)
    if not grade_result or len(grade_result.groups()) != grade_field_count:
        raise DataProcessingError("Page has no valid grade.")

    grade = grade_result.group(1).strip()

    df_list = pd.read_html(
        StringIO(page_text.replace("<br>", "|"))
    )  # this parses all the tables in webpages to a list
    posts_table = df_list[3]
    posts = parse_posts(posts_table)
    return PageData(peak=Summit(name=peak), route=Route(route_name=route, grade=grade), posts=posts)
