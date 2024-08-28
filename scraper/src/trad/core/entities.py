"""
Provides all the business/core data types.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Final

NO_GRADE: Final = 0
""" Special value to mark a missing or no grade. """


@dataclass
class Summit:
    """
    A single summit.

    A summit is a single rock or mountain that can be climbed onto. There are usually several routes
    to the top.
    """

    name: str
    """ The name of this summit. """


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
    The count of official stars assigend to this route. An increasing number of stars marks a route
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
