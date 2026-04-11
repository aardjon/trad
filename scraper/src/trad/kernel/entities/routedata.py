"""
Provides types for representing the actual climbing route information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from logging import getLogger
from typing import Final

from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.names import NormalizedName
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.errors import IncompleteDataError

_logger = getLogger(__name__)

NO_GRADE: Final = 0
""" Special value to mark a missing or no grade. """


@dataclass
class Summit:
    """
    A single summit.

    A summit is a single rock or mountain that can be climbed onto. There are usually several routes
    to the top.

    A summit can have several different names for different usages, but it must always have at least
    one.
    """

    official_name: str | None = None
    """
    The official, default name of this summit.
    """

    alternate_names: list[str] = field(default_factory=list)
    """
    List of alternate names for this summit. Alternate names can be completely different (like
    historic or local) names as well as common names in different languages - basically everything
    a user may want to search for. Never contains the `official_name`
    """

    unspecified_names: list[str] = field(default_factory=list)
    """
    List of names whose usage is not specified, i.e. the source doesn't say whether they are
    official. These names do not end up in the created route database.
    """

    position: RankedValue[GeoPosition] = field(default_factory=RankedValue[GeoPosition].create_null)
    """
    Geographical position of this summit. May legally be a null object if no exact position is
    known.
    """

    sector: RankedValue[str] = field(default_factory=RankedValue[str].create_null)
    """
    Name of the sector this summit belongs to. Null value means that the sector is unknown.
    """

    def __post_init__(self) -> None:
        # Make sure that at least one name has been provided
        if not self.official_name and not self.alternate_names and not self.unspecified_names:
            raise ValueError("Cannot create Summit without a name.")

    @property
    def name(self) -> str:
        """
        Returns a name for this summit.

        The returned name is the first one that can be found from official, alternate, unspecified
        names (searching in that order). This may be useful if you just need any identifying name,
        e.g. to display it to the user. If you need certainty about the name usage, use one of the
        specialized properties instead.
        """
        # Note that there must always be at least one name somewhere, even though it is not ensured
        # (yet?)
        name = self.official_name
        if not name:
            name = next(iter(self.alternate_names), None)
        if not name:
            name = next(iter(self.unspecified_names))
        return name

    @property
    def normalized_name(self) -> NormalizedName:
        """
        The default normalized name of this summit, not meant to be displayed to users.
        """
        return NormalizedName(self.name)

    def get_all_normalized_names(self) -> list[NormalizedName]:
        """
        Return all known normalized names of this object.
        """
        off_name = [self.official_name] if self.official_name else []
        return [
            NormalizedName(name)
            for name in off_name + self.alternate_names + self.unspecified_names
        ]

    def fix_invalid_data(self) -> None:
        """
        Checks if the data of this Summit is invalid, and tries to fix any problems if possible.
        If the data is already valid, `self` is not modified. If invalid data cannot be fixed, an
        `IncompleteDataError` is raised.

        This method logs a warning message when automatically fixing data.
        """
        if not self.official_name:
            # Some summits don't have an official name. Possible reasons (besides bugs):
            #    - "Massive" are not (yet) retrieved from OSM (https://github.com/Headbucket/trad/issues/12)
            #    - New entries on some external sites
            # This can be fixed automatically by using any of the other names instead.
            available_name = self.name
            _logger.warning(
                "Found Summit without official name, setting it to '%s'",
                available_name,
            )
            self.official_name = available_name
            self.alternate_names.clear()
            self.unspecified_names.clear()

        if self.sector.is_null() or not self.sector.is_production_quality():
            # All summits must be assigned to a sector!
            raise IncompleteDataError(self, "sector")

        if not self.position.is_null() and not self.position.is_production_quality():
            # Ignore low-quality position data
            _logger.warning(
                "Discarding low-quality position data of Summit '%s'",
                self.official_name,
            )
            self.position = RankedValue.create_null()


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

    Routes come with a `conflict_rank` for determining which data to use in case of several
    conflicting values. This is a positive integer with 1 being the most important rank. If two
    Route objects describe the same route but differ in their grades, the data with the lower 'rank'
    value will be used.
    """

    conflict_rank: int
    """
    Priority value for determining which route data to choose in case of conflicting values (from
    different data sources). 1 is the most important rank.
    """

    route_name: str
    """ The name of the route. """

    grade: str = ""
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

    def fix_invalid_data(self) -> None:
        """
        Checks if the data of this Route is invalid, and tries to fix any problems if possible.
        If the data is already valid, `self` is not modified. If invalid data cannot be fixed, an
        `IncompleteDataError` is raised.

        This method logs a warning message when automatically fixing data.
        """
        if not self.route_name:
            raise IncompleteDataError(self, "name")


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

    source_label: str
    """
    Label ("name") of the external data source this post was retrieved from.
    """
