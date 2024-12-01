"""
Provides all the business/core data types.
"""

from dataclasses import dataclass
from datetime import datetime


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
    """

    route_name: str
    """ The name of the route. """
    grade: str


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
    """ The rating the author assigned to the entity this post corresponds to. """
