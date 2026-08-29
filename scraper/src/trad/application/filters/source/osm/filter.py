"""
Filter for importing OSM data. Data is retrieved from Nominatim and Overpass.
"""

from collections.abc import Callable, Collection, Iterable, Iterator
from functools import partial
from logging import getLogger
from typing import Final, override

from trad.application.boundaries.http import HttpNetworkingBoundary
from trad.application.filters._base import SourceFilter
from trad.application.filters.source.osm.api import OsmApiReceiver
from trad.application.filters.source.osm.api.overpass import (
    OsmObjectTypes,
    OverpassElement,
    OverpassNode,
    OverpassRelation,
    OverpassTags,
)
from trad.application.filters.source.route_data_factory import RouteDataFactory
from trad.kernel.boundaries.pipes import Pipe, SummitInstanceId
from trad.kernel.entities.datasources import ExternalSource
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.routedata import Summit
from trad.kernel.errors import DataProcessingError, MergeConflictError

_logger = getLogger(__name__)


class OsmSummitDataFilter(SourceFilter):
    """
    Filter for importing summit data from the OpenStreetMap database.

    This filter imports the following information for all summits where climbing is allowed:
        - name
        - geographical position
        - climbing regulations

    Using the positions from OSM has the advantage that when sending it to some OSM based map later
    on the mobile device, the point is exactly on the summit and not "somewhere near".

    In general, this implementation tries to do as less OSM queries as possible, and to reduce the
    transfered data amount to a minimum.
    """

    _EXTERNAL_SOURCE_DESCRIPTION: Final = ExternalSource(
        label="OpenStreetMap",
        url="https://www.openstreetmap.org",
        license_name="ODbL",
        attribution="OSM Contributors",
    )
    """
    Source attribution for OSM.
    Please note that (other than other filters) the OSM attribution is always added because we never
    expect it to retrieve no data at all.
    """

    def __init__(self, network_boundary: HttpNetworkingBoundary) -> None:
        """
        Create a new OsmSummitDataFilter instance that retrieves data via the given
        [network_boundary].
        """
        super().__init__()
        self._osm_api_receiver = OsmApiReceiver(http_boundary=network_boundary)
        self._route_data_factory = RouteDataFactory(summit_sector_rank=1, summit_position_rank=1)

    @override
    def get_name(self) -> str:
        return "OpenStreetMap"

    @override
    def _execute_source_filter(self, output_pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        # Add the external source attribution
        self.__store_external_source_attribution(output_pipe)

        data_cache = _OsmDataCache()
        data_cache.retrieve_all_data(self._osm_api_receiver)

        self.__process_peak_nodes(data_cache, output_pipe)
        self.__process_peak_relations(data_cache, output_pipe)

        _logger.debug("'%s' filter finished", self.get_name())

    def __process_peak_nodes(self, data_cache: _OsmDataCache, output_pipe: Pipe) -> None:
        summits_from_nodes = self.__create_summits_from_nodes(
            data_cache, data_cache.get_peak_nodes()
        )
        # We can ignborie the return value here because peak nodes never have any routes assigned
        self.__store_summits(output_pipe, summits_from_nodes)

        _logger.debug("Processed summits from %d nodes", len(data_cache.get_peak_nodes()))

    def __process_peak_relations(self, data_cache: _OsmDataCache, output_pipe: Pipe) -> None:
        # Create Summit objects for all relations
        summits_from_relations = self.__create_summits_from_relations(
            data_cache, data_cache.get_peak_relations()
        )
        # Send all created summits to the pipe
        self.__store_summits(output_pipe, summits_from_relations)

        _logger.debug("Processed summits from %d relations", len(data_cache.get_peak_relations()))

    def __is_forbidden_node(self, osm_node: OverpassNode) -> bool:
        """
        Returns True if the given peak node may never be climbed on. This is checked by means of
        legal restrictions, i.e. the 'access' tag.
        For nodes with partial (e.g. seasonal) restrictions this method returns False because they
        can indeed be accessed legally (just not always), and thus the restriction must be evaluated
        by the mobile app dynamically.
        """
        total_access_restrictions: Final = ["no", "private"]
        return osm_node.tags.access in total_access_restrictions

    def __create_summits_from_relations(
        self,
        data_cache: _OsmDataCache,
        peak_relations: Collection[OverpassRelation],
    ) -> Iterator[tuple[int, Summit]]:
        """
        Creates (and yields) a Summit object for each relation in `peak_relations`. The paired
        integer is the OSM element ID from which the Summit was created.
        """
        # Create Summit objects for all relations
        for relation in peak_relations:
            # Find the peak node member of this relations, should be exactly one
            found_peak_nodes = data_cache.get_relation_member_nodes(
                relation.id, lambda tags: tags.natural == "peak"
            )

            if not found_peak_nodes:
                # The relation doesn't reference a "peak" node. This means we cannot get a position
                # for it, which is bad.
                raise DataProcessingError(
                    f"No peak node can be loaded for relation '{relation.tags.name}'. Does it "
                    "contain one at all?",
                )
            if len(found_peak_nodes) > 1:
                # Not sure what this means, maybe we have to choose the correct one in the future?
                # For now, just log a warning to find some examples.
                _logger.warning(
                    "Summit relation '%s' has multiple peak nodes (%d), using only the first one.",
                    relation.tags.name,
                    len(found_peak_nodes),
                )
            peak_node = found_peak_nodes[0]

            if self.__is_forbidden_node(peak_node):
                continue

            yield (
                relation.id,
                self._route_data_factory.create_summit(
                    official_name=relation.tags.name,
                    alternate_names=relation.tags.get_alternate_names(),
                    position=GeoPosition.from_decimal_degree(peak_node.lat, peak_node.lon),
                    sector=data_cache.get_sector_name(relation.id),
                ),
            )

    def __create_summits_from_nodes(
        self,
        data_cache: _OsmDataCache,
        osm_nodes: Iterable[OverpassNode],
    ) -> Iterator[tuple[int, Summit]]:
        """
        Creates (and yields) a Summit object for each node in `osm_nodes`. The paired integer is the
        OSM element ID from which the Summit was created.
        """
        for summit_element in osm_nodes:
            if self.__is_forbidden_node(summit_element):
                continue

            yield (
                summit_element.id,
                self._route_data_factory.create_summit(
                    official_name=summit_element.tags.name,
                    alternate_names=summit_element.tags.get_alternate_names(),
                    position=GeoPosition.from_decimal_degree(
                        summit_element.lat, summit_element.lon
                    ),
                    sector=data_cache.get_sector_name(summit_element.id),
                ),
            )

    def __store_external_source_attribution(self, pipe: Pipe) -> None:
        pipe.add_source(self._EXTERNAL_SOURCE_DESCRIPTION)

    def __store_summits(
        self, pipe: Pipe, summits: Iterable[tuple[int, Summit]]
    ) -> dict[int, SummitInstanceId]:
        """
        Store all given `summits` into the given `pipe`. Returns a mapping of each summit's OSM
        element ID to the assigned pipe ID. This mapping is needed to e.g. assign routes later on.
        """
        osm_to_pipe_map: dict[int, SummitInstanceId] = {}
        for osm_id, summit in summits:
            try:
                osm_to_pipe_map[osm_id] = pipe.add_summit(summit)
            except MergeConflictError as e:
                _logger.warning(e)
        return osm_to_pipe_map


class _OsmDataCache:
    """
    Container that retrieves all necessary data from OSM and provides them to the filter. It does
    some mapping (e.g. "which nodes are assigned to which relations"), but no further processing.

    Unlike a usual cache, this class does not retrieve missing data as needed but gathers all data
    at once, and only on explicit request. The main goal is to limit OSM API requests to the
    absolutely necessary minimum. That also means, that `retrieve_all_data()` must be called first
    (and only once), otherwise the other methods won't return any results.
    """

    _peak_nodes: dict[int, OverpassNode]
    """
    List of nodes that each describe the complete data of a single summit.
    """

    _peak_relations: list[OverpassRelation]
    """
    List of relations that each describe a single summit.

    Relations may contain additional points besides the peak, like route bottoms or bolts.
    """

    _relations_member_nodes: dict[int, list[OverpassNode]]
    """
    Map of all node objects that are members of a crag relation and have been not been processed
    yet. The dict key is the OSM ID of the relation (i.e. the summit itself).

    To reduce the load on the Overpass server, we fetch all relation members in one query and
    filter them manually as needed. At least in the future, we are probably interested in most of
    those nodes, so we don't retrieve much unnecessary data.
    """

    _sector_names: dict[int, str]
    """ Maps actual sector names to their internal ID. """

    _sector_map: dict[int, int]
    """
    Assigns sector ID to certain feature (node or relation) IDs, i.e. the setcor this feature
    belongs to.
    """

    def __init__(self) -> None:
        self._sector_map = {}
        self._sector_names = {}
        self._peak_nodes = {}
        self._peak_relations = []
        self._relations_member_nodes = {}

    def retrieve_all_data(self, api_receiver: OsmApiReceiver) -> None:
        """
        Retrieve all necessary data from OSM. Must be called exactly once before calling any of the
        other methods.
        """
        # Get the OSM ID of the geographical area to query
        area_id = self.__get_area_id(api_receiver)

        # Get all OSM nodes and relations for that area
        osm_elements = self.__get_osm_summit_elements(api_receiver, area_id)
        _logger.debug("Retrieved %d OSM elements", len(osm_elements))
        if not osm_elements:
            return

        # Separate nodes and relations
        self._peak_nodes, self._peak_relations = self.__separate_elements_by_type(osm_elements)

        # Get all parent relations (=sectors) of the given node and relation IDs
        self._sector_names, self._sector_map = self.__retrieve_sector_relations(
            api_receiver,
            self._peak_nodes.keys(),
            [rel.id for rel in self._peak_relations],
        )

        # Move peak that are actually part of a relation into the `_relations_member_nodes` list
        self._relations_member_nodes = self.__extract_available_relation_member_nodes(
            self._peak_nodes,
            self._peak_relations,
        )

        # Retrieve all missing peak relation members (relation members)
        self.__retrieve_referenced_nodes(
            api_receiver, self._relations_member_nodes, self._peak_relations
        )
        _logger.debug("Retrieved all referenced nodes")

    def get_peak_nodes(self) -> list[OverpassNode]:
        """
        Return raw data of all retrieved peak nodes.
        """
        return list(self._peak_nodes.values())

    def get_peak_relations(self) -> list[OverpassRelation]:
        """
        Return raw data of all retrieved peak relations.
        """
        return self._peak_relations

    def get_relation_member_nodes(
        self, relation_id: int, predicate: Callable[[OverpassTags], bool] | None
    ) -> list[OverpassNode]:
        """
        Return a list of all member node raw data assigned to the given relation. The given relation
        ID must be of one of the relation returned by `get_peak_relations()`. If it is not, a
        KeyError is raised.

        The `predicate` parameter allows to optionally filter the returned nodes by tags, i.e. only
        member nodes with all of the given tag values (and optionally additional ones) are returned.
        It is a callable that returns True for nodes that shall be returned.
        """
        if predicate is None:
            predicate = partial(lambda _t: True)

        return [node for node in self._relations_member_nodes[relation_id] if predicate(node.tags)]

    def get_sector_name(self, osm_id: int) -> str | None:
        sector_id = self._sector_map.get(osm_id)
        if sector_id is not None:
            return self._sector_names.get(sector_id)
        return None

    def __get_area_id(self, api_receiver: OsmApiReceiver) -> int:
        area_name: Final = "Sächsische Schweiz"
        return int(api_receiver.retrieve_area_by_name(area_name).osm_id)

    def __get_osm_summit_elements(
        self, api_receiver: OsmApiReceiver, area_id: int
    ) -> list[OverpassElement]:
        """
        Retrieve all elements that represent Summits from OSM.
        Each summit is either a single node or a relation.
        """
        common_tags: Final = {"sport": "climbing", "climbing:trad": "yes"}
        element_filter: Final = {
            OsmObjectTypes.node: {"natural": "peak"} | common_tags,
            OsmObjectTypes.relation: {"type": "site", "climbing": "crag"} | common_tags,
        }
        return api_receiver.retrieve_elements_from_area(area_id, element_filter)

    def __separate_elements_by_type(
        self, osm_elements: Collection[OverpassElement]
    ) -> tuple[dict[int, OverpassNode], list[OverpassRelation]]:
        """
        Splits all nodes and relations from `osm_elements` into two separate collections, because
        they have to be handled differently. Returns a tuple of all nodes and all relations:
         - First: Dict of node IDs and OSM node elements
         - Second: List of OSM relation elements
        """
        osm_nodes = {elem.id: elem for elem in osm_elements if isinstance(elem, OverpassNode)}
        osm_relations = [elem for elem in osm_elements if isinstance(elem, OverpassRelation)]
        if (len(osm_nodes) + len(osm_relations)) < len(osm_elements):
            _logger.warning(
                "Retrieved %d unexpected elements from OSM, they will be ignored",
                len(osm_elements) - len(osm_nodes) - len(osm_relations),
            )
        return osm_nodes, osm_relations

    def __retrieve_sector_relations(
        self,
        api_receiver: OsmApiReceiver,
        node_ids: Collection[int],
        relation_ids: Collection[int],
    ) -> tuple[dict[int, str], dict[int, int]]:
        """
        Retrieves the sectors the given OSM elements belong to. The first returned value is a dict
        of sector ID and sector name, the second value is a dict of element IDs (dict key) and the
        ID of the sector they belong to (dict value).
        """
        parent_relation_elements = api_receiver.retrieve_parent_relations(
            node_ids, relation_ids, rel_filter={"climbing": "area", "type": "site"}
        )
        sector_names = {rel.id: rel.tags.name for rel in parent_relation_elements if rel.tags.name}
        all_member_ids = set(list(node_ids) + list(relation_ids))
        sector_assignment = {
            member.ref: sector_relation.id
            for sector_relation in parent_relation_elements
            for member in sector_relation.members
            if member.ref in all_member_ids
        }
        return sector_names, sector_assignment

    def __extract_available_relation_member_nodes(
        self,
        peak_nodes: dict[int, OverpassNode],
        peak_relations: list[OverpassRelation],
    ) -> dict[int, list[OverpassNode]]:
        """
        Removes all nodes that are referenced by one of the given `peak_relations` from `peak_nodes`
        and returns them assigned to their corresponding relation ID. These are peaks that have
        climbing tags on the peak node as well as on the relation.
        """
        already_available_node_ids = set(peak_nodes.keys())
        already_available_relation_members: dict[int, list[OverpassNode]] = {}
        for relation in peak_relations:
            referenced_node_ids = {item.ref for item in relation.iter_members(OsmObjectTypes.node)}
            for nodeid in referenced_node_ids & already_available_node_ids:
                already_available_node_ids.discard(nodeid)
                osm_node = peak_nodes.pop(nodeid)
                already_available_relation_members.setdefault(relation.id, []).append(osm_node)

        return already_available_relation_members

    def __retrieve_referenced_nodes(
        self,
        api_receiver: OsmApiReceiver,
        relation_member_nodes: dict[int, list[OverpassNode]],
        peak_relations: Collection[OverpassRelation],
    ) -> None:
        """
        Retrieves all peak node elements that are referenced by the relations within
        `peak_relations` and stores them into `relation_member_nodes`. Does only one OSM request,
        and does not re-retrieve nodes that are already there.
        """
        # Get a flat set of all referenced nodes that we already have
        already_available_node_ids = {
            node.id for nodes in relation_member_nodes.values() for node in nodes
        }

        # Get a flat set of all relation member node IDs that we don't have yet
        missing_node_ids = {
            item.ref
            for relation in peak_relations
            for item in relation.iter_members(OsmObjectTypes.node)
            if item.ref not in already_available_node_ids
        }

        # Retrieve all missing nodes, if any
        retrieved_nodes = (
            {
                node.id: node
                for node in api_receiver.retrieve_nodes_by_ids(
                    osm_ids=missing_node_ids,
                    node_filter={},
                )
            }
            if missing_node_ids
            else {}
        )

        for relation in peak_relations:
            relation_member_nodes.setdefault(relation.id, []).extend(
                [
                    retrieved_nodes[member.ref]
                    for member in relation.iter_members(OsmObjectTypes.node)
                    if member.ref in retrieved_nodes
                ]
            )
