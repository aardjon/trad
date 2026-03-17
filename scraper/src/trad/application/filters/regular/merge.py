"""
Provides the functionality of merging different data objects (e.g. from different sources) that
actually describe the same physical entity into a single one.
"""

import string
from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from logging import getLogger
from typing import Final, override

from trad.kernel.boundaries.filters import Filter
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import (
    NO_GRADE,
    UNDEFINED_GEOPOSITION,
    NormalizedName,
    Post,
    Route,
    Summit,
)
from trad.kernel.errors import MergeConflictError

_logger = getLogger(__name__)


class MergeFilter(Filter):
    """
    A Filter for merging Summit (and Route) instances that are actually describing the same physical
    object into a single instance.
    """

    def __init__(self) -> None:
        """
        Create a new MergeFilter instance.
        """
        self._merged_summit_data: list[_SummitRelatedData] = []

    @override
    def get_name(self) -> str:
        return "DataMerge"

    @override
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        for source in input_pipe.get_sources():
            output_pipe.add_source(source)

        summit_merger = _SummitMerger(self._merged_summit_data)
        for summit_id, summit in input_pipe.iter_summits():
            full_summit_data = _SummitRelatedData(summit=summit, routes=[])
            route_merger = _RouteMerger(full_summit_data.routes)
            for route_id, route in input_pipe.iter_routes_of_summit(summit_id):
                full_route_data = _RouteRelatedData(route=route, posts=[])
                for post in input_pipe.iter_posts_of_route(route_id):
                    full_route_data.posts.append(post)
                route_merger.merge_entity(full_route_data)
            summit_merger.merge_entity(full_summit_data)

        self._write_merged_data(output_pipe)

    def _write_merged_data(self, output_pipe: Pipe) -> None:
        # Write all collected data into the output pipe
        summit_count = len(self._merged_summit_data)
        _logger.debug("Writing summits with %s names...", summit_count)
        for idx, summit_data in enumerate(self._merged_summit_data):
            summit_id = output_pipe.add_summit(summit_data.summit)
            _logger.debug(
                "Writing %s routes for summit %d/%d ('%s')...",
                len(summit_data.routes),
                idx + 1,
                summit_count,
                summit_data.summit.name,
            )

            for route_data in summit_data.routes:
                route_id = output_pipe.add_route(summit_id, route_data.route)

                for post in route_data.posts:
                    output_pipe.add_post(route_id, post)

        # Delete all in-memory data
        self._merged_summit_data.clear()


@dataclass
class _SummitRelatedData:
    """
    Encapsulation of all data related to a single summit.
    """

    summit: Summit
    """ The summit instance. """
    routes: list[_RouteRelatedData]
    """ Data of all routes that are assigned to this summit. """


@dataclass
class _RouteRelatedData:
    """
    Encapsulation of all data related to a single route.
    """

    route: Route
    """ The Route instance. """
    posts: list[Post]
    """ All Posts that are assigned to this route. """


class _EntityMerger[Entity: (_SummitRelatedData, _RouteRelatedData)](ABC):
    """
    Generic algorithm for merging summits or routes. New entities are merged into the list provided
    on instantiation (modifying it!). Utilizes the Template Method design pattern, i.e. certain
    steps of the algorithm are delegated to derived classes.

    The `Entity` type parameter is the type of entity objects to be merged.
    """

    def __init__(self, target_entities: list[Entity]):
        """
        Creates a new Merger instance for merging objects of type `Entity` into `target_entities`.
        The given list may contain any number of items (including none).
        """
        self.__target_entities: list[Entity] = target_entities

    def merge_entity(self, new_entity: Entity) -> None:
        """
        Merges the given `new_entity` into the target entities list. Due to that, the list may:
        - increase, if the entity is new and therefore just added
        - keep its length, if the entity is merged into an existing one
        - shrink, if the new entity reveals that several existing ones must be merged

        However, the target list will never be empty after calling this method.

        May raise a MergeConflictError if the entity cannot be merged.
        """
        # Find all already known Entity objects that are physically the same as the new one
        existing_objects_to_merge = [
            existing_entity
            for existing_entity in self.__target_entities
            if self._is_same(existing_entity, new_entity)
        ] + [new_entity]

        # Merge all found objects into the first one and remove them from the self.__known_entities
        # list (if necessary)
        target_object = existing_objects_to_merge[0]
        for merge_object in existing_objects_to_merge[1:]:
            self._merge_objects(target_object, merge_object)
            with suppress(ValueError):
                self.__target_entities.remove(merge_object)

        # Make sure that the target object is contained in self._summits list, because it may have
        # been the first of its kind (without any merging happening at all)
        if target_object not in self.__target_entities:
            self.__target_entities.append(target_object)

    @abstractmethod
    def _is_same(self, existing_entity: Entity, new_entity: Entity) -> bool:
        """
        Returns True if the two given entities are describing the same physical object (e.g. the
        same summit) and therefore have to be merged, or False if they don't.
        """

    @abstractmethod
    def _merge_objects(self, target_entity: Entity, source_entity: Entity) -> None:
        """
        Merges the `source_entity` into `target_entity` by enriching its data. The target entity is
        modified (unless their data is already equal). Raises MergeConflictError if merging is not
        possible.
        """


