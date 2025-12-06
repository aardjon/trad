"""
Provides the functionality of merging different data objects (e.g. from different sources) that
actually describe the same physical entity into a single one.
"""

from abc import ABC, abstractmethod
from contextlib import suppress
from logging import getLogger
from typing import Final, override

from trad.kernel.boundaries.filters import Filter
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import UNDEFINED_GEOPOSITION, NormalizedName, Post, Route, Summit
from trad.kernel.errors import EntityNotFoundError

_logger = getLogger(__name__)


class MergeFilter(Filter):
    """
    A Filter for merging Summit (and Route) instances that are actually describing the same physical
    object into a single instance.

    TODO(aardjon): Routes are not correctly merged yet because atm there is only ever one single
                   source for routes which is also retrieved last. This must be fixed!
    """

    def __init__(self) -> None:
        """
        Create a new MergeFilter instance.
        """
        self._summits: list[Summit] = []
        self._routes: dict[NormalizedName, list[Route]] = {}
        self._posts: dict[NormalizedName, dict[str, list[Post]]] = {}

    @override
    def get_name(self) -> str:
        return "DataMerge"

    @override
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        merger = _SummitMerger(self._summits)
        for summit_id, summit in input_pipe.iter_summits():
            merger.merge_entity(summit)

            for route_id, route in input_pipe.iter_routes_of_summit(summit_id):
                self._add_route(summit.name, route)
                for post in input_pipe.iter_posts_of_route(route_id):
                    self._add_post(summit.name, route.route_name, post)
        self._write_merged_data(output_pipe)

    def _write_merged_data(self, output_pipe: Pipe) -> None:
        # Write all collected data into the output pipe
        summit_count = len(self._summits)
        _logger.debug("Writing summits with %s names...", summit_count)
        for idx, summit in enumerate(self._summits):
            summit_id = output_pipe.add_summit(summit)
            routes = self._routes.get(summit.normalized_name, [])
            _logger.debug(
                "Writing %s routes for summit %d/%d ('%s')...",
                len(routes),
                idx + 1,
                summit_count,
                summit.name,
            )
            for route in routes:
                route_id = output_pipe.add_route(summit_id, route)

                posts = self._posts.get(summit.normalized_name, {}).get(route.route_name, [])
                for post in posts:
                    output_pipe.add_post(route_id, post)

        # Delete all in-memory data
        self._summits.clear()
        self._routes.clear()
        self._posts.clear()

    def _add_route(self, summit_name: str, route: Route) -> None:
        self._routes.setdefault(self._find_first_summit(summit_name).normalized_name, []).append(
            route
        )
        # TODO(aardjon): Existing routes need to be merged, too! Not necessary with only Teufelsturm
        #                and OSM data being merged, though, because we don't gather route data from
        #                OSM.

    def _add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        self._posts.setdefault(self._find_first_summit(summit_name).normalized_name, {}).setdefault(
            route_name, []
        ).append(post)

    def _find_first_summit(self, summit_name: str) -> Summit:
        """
        Find the first summit object with the given `summit_name`. Raises EntityNotFoundError if no
        such summit can be found.
        """
        normalized_name = NormalizedName(summit_name)
        try:
            return next(
                summit
                for summit in self._summits
                if normalized_name in summit.get_all_normalized_names()
            )
        except StopIteration:
            raise EntityNotFoundError(summit_name) from None


class _EntityMerger[Entity: (Summit, Route)](ABC):
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
        - keep it length, if the entity is merged into an existing one
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
        # been the first of its kind (without any merging happening)
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
        modifed (unless their data is already equal). Raises MergeConflictError if merging is not
        possible.
        """


class _SummitMerger(_EntityMerger[Summit]):
    """
    Concrete implementation for merging Summit objects.
    """

    _match_search_radius: Final = 200
    """
    The radius (in meters) within which two Summits with the same same are considered to be the
    same.
    """

    @override
    def __init__(self, known_entities: list[Summit]):
        super().__init__(known_entities)
        self.__new_summit_id = 0
        """
        ID (as returned from the id() function) of the summit `self.__new_summit_normalized_names`
        refers to. 0 if no summit has been requested.
        """
        self.__new_summit_normalized_names: set[NormalizedName] = set()
        """ All normalized names of the Summit with the id `self.__new_summit_id` (may be empy). """

    @override
    def _is_same(self, existing_entity: Summit, new_entity: Summit) -> bool:
        new_summit_normalized_names = self.__get_all_normalied_names(new_entity)
        return bool(
            new_summit_normalized_names.intersection(existing_entity.get_all_normalized_names())
            and (
                (
                    existing_entity.position is UNDEFINED_GEOPOSITION
                    or new_entity.position is UNDEFINED_GEOPOSITION
                )
                or existing_entity.position.is_within_radius(
                    new_entity.position,
                    self._match_search_radius,
                )
            )
        )

    def __get_all_normalied_names(self, summit: Summit) -> set[NormalizedName]:
        """
        Returns all normalized names of the given `summit`. This method implements a cache of the
        last requested summit object, to not calculate the normalized strings over and over again.
        """
        if self.__new_summit_id != id(summit):
            self.__new_summit_id = id(summit)
            self.__new_summit_normalized_names = set(summit.get_all_normalized_names())
        return self.__new_summit_normalized_names

    @override
    def _merge_objects(self, target_entity: Summit, source_entity: Summit) -> None:
        target_entity.enrich(source_entity)

        # TODO(aardjon): Assigned routes need to be merged, too! Not necessary with only Teufelsturm
        #                and OSM data being merged, though, because we don't gather route data from
        #                OSM.
