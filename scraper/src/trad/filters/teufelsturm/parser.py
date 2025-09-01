"""
Teufelsturm route page content parser.
"""

from __future__ import annotations

import re
import urllib
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from logging import getLogger
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlparse

import pandas as pd
import pytz
from bs4 import BeautifulSoup
from bs4.element import Tag

from trad.core.entities import UNDEFINED_GEOPOSITION, GeoPosition, Post, Route, Summit
from trad.core.errors import DataProcessingError

if TYPE_CHECKING:
    from collections.abc import Callable

    from pandas.core.frame import DataFrame
    from pandas.core.series import Series

_logger = getLogger(__name__)


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


def parse_page(page_text: str, summit_cache: SummitCache) -> PageData:
    """Parses the given HTML [page_text] and returns the extracted data."""
    route_field_count: Final = 2
    grade_field_count: Final = 1

    soup = BeautifulSoup(page_text, "html.parser")
    paragraph_elements = soup.find("p")
    if not isinstance(paragraph_elements, Tag) or not paragraph_elements.contents:
        raise DataProcessingError(f"Page '{soup.title}' has no valid route and summit data")
    try:
        route_name_element = next(p for p in paragraph_elements.contents if isinstance(p, Tag))
        route_elements = [tag for tag in route_name_element.contents if isinstance(tag, Tag)]
    except Exception as e:
        raise DataProcessingError(
            f"Cannot find route and summit name on page '{soup.title}'"
        ) from e
    if len(route_elements) != route_field_count:
        raise DataProcessingError(f"Found unexpected name parts on page {soup.title}")

    route = route_elements[0].get_text().strip()

    peak_element = route_elements[1].find("a")
    if not isinstance(peak_element, Tag):
        raise DataProcessingError(f"Page '{soup.title}' has no valid route name")
    peak_url = urlparse(peak_element.attrs.get("href", ""))
    peak_id_result = re.search("gipfelnr=[0-9]+", peak_url.query)
    if not peak_id_result or not peak_id_result.string:
        raise DataProcessingError("Page has no valid summit ID.")
    peak_id = int(peak_id_result.string.split("=")[1])
    peak = summit_cache.get_summit_by_peak_id(peak_id)

    grade_result = re.search(r".*?\[(.*?)\].*", route_elements[1].get_text())
    if not grade_result or len(grade_result.groups()) != grade_field_count:
        raise DataProcessingError("Page has no valid grade.")
    grade = grade_result.group(1).strip()

    df_list = pd.read_html(
        StringIO(page_text.replace("<br>", "|"))
    )  # this parses all the tables in webpages to a list
    posts_table = df_list[3]
    posts = parse_posts(posts_table)

    # Teufelsturm doesn't provide information about name usage, that's why we have to set them as
    # 'unspecified'.
    return PageData(
        peak=peak,
        route=Route(route_name=route, grade=grade),
        posts=posts,
    )


def _fix_erroneous_name(summit_name: str) -> str:
    """
    Checks if the given `summit_name` is erroneous, and returns the fixed version (if it is) or the
    unchanged `summit_name` (if it is not).

    Background: Some summit names on Teufelsturm are simply wrong and therefore cannot be easily
    mapped automatically. "Wrong" means things like e.g.:
     - Typing mistakes
     - Spelling differs from the official name (e.g. using "1." or "I." instead of "First")

    They are just hard-coded here and replaced with the correct (official) name variant. Some (or
    even all) of the translations may be replaced by more generic approaches in the future.
    """
    known_name_errors = {
        "Amboß": "Amboss",
        "Burgener Turm": "Burgenerturm",
        "Lehnsteigturm, Dritter": "III. Lehnsteigturm",
        "Lehnsteigturm, Zweiter": "II. Lehnsteigturm",
        "Zerborstener Turm, Erster": "1. Zerborstener Turm",
        "Zerborstener Turm, Zweiter": "2. Zerborstener Turm",
        # TODO (aardjon): The following names are special, because they are indeed the correct,
        # official variant (which uses an abbreviation) while OSM uses (according to its rules) the
        # unabbreviated name. We will probably have to face many similar cases when merging routes.
        # A generic solution would be good here.
        "Gralsburg, NO-Zinne": "Gralsburg Nordost-Zinne",
        "Gralsburg, SW-Zinne": "Gralsburg Südwest-Zinne",
    }
    return known_name_errors.get(summit_name, summit_name)


