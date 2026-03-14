"""
Provide a Filter implementation for importing data from sandsteinklettern.de.
"""

from logging import getLogger
from typing import Final, override

import pytz

from trad.application.boundaries.http import HttpNetworkingBoundary
from trad.application.filters._base import SourceFilter
from trad.application.filters.source.sandsteinklettern.api import (
    ApiItemIdType,
    JsonGipfel,
    JsonGipfelStatus,
    JsonGipfelTyp,
    JsonKomment,
    JsonSektor,
    JsonWeg,
    JsonWegStatus,
    SandsteinkletternApiReceiver,
)
from trad.application.grades import GradeParser, SaxonGrade
from trad.application.grades.fuzzy import FuzzyParser
from trad.kernel.boundaries.pipes import Pipe, RouteInstanceId, SummitInstanceId
from trad.kernel.entities import ExternalSource, GeoPosition, Post, Route, Summit
from trad.kernel.errors import DataProcessingError, ValueParseError

_logger = getLogger(__name__)


class _ExternalToPipeIdMap[PipeIdType]:
    """
    An ID mapping storages that assigns internal (Pipe side) ID to their corresponding external (API
    side) ones, or marks them as being ignored if this the case.

    Each ID can either be assigned or ignored, but not both. Also, each ID must be set only once.
    Calling `clear()` resets all assignments.
    """

    def __init__(self) -> None:
        self._external_to_pipe_id_map: dict[ApiItemIdType, PipeIdType] = {}
        self._ignored_external_ids: set[ApiItemIdType] = set()

    def get_pipe_id(self, external_id: ApiItemIdType) -> PipeIdType:
        """
        Returns the Pipe side ID that is assigned the given `external_id`. Raises `KeyError` if the
        ID is not assigend.
        """
        return self._external_to_pipe_id_map[external_id]

    def is_ignored(self, external_id: ApiItemIdType) -> bool:
        """Returns True if the entity with the given `external_id` is ignored, otherwise False."""
        return external_id in self._ignored_external_ids

    def set_pipe_id(self, external_id: ApiItemIdType, pipe_id: PipeIdType) -> None:
        """
        Assigns the given `pipe_id` to the given `external_id`. Raises `KeyError` if the ID is
        already assigend a different value, or is ignored.
        """
        if external_id in self._ignored_external_ids:
            raise KeyError(f"External ID {external_id} is already ignored")
        if external_id in self._external_to_pipe_id_map:
            raise KeyError(f"External ID {external_id} is already set")
        self._external_to_pipe_id_map[external_id] = pipe_id

    def ignore_external_id(self, external_id: ApiItemIdType) -> None:
        """
        Marks the given `external_id` as being ignored. Raises `KeyError` if a Pipe ID has already
        been assigend earlier.
        """
        if external_id in self._external_to_pipe_id_map:
            raise KeyError(f"External ID {external_id} is already mapped to a pipe ID")
        self._ignored_external_ids.add(external_id)

    def clear(self) -> None:
        """Clear all stored data. IDs can be marked and assigned again differently after this."""
        self._external_to_pipe_id_map.clear()
        self._ignored_external_ids.clear()