class _SummitMerger(_EntityMerger[_SummitRelatedData]):
    """
    Concrete implementation for merging Summit objects.
    """

    _match_search_radius: Final = 200
    """
    The radius (in meters) within which two Summits with the same same are considered to be the
    same.
    """

    @override
    def __init__(self, known_entities: list[_SummitRelatedData]):
        super().__init__(known_entities)
        self.__new_summit_id = 0
        """
        ID (as returned from the id() function) of the summit `self.__new_summit_normalized_names`
        refers to. 0 if no summit has been requested.
        """
        self.__new_summit_normalized_names: set[NormalizedName] = set()
        """ All normalized names of the Summit with the id `self.__new_summit_id` (may be empy). """

    @override
    def _is_same(self, existing_entity: _SummitRelatedData, new_entity: _SummitRelatedData) -> bool:
        existing_summit = existing_entity.summit
        new_summit = new_entity.summit

        new_summit_normalized_names = self.__get_all_normalized_names(new_summit)
        return bool(
            new_summit_normalized_names.intersection(existing_summit.get_all_normalized_names())
            and (
                (
                    existing_summit.position is UNDEFINED_GEOPOSITION
                    or new_summit.position is UNDEFINED_GEOPOSITION
                )
                or existing_summit.position.is_within_radius(
                    new_summit.position,
                    self._match_search_radius,
                )
            )
        )

    def __get_all_normalized_names(self, summit: Summit) -> set[NormalizedName]:
        """
        Returns all normalized names of the given `summit`. This method implements a cache of the
        last requested summit object, to not calculate the normalized strings over and over again.
        """
        if self.__new_summit_id != id(summit):
            self.__new_summit_id = id(summit)
            self.__new_summit_normalized_names = set(summit.get_all_normalized_names())
        return self.__new_summit_normalized_names

    @override
    def _merge_objects(
        self,
        target_entity: _SummitRelatedData,
        source_entity: _SummitRelatedData,
    ) -> None:
        self.enrich_summit(target_entity.summit, source_entity.summit)

        merger = _RouteMerger(target_entity.routes)
        for route_data in source_entity.routes:
            merger.merge_entity(route_data)

    @staticmethod
    def enrich_summit(target: Summit, source: Summit) -> None:
        """
        Enrich (merge) the `target` Summit instance with the data from `source` (making it the union
        of both). Raises `MergeConflictError` if some data cannot be merged because of an
        unresolvable conflict.
        """
        _SummitMerger._enrich_official_name(target, source)
        _SummitMerger._enrich_alternate_names(target, source)
        _SummitMerger._enrich_unspecified_names(target, source)
        _SummitMerger._enrich_position(target, source)
        _SummitMerger._enrich_sector(target, source)

    @staticmethod
    def _enrich_official_name(target: Summit, source: Summit) -> None:
        if not source.official_name:
            return

        if not target.official_name:
            target.official_name = source.official_name
            return

        if NormalizedName(source.official_name) == NormalizedName(target.official_name):
            return
        raise MergeConflictError("summit", source.name, "official name")

    @staticmethod
    def _enrich_alternate_names(target: Summit, source: Summit) -> None:
        if source.alternate_names:
            target.alternate_names = list(
                dict.fromkeys(target.alternate_names + source.alternate_names)
            )
        # Make sure the official name is not contained in the alternate list
        if target.official_name:
            with suppress(ValueError):
                target.alternate_names.remove(target.official_name)

    @staticmethod
    def _enrich_unspecified_names(target: Summit, source: Summit) -> None:
        if source.unspecified_names:
            target.unspecified_names = list(
                dict.fromkeys(target.unspecified_names + source.unspecified_names)
            )

    @staticmethod
    def _enrich_position(target: Summit, source: Summit) -> None:
        # Merge the high grade position
        if target.high_grade_position == UNDEFINED_GEOPOSITION:
            target.high_grade_position = source.high_grade_position
        elif source.high_grade_position != UNDEFINED_GEOPOSITION and (
            not target.high_grade_position.is_equal_to(source.high_grade_position)
        ):
            raise MergeConflictError("summit", source.name, "high_grade_position")

        # Use the low-grade position only if none is set already - otherwise, ignore the other one
        if target.low_grade_position == UNDEFINED_GEOPOSITION:
            target.low_grade_position = source.low_grade_position

    @staticmethod
    def _enrich_sector(target: Summit, source: Summit) -> None:
        if target.sector is None:
            target.sector = source.sector
        elif source.sector not in (None, target.sector):
            raise MergeConflictError("summit", source.name, "sector")


