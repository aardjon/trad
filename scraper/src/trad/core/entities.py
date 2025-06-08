"""
Provides all the business/core data types.
"""

import string
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Self

NO_GRADE: Final = 0
""" Special value to mark a missing or no grade. """


class GeoPosition:
    """
    A single geographical point in the WGS 84 geodetic system. It provides a maximum precision of
    geographic coordinates of about 1 cm (7 decimal places), which is the same as used by OSM.

    The coordinate values can be provided either as normal decimal degree values (float) or as
    integer values. Both provide the same precision, but the integer values multiplied by
    10.000.000 to provide the same precision without the drawbacks of the floating point
    representation. The integer representation is the same as in the route database, to avoid
    unnecessary conversions.
    """

    _COORDINATE_PRECISION: Final = 10000000

    def __init__(self, latitude: int, longitude: int):
        """
        Create a new instance with the given (integer) coordinate values. Raises [ValueError] if
        invalid values are given.
        """
        if abs(latitude) > 90 * self._COORDINATE_PRECISION:
            raise ValueError("Latitude value must be within [-90, 90]")
        if abs(longitude) > 180 * self._COORDINATE_PRECISION:
            raise ValueError("Longitude value must be within [-180, 180]")

        self._latitude = latitude
        self._longitude = longitude

    @classmethod
    def from_decimal_degree(cls, latitude: float, longitude: float) -> Self:
        """
        Create a new GeoPosition instance from the given decimal degree values.
        """
        return cls(
            latitude=int(latitude * cls._COORDINATE_PRECISION),
            longitude=int(longitude * cls._COORDINATE_PRECISION),
        )

    @property
    def latitude_int(self) -> int:
        """
        The latitude value as integer within [-900000000, 900000000].
        """
        return self._latitude

    @property
    def longitude_int(self) -> int:
        """
        The longitude value as integer within [-1800000000, 1800000000]
        """
        return self._longitude

    @property
    def latitude_decimal_degree(self) -> float:
        """
        The latitude value as decimal degree.
        """
        return float(self._latitude) / self._COORDINATE_PRECISION

    @property
    def longitude_decimal_degree(self) -> float:
        """
        The longitude value as decimal degree.
        """
        return float(self._longitude) / self._COORDINATE_PRECISION

    def __str__(self) -> str:
        hemisphere_lat = "N" if self._latitude >= 0 else "S"
        hemisphere_lon = "E" if self._longitude >= 0 else "W"
        lat_str = f"{abs(self.latitude_decimal_degree):.7f}".rstrip("0").rstrip(".")
        lon_str = f"{abs(self.longitude_decimal_degree):.7f}".rstrip("0").rstrip(".")
        return f"{lat_str}°{hemisphere_lat} {lon_str}°{hemisphere_lon}"


UNDEFINED_GEOPOSITION: Final = GeoPosition(0, 0)
"""
Special value representing an "undefined" GeoPosition instance. Used when the position information
is missing but we still want valid (but useless) data so that the application can continue normally
without having to check for this case over and over again (Null Object Pattern).

Please note that this geographical position is not *invalid*, it is just a point somewhere in the
Atlantic Ocean where we do not expect a climbing rock. It may be changed if a new island is
discovered there, of course ;)
"""


@dataclass
class Summit:
    """
    A single summit.

    A summit is a single rock or mountain that can be climbed onto. There are usually several routes
    to the top.
    """

    name: str
    """ The name of this summit. """

    position: GeoPosition = UNDEFINED_GEOPOSITION
    """ Geographical position of this summit. """

    @property
    def unique_identifier(self) -> str:
        """
        A unique identifier of this summit, unique within the current route database. It is not
        meant to be displayed to users.

        The identifier is based on the summit's name and can be used to map slightly different name
        variants (e.g. different punctuation or permutations) to each other. It does not work for
        completely different names, though.
        """
        identifier = self.name.lower()
        # Remove non-ASCII characters
        identifier = "".join(c for c in identifier if c in string.printable)
        # Replace punctuation characters with spaces
        identifier = "".join(c if c not in string.punctuation else " " for c in identifier)
        # Order the single segments alphabetically, and rejoin them with single underscores
        return "_".join(sorted(identifier.split()))


@dataclass
class Route:
    """
    A single climbing route.

    A route is the path by which a climber reaches the top of a mountain, so it is always attached
    to a single summit. In most cases, there are multiple routes onto each summit.

    Routes have several grades describing their difficulty, depending on the route characteristics
    (e.g. does it include a jump?), the climbing style (e.g. "all free" or "redpoint") and also on
    each other:
     - A route without a jumping grade is usually climbed without having to jump
     - A route with both grades contains a single jump within its climbing parts
     - A route with only a jumping grade consists of a single jump only
     - The AF/RP ratings of a route with OU grade require some additional support

    Grades are represented by integer numbers, with 1 being the lowest (or "easiest") possible
    rating and without an upper bound. Each step in the corresponding scale system increases the
    value by one, so e.g. the saxon grade VIIb is stored as 8 and the UIAA grade IV is stored as 6.
    0 can be used when a certain grade doesn't apply to a route at all, e.g. when there is no jump.
    """

    route_name: str
    """ The name of the route. """

    grade: str
    """ String representing the grade. Deprecated, use the more fine-grained grade fields. """

    grade_af: int = NO_GRADE
    """
    The grade that applies when climbing this route in the AF ("alles frei", i.e. "all free") style,
    i.e. without any belaying (no rope, no abseiling). Set to NO_GRADE when it is just a single
    jump.
    """

    grade_rp: int = NO_GRADE
    """
    The grade that applies when climbing this route in the RP ("Rotpunkt", i.e. "redpoint") style.
    This is the default style which is available for all climbing routes (but may still be missing
    for pure jumps). Set to NO_GRADE when it is just a single jump.
    """

    grade_ou: int = NO_GRADE
    """
    The grade that applies when climbing this route in the OU ("ohne Unterstützung", i.e. "without
    support") style, i.e. without using the support considered in the AF style grade. Set to
    NO_GRADE when the AF grade doesn't include any support.
    """

    grade_jump: int = NO_GRADE
    """
    The grade of the jump within this route. Set to NO_GRADE when there is no need to jump.
    """

    star_count: int = 0
    """
    The count of official stars assigned to this route. An increasing number of stars marks a route
    as "more beautiful". A value of zero doesn't mean that a route is bad, but that it is just a
    regular one.
    """

    dangerous: bool = False
    """
    True if the route is officially marked as "dangerous", False if not.
    """


@dataclass
class Post:
    """
    A single post someone contributed to a public climbing database or community.

    Posts are written by community members and can be assigned e.g. to routes, allowing the
    community to rate and comment. There can be multiple posts for the same entity.
    """

    user_name: str
    """ Name of the post's author. """

    post_date: datetime
    """ The time the post was published. """

    comment: str
    """ The comment. """

    rating: int
    """
    The rating the author assigned to the entity this post corresponds to. This is a signed integer
    value in the range between -3 (extremely bad/dangerous) to 3 (extremely outstanding/great).
    """