class SandsteinkletternDataFilter(SourceFilter):
    """
    Filter for importing data from https://www.sandsteinklettern.de into the pipe.

    The sandsteinklettern.de DB does not assign "stars" to the route grades, but instead puts them
    into the route name. There always seems to be only one star at the most for now, but we still
    count them to set the correct number if this changes in the future.
    """

    _EXTERNAL_SOURCE_DESCRIPTION: Final = ExternalSource(
        label="Sandsteinklettern",
        url="http://sandsteinklettern.de",
        attribution="Jörg Brutscher",
    )

    _ROUTE_DATA_RANK: Final = 3
    """Priority/Accuracy of the route data retrieved from sandsteinklettern in case of conflicts."""

    _timezone_berlin: Final = pytz.timezone("Europe/Berlin")
    """ Time zone from which all naive dates on the external system are assumed to be."""

    def __init__(self, network_boundary: HttpNetworkingBoundary) -> None:
        """
        Create a new SandsteinkletternDataFilter instance that retrieves data via the given
        [network_boundary].
        """
        super().__init__()
        self._api_receiver = SandsteinkletternApiReceiver(http_boundary=network_boundary)
        self._grade_parser: GradeParser = FuzzyParser()

        self._summit_added = False  # Remember if at least one summit has been added (True) or not
        self._summit_id_map = _ExternalToPipeIdMap[SummitInstanceId]()
        self._route_id_map = _ExternalToPipeIdMap[RouteInstanceId]()

    @override
    def get_name(self) -> str:
        return "sandsteinklettern.de"

    @override
    def _execute_source_filter(self, output_pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())

        for sector in self._get_all_sectors():
            _logger.debug("Retrieving data of sector '%s'", sector.sektorname_d)
            self._import_summits_of_sector(output_pipe, sector)
            self._import_routes_of_sector(output_pipe, sector)
            self._import_posts_of_sector(output_pipe, sector)
            self._summit_id_map.clear()
            self._route_id_map.clear()

        if self._summit_added:
            self._import_source_attribution(output_pipe)

        _logger.debug("'%s' filter finished", self.get_name())

    def _get_all_sectors(self) -> list[JsonSektor]:
        _country_name: Final = "Deutschland"
        _area_name: Final = "Sächsische Schweiz"

        areas = self._api_receiver.retrieve_areas(country_name=_country_name)
        area_id_to_request = next(
            area.gebiet_id for area in iter(areas) if area.gebiet == _area_name
        )
        return self._api_receiver.retrieve_sectors(area_id=area_id_to_request)

    def _import_source_attribution(self, output_pipe: Pipe) -> None:
        output_pipe.add_source(self._EXTERNAL_SOURCE_DESCRIPTION)

    def _import_summits_of_sector(
        self,
        output_pipe: Pipe,
        sector: JsonSektor,
    ) -> None:
        for json_summit in self._api_receiver.retrieve_summits(sector.sektor_id):
            if self._ignore_summit(json_summit):
                self._summit_id_map.ignore_external_id(json_summit.gipfel_id)
                continue

            summit_names = self._parse_summit_names(json_summit)
            if not summit_names:
                _logger.warning("Ignoring summit %s because it has no name", json_summit.gipfel_id)
                self._summit_id_map.ignore_external_id(json_summit.gipfel_id)
                continue

            pipe_id = output_pipe.add_summit(
                Summit(
                    unspecified_names=summit_names,
                    low_grade_position=GeoPosition.from_decimal_degree(
                        latitude=float(json_summit.ngrd),
                        longitude=float(json_summit.vgrd),
                    ),
                )
            )
            self._summit_id_map.set_pipe_id(json_summit.gipfel_id, pipe_id)
            self._summit_added = True

    def _ignore_summit(self, json_summit: JsonGipfel) -> bool:
        """
        Checks if the given `json_summit` has to be ignored completely for some reason.
        """
        allowed_typ_value: Final = (JsonGipfelTyp.REGULAR, JsonGipfelTyp.CRAG)
        allowed_status_value: Final = (
            JsonGipfelStatus.OPEN,
            JsonGipfelStatus.PARTIALLY_CLOSED,
            JsonGipfelStatus.OCCASIONALLY_CLOSED,
        )
        forbidden_summit_name: Final = "Übungsstelle "

        if json_summit.typ not in allowed_typ_value:
            # Ignore because this is not a regular climbing crag (but e.g. a cave or alpine path)
            return True
        if json_summit.status not in allowed_status_value:
            # Ignore because the summit not accessible (e.g. not existing anymore)
            return True
        if json_summit.gipfelname_d.startswith(forbidden_summit_name):  # noqa: SIM103
            # Ignore because these are no real, official climbing crags (even though they are tagged
            # as such)
            return True
        return False

    def _parse_summit_names(self, json_summit: JsonGipfel) -> list[str]:
        """Parses all names of this summit into a plain list."""
        extracted_names: list[str] = []
        for name in (json_summit.gipfelname_d, json_summit.gipfelname_cz):
            all_names = self._fix_erroneous_name(name)
            if all_names.endswith(")"):
                extracted_names.extend(n.strip() for n in all_names[:-1].split("("))
            else:
                extracted_names.extend([all_names.strip()])
        return [n for n in extracted_names if n]

    def _import_routes_of_sector(
        self,
        output_pipe: Pipe,
        sector: JsonSektor,
    ) -> None:
        for json_route in self._api_receiver.retrieve_routes(sector_id=sector.sektor_id):
            if self._ignore_route(json_route):
                self._route_id_map.ignore_external_id(json_route.weg_id)
                continue
            try:
                self._import_route(output_pipe, json_route)
            except DataProcessingError as e:
                _logger.exception(
                    "Ignoring route %s due to a processing error!", json_route.weg_id, exc_info=e
                )
                self._route_id_map.ignore_external_id(json_route.weg_id)

    def _import_route(self, output_pipe: Pipe, json_route: JsonWeg) -> None:
        try:
            parsed_grade = self._parse_grade(json_route.schwierigkeit)
        except ValueParseError as e:
            _logger.warning(
                "Failed parsing the grade of route %s due to: %s", json_route.weg_id, str(e)
            )
            parsed_grade = SaxonGrade()

        pipe_id = output_pipe.add_route(
            summit_id=self._summit_id_map.get_pipe_id(json_route.gipfelid),
            route=Route(
                self._ROUTE_DATA_RANK,
                route_name=self._parse_route_name(json_route),
                grade=json_route.schwierigkeit,
                grade_af=parsed_grade.af,
                grade_ou=parsed_grade.ou,
                grade_rp=parsed_grade.rp,
                grade_jump=parsed_grade.jump,
                star_count=self._count_stars(json_route),
                dangerous=parsed_grade.danger,
            ),
        )
        self._route_id_map.set_pipe_id(json_route.weg_id, pipe_id)

    def _ignore_route(self, json_route: JsonWeg) -> bool:
        # TODO(aardjon): What about WegStatus FIRST_ASCEND and MENTIONED?
        allowed_status_values: Final = (JsonWegStatus.ACKNOWLEDGED, JsonWegStatus.TEMP_CLOSED)

        if self._summit_id_map.is_ignored(json_route.gipfelid):
            # Ignore because the whole summit has been ignored
            return True
        if self._check_erroneous_route(json_route.weg_id):
            # Ignore because this route is known to be somehow wrong in the source
            return True
        if json_route.wegstatus not in allowed_status_values:
            # Ignore, because the route is not an officially allowed one
            return True
        if not json_route.wegname_d.strip() and not json_route.wegname_cz.strip():  # noqa: SIM103
            # Ignore routes without a name
            return True

        return False

    def _parse_route_name(self, json_route: JsonWeg) -> str:
        """
        Chooses a name (if there are several) and removes the "*" from the beginning of it, if any.
        """
        route_name = json_route.wegname_d.strip() or json_route.wegname_cz.strip()
        return route_name.replace("*", "").strip()

    def _count_stars(self, json_route: JsonWeg) -> int:
        """
        Stars are not part of the grade but are added to the beginning of the name.
        """
        route_name = json_route.wegname_d.strip() or json_route.wegname_cz.strip()
        return route_name.count("*")

    def _parse_grade(self, grade_label: str) -> SaxonGrade:
        """
        Prepares the grade label for the parser by removing/fixing some possible data problems.
        Background: On sandsteinklettern, users can enter any string as route grade.
        """
        normalized_grade = grade_label.strip()
        return self._grade_parser.parse_saxon_grade(normalized_grade)

    def _import_posts_of_sector(
        self,
        output_pipe: Pipe,
        sector: JsonSektor,
    ) -> None:
        for json_post in self._api_receiver.retrieve_posts(sector_id=sector.sektor_id):
            if self._ignore_post(json_post):
                continue
            try:
                self._import_post(output_pipe, json_post)
            except DataProcessingError as e:
                _logger.exception(
                    "Ignoring post %s due to a processing error!", json_post.komment_id, exc_info=e
                )

    def _ignore_post(self, json_post: JsonKomment) -> bool:
        summit_assigned_post_id: Final = "0"
        if self._route_id_map.is_ignored(json_post.wegid):
            # Ignore because the corresponding route is ignored
            return True
        if json_post.wegid == summit_assigned_post_id:  # noqa: SIM103
            # Ignore, because this post is assigned to a summit itself instead of a route
            return True
        return False

    def _import_post(self, output_pipe: Pipe, json_post: JsonKomment) -> None:
        output_pipe.add_post(
            route_id=self._route_id_map.get_pipe_id(json_post.wegid),
            post=Post(
                user_name=json_post.username,
                post_date=self._timezone_berlin.localize(json_post.datum),
                comment=json_post.kommentar,
                rating=self._parse_route_rating(json_post),
                source_label=self._EXTERNAL_SOURCE_DESCRIPTION.label,
            ),
        )

    def _parse_route_rating(self, json_post: JsonKomment) -> int:
        """
        Map the rating to our scale. TODO(aardjon): The rating system needs to change in the future,
        to make all ratings equally important (https://github.com/aardjon/trad/issues/33)
        """
        ratings_map: Final = {
            "0": 0,  # Map now rating to "average/normal"
            "1": 3,
            "2": 2,
            "3": 0,
            "4": -2,
            "5": -3,
        }
        rating = ratings_map.get(json_post.qual)
        if rating is None:
            raise ValueParseError("route rating", json_post.qual)
        return rating

    @staticmethod
    def _fix_erroneous_name(summit_name: str) -> str:
        """
        Checks if the given `summit_name` is erroneous, and returns the fixed version (if it is) or
        the unchanged `summit_name` (if it is not).

        Background: Some summit names on sandsteinklettern are simply wrong and therefore cannot be
        easily mapped automatically. "Wrong" means things like e.g.:
         - Typing mistakes
         - Spelling differs from the official name (e.g. using "1." or "I." instead of "First")

        They are just hard-coded here and replaced with the correct (official) name variant. Since
        the external data can be edited, they may be fixed there at eventually. Also, some of the
        translations may be replaced by more generic approaches in the future.
        """
        known_name_errors = {
            "Dritter Lehnsteigturm": "III. Lehnsteigturm",
            "Festung Königstein": "Königstein",
            "Gralsburg, Nordostzinne": "Gralsburg Nordost-Zinne",
            "Gralsburg, Südwestzinne": "Gralsburg Südwest-Zinne",
            "Kleiner Amboss": "Kleiner Amboß",
            "Lilienstein - Westecke": "Lilienstein-Westecke",
            "Zweiter Lehnsteigturm": "II. Lehnsteigturm",
            "Zwergfels": "Zwerg",
        }
        return known_name_errors.get(summit_name, summit_name)

    @staticmethod
    def _check_erroneous_route(external_route_id: ApiItemIdType) -> bool:
        """
        Return True if the route with the given external ID (aka "wegid") must be ignored, or False
        if not (the normal case).

        Background: Sandsteinklettern contains some "route" entries that to not correspond to actual
        routes (for different reasons) and therefore shall be ignored.
        """
        routes_to_ignore: Final = {
            "77482",  # Müllerstein, "***Sockelwege:" (it's actually a kind of section title)
        }
        return external_route_id in routes_to_ignore