def parse_route_list(page_text: str) -> set[int]:
    """Parses the given HTML [page_text] and returns the IDs of all referenced routes."""
    regexp = re.compile(r"/wege/bewertungen/anzeige\.php\?wegnr=\d+")
    return {
        int(urllib.parse.urlsplit(url).query.split("=")[1]) for url in regexp.findall(page_text)
    }


def _parse_summit_page(page_text: str) -> Summit:
    """Parses the given HTML [page_text] and creates a new Summit object from its data."""
    soup = BeautifulSoup(page_text, "html.parser")
    # The summit name is displayed with font face "Tahoma", size "3" and color of "#FFFFFF"
    possible_peak_names = soup.find_all("font", color="#FFFFFF", face="Tahoma", size="3")
    if len(possible_peak_names) != 1:
        raise DataProcessingError(
            f"Summit details page contains {len(possible_peak_names)} summit name candidates "
            "(expected 1).",
        )
    peak_name = possible_peak_names[0].get_text()

    # Replace the summit name if it is wrong
    peak_name = _fix_erroneous_name(peak_name)

    positions_table = soup.find_all("table")[-1]
    lat = None
    lon = None
    for table_cell in positions_table.find_all("td"):
        # Note: The coordinate values are interchanged on the summits page (no idea why, probably
        # just a mistake), that's why we purposely assign the "Latitude" value to `lon` and the
        # "Longitude" value to `lat`.
        if table_cell.get_text() == "Longitude":
            lat = table_cell.next_sibling.get_text()
        if table_cell.get_text() == "Latitude":
            lon = table_cell.next_sibling.get_text()

    if not (lat and lon):
        _logger.warning("Cannot find summit coordinates on details page of %s", peak_name)
        position = UNDEFINED_GEOPOSITION
    else:
        try:
            position = GeoPosition.from_decimal_degree(latitude=float(lat), longitude=float(lon))
        except Exception as e:
            raise DataProcessingError(
                f"The extracted coordinate values are invalid: ({lat}, {lon})"
            ) from e

    # Teufelsturm doesn't provide information about name usage, that's why we have to set them as
    # 'unspecified'. Also, the position values are known to be quite inaccurate, that's why we use
    # them for assistance only.
    return Summit(unspecified_names=[peak_name], low_grade_position=position)


class SummitCache:
    """
    A cache which provides Summit objects based on their teufelsturm ID, retrieving and creating
    them on demand (and only once).

    Individual cache entries are never deleted automatically, but it is possible to empty the whole
    cache at once by calling `clear_cache()`.
    """

    def __init__(self, retrieve_summit_details_page: Callable[[int], str]):
        """
        Create a new cache instance. The `retrieve_summit_details_page` is a function that takes a
        teufelsturm peak ID and returns the HTML content of this peak's details page.
        """
        self._retrieve_summit_details_page = retrieve_summit_details_page
        self._seen_summits: dict[int, Summit] = {}

    def get_summit_by_peak_id(self, peak_id: int) -> Summit:
        """
        Return the Summit object that corresponds to the given `peak_id`. If it is not present in
        the cache already, the summit data is retrieved by calling retrieve_summit_details_page().
        """
        summit = self._seen_summits.get(peak_id, None)
        if summit is None:
            page_text = self._retrieve_summit_details_page(peak_id)
            summit = _parse_summit_page(page_text)
            self._seen_summits[peak_id] = summit
        return summit

    def clear_cache(self) -> None:
        """Flushes the whole cache, deleting all previously retrieved summits."""
        self._seen_summits = {}
