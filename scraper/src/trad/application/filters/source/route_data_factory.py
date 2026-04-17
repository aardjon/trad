"""
Provides functionality for easily creating route data domain objects (e.g. Summit or Route).
"""

from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import NO_GRADE, Route, RouteDirections, Summit
from trad.kernel.errors import InvalidStateError


class RouteDataFactory:
    """
    Factory for creating route data objects by using pre-defined value ranks.

    The idea is, to not having to provide the necessary rank data each time a new data object is
    created. Instead, each source filter should have one instance of this factory class and delegate
    the object creation to it. Each factory instance knows the rank values to be used, so they are
    configured only once and in a single place for each source.
    """

    def __init__(
        self,
        source_label: str | None = None,
        summit_sector_rank: int | None = None,
        summit_position_rank: int | None = None,
        route_grade_conflict_rank: int | None = None,
    ) -> None:
        """
        Create a new data factory which uses the given rank and source information when creating
        data objects. For undefined values, no value can be created - trying to do so will raise an
        InvalidStateError.
        """
        self._source_label = source_label
        self._summit_sector_rank = summit_sector_rank
        self._summit_position_rank = summit_position_rank
        self._route_grade_conflict_rank = (
            route_grade_conflict_rank or RankedValue.create_null().rank
        )

    def create_summit(
        self,
        official_name: str | None = None,
        alternate_names: list[str] | None = None,
        unspecified_names: list[str] | None = None,
        position: GeoPosition | None = None,
        sector: str | None = None,
    ) -> Summit:
        """
        Create a new `Summit` instance with the given data. See there for detailled parameter
        explanation.
        """
        return Summit(
            official_name=official_name,
            alternate_names=alternate_names or [],
            unspecified_names=unspecified_names or [],
            position=self._create_ranked_value(position, self._summit_position_rank),
            sector=self._create_ranked_value(sector, self._summit_sector_rank),
        )

    def create_route(  # noqa: PLR0913
        self,
        route_name: str,
        *,
        directions: str | None = None,
        grade: str = "",
        grade_af: int = NO_GRADE,
        grade_rp: int = NO_GRADE,
        grade_ou: int = NO_GRADE,
        grade_jump: int = NO_GRADE,
        star_count: int = 0,
        dangerous: bool = False,
    ) -> Route:
        """
        Create a new `Route` instance with the given data. See there for detailled parameter
        explanation.
        """
        if self._source_label is None:
            raise InvalidStateError("No source label has been defined in this factory instance.")
        route_directions = (
            [RouteDirections(directions=directions, source_label=self._source_label)]
            if directions
            else []
        )

        return Route(
            conflict_rank=self._route_grade_conflict_rank,
            route_name=route_name,
            directions=route_directions,
            grade=grade,
            grade_af=grade_af,
            grade_rp=grade_rp,
            grade_ou=grade_ou,
            grade_jump=grade_jump,
            star_count=star_count,
            dangerous=dangerous,
        )

    def _create_ranked_value[T](self, value: T | None, rank: int | None) -> RankedValue[T]:
        """
        Create a RankedValue instance with the given `value` and `rank`. Returns a null object if
        `value` is None.
        """
        if value is not None:
            if rank is not None:
                return RankedValue(
                    value=value,
                    rank=rank,
                )
            raise InvalidStateError("No rank has been defined in this factory instance.")
        return RankedValue.create_null()

    def _ensure_source_label(self) -> None:
        """
        Ensures that there is a source_label.
        """
        if self._source_label is None:
            raise InvalidStateError("No source label has been defined in this factory instance.")