class _RouteMerger(_EntityMerger[_RouteRelatedData]):
    """
    Concrete implementation for merging Route objects (including their Posts).
    """

    @override
    def _is_same(self, existing_entity: _RouteRelatedData, new_entity: _RouteRelatedData) -> bool:
        existing_route = existing_entity.route
        new_route = new_entity.route
        return self.__normalize_name(existing_route.route_name) == self.__normalize_name(
            new_route.route_name
        ) and (
            existing_route.grade_af == new_route.grade_af
            or existing_route.conflict_rank != new_route.conflict_rank
        )

    def __normalize_name(self, object_name: str) -> str:
        """Does the actual name normalization."""
        normalized_name = object_name
        # Replace some common abbreviations
        # Note: The order is important (don't replace "O-" only for "NO-")!
        for abbr, full in (
            ("AW", "Alter Weg"),
            ("NO-", "Nordost"),
            ("NW-", "Nordwest"),
            ("SO-", "Südost"),
            ("SW-", "Südwest"),
            ("N-", "Nord"),
            ("S-", "Süd"),
            ("O-", "Ost"),
            ("W-", "West"),
        ):
            normalized_name = normalized_name.replace(abbr, full)

        # Lower-case the whole string
        normalized_name = normalized_name.lower()
        # Remove non-ASCII characters
        normalized_name = "".join(c for c in normalized_name if c in string.printable)
        # Replace punctuation characters with spaces
        normalized_name = "".join(
            c if c not in string.punctuation else " " for c in normalized_name
        )
        # Order the single segments alphabetically, and rejoin them with single underscores
        return "_".join(sorted(normalized_name.split()))

    @override
    def _merge_objects(
        self,
        target_entity: _RouteRelatedData,
        source_entity: _RouteRelatedData,
    ) -> None:
        target_route = target_entity.route
        source_route = source_entity.route

        # Merge grade data
        target_grade = (
            target_route.grade_af,
            target_route.grade_ou,
            target_route.grade_rp,
            target_route.grade_jump,
            target_route.dangerous,
            target_route.star_count,
        )
        source_grade = (
            source_route.grade_af,
            source_route.grade_ou,
            source_route.grade_rp,
            source_route.grade_jump,
            source_route.dangerous,
            source_route.star_count,
        )
        missing_grade: Final = (NO_GRADE, NO_GRADE, NO_GRADE, NO_GRADE, False, 0)

        if target_grade == missing_grade:
            target_route.grade_af = source_route.grade_af
            target_route.grade_ou = source_route.grade_ou
            target_route.grade_rp = source_route.grade_rp
            target_route.grade_jump = source_route.grade_jump
            target_route.dangerous = source_route.dangerous
            target_route.star_count = source_route.star_count
            target_route.conflict_rank = source_route.conflict_rank
        elif source_grade == target_grade:
            # Data is equal - use the better (lower) rank if they differ
            target_route.conflict_rank = min(target_route.conflict_rank, source_route.conflict_rank)
        elif source_grade != missing_grade:
            # Take the data from the object with the lower rank. If this is the target, nothing must
            # be done to just keep the data.
            if source_route.conflict_rank < target_route.conflict_rank:
                target_route.grade_af = source_route.grade_af
                target_route.grade_ou = source_route.grade_ou
                target_route.grade_rp = source_route.grade_rp
                target_route.grade_jump = source_route.grade_jump
                target_route.dangerous = source_route.dangerous
                target_route.star_count = source_route.star_count
                target_route.conflict_rank = source_route.conflict_rank
            elif source_route.conflict_rank == target_route.conflict_rank:
                # Conflicting data and same rank
                raise MergeConflictError("route", source_route.route_name, "grade")

        # Add all posts from the source route to the target route
        target_entity.posts.extend(source_entity.posts)
