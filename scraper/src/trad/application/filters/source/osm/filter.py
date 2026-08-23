"""
Filter for importing OSM data. Data is retrieved from Nominatim and Overpass.
"""

from collections.abc import Callable, Collection, Iterable, Iterator
from itertools import chain
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
)
from trad.application.filters.source.route_data_factory import RouteDataFactory
from trad.kernel.boundaries.pipes import Pipe
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

    _OVERPASS_PEAK_NODE_TAGS: Final = {"natural": "peak"}
    """ OSM node tags by which we recognize a single summit point. """

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

        # Get the OSM ID of the geographical area to query
        area_id = self.__get_area_id()

        # Get all OSM nodes and relations for that area
        osm_elements = self.__get_osm_summit_elements(area_id)
        _logger.debug("Retrieved %d OSM elements", len(osm_elements))
        if not osm_elements:
            return

        # Separate nodes and relations
        osm_nodes, osm_relations = self.__separate_elements_by_type(osm_elements)

        # Get all parent relations (=sectors) of the given node and relation IDs
        sector_names, sector_map = self.__retrieve_sector_relations(
            osm_nodes.keys(),
            [rel.id for rel in osm_relations],
        )

        # Retrieve all missing peak nodes (relation members)
        self.__retrieve_missing_nodes(osm_nodes, osm_relations)
        _logger.debug("Retrieved referenced OSM peak nodes")

        # Remove all peak nodes that must never be accessed at all
        # Note: We don't expect such nodes to be part of a crag relation because it doesn't seem to
        # make sense, that's why we purposely don't handle this case. If it does happen, though,
        # trying to process such a relation fails with an exception.
        self.__remove_forbidden_nodes(osm_nodes)

        def get_sector_name(osm_id: int) -> str | None:
            sector_id = sector_map.get(osm_id)
            if sector_id is not None:
                return sector_names.get(sector_id)
            return None

        # Create Summit objects for all relations
        # This removes all processed nodes from osm_nodes because we don't want to create another
        # Summit object for them later.
        summits_from_relations = self.__create_summits_from_relations(
            osm_nodes, osm_relations, get_sector_name
        )
        # Create Summit objects for all left-over peak nodes (which do not belong to any relation)
        summits_from_nodes = self.__create_summits_from_nodes(osm_nodes.values(), get_sector_name)

        # Send all summits to the pipe
        self.__store_summits(output_pipe, chain(summits_from_relations, summits_from_nodes))
        _logger.debug(
            "Processed summits from %d relations and %d nodes", len(osm_relations), len(osm_nodes)
        )

        _logger.debug("'%s' filter finished", self.get_name())

    def __get_area_id(self) -> int:
        area_name: Final = "Sächsische Schweiz"
        return int(self._osm_api_receiver.retrieve_area_by_name(area_name).osm_id)

    def __get_osm_summit_elements(self, area_id: int) -> list[OverpassElement]:
        common_tags: Final = {"sport": "climbing", "climbing:trad": "yes"}
        element_filter: Final = {
            OsmObjectTypes.node: self._OVERPASS_PEAK_NODE_TAGS | common_tags,
            OsmObjectTypes.relation: {"type": "site", "climbing": "crag"} | common_tags,
        }
        return self._osm_api_receiver.retrieve_elements_from_area(area_id, element_filter)

    def __separate_elements_by_type(
        self, osm_elements: Collection[OverpassElement]
    ) -> tuple[dict[int, OverpassNode], list[OverpassRelation]]:
        """
        Extracts all nodes and relations from `osm_element` into two separate collections, because
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
        self, node_ids: Collection[int], relation_ids: Collection[int]
    ) -> tuple[dict[int, str], dict[int, int]]:
        """
        Retrieves the sectors the given OSM elements belong to. The first returned value is a dict
        of sector ID and sector name, the second value is a dict of element IDs (dict key) and the
        ID of the sector they belong to (dict value).
        """
        parent_relation_elements = self._osm_api_receiver.retrieve_parent_relations(
            node_ids, relation_ids, rel_filter={"climbing": "area", "type": "site"}
        )
        sector_names = {rel.id: rel.tags.name for rel in parent_relation_elements}
        all_member_ids = set(list(node_ids) + list(relation_ids))
        sector_assignment = {
            member.ref: sector_relation.id
            for sector_relation in parent_relation_elements
            for member in sector_relation.members
            if member.ref in all_member_ids
        }
        return sector_names, sector_assignment

    def __retrieve_missing_nodes(
        self, osm_nodes: dict[int, OverpassNode], osm_relations: Collection[OverpassRelation]
    ) -> None:
        """
        Retrieves all peak node elements that are referenced by the relations within `osm_relations`
        and adds them into `osm_nodes`. Does only one OSM request, and does not re-retrieve nodes
        that are already there.

        :param osm_nodes: Maps OSM node instances to their OSM ID. Will be extended.
        """
        # Get all relation member node IDs that are not already available.
        missing_nodes = [
            item.ref
            for relation in osm_relations
            for item in relation.iter_members(OsmObjectTypes.node)
            if item.ref not in osm_nodes
        ]
        # Retrieve all missing nodes (should be one per relation at the most)
        osm_nodes.update(
            {
                node.id: node
                for node in self._osm_api_receiver.retrieve_nodes_by_ids(
                    osm_ids=missing_nodes,
                    node_filter=self._OVERPASS_PEAK_NODE_TAGS,
                )
            }
            if missing_nodes
            else {}
        )

    def __remove_forbidden_nodes(self, osm_nodes: dict[int, OverpassNode]) -> None:
        """
        Removes all peak nodes that may never be climbed on from `osm_nodes`. The check is done by
        means of legal restrictions, i.e. the 'access' tag.
        Nodes with partial (e.g. seasonal) restrictions are *not* removed because they can be
        accessed legally (just not always).
        """
        total_access_restrictions: Final = ["no", "private"]

        ids_to_delete: list[int] = [
            node_id
            for node_id, node in osm_nodes.items()
            if node.tags.access in total_access_restrictions
        ]
        for node_id in ids_to_delete:
            del osm_nodes[node_id]

    def __create_summits_from_relations(
        self,
        osm_nodes: dict[int, OverpassNode],
        osm_relations: Collection[OverpassRelation],
        get_sector_name: Callable[[int], str | None],
    ) -> Iterator[Summit]:
        """
        Creates (and yields) a Summit object for each relation in `osm_relations`, using the peaks
        from `osm_nodes`. The peak node elements that correspond to the processed relations are
        removed from `osm_nodes`.
        """
        # Create Summit objects for all relations
        for relation in osm_relations:
            # Find the peak node member of this relations, should be exactly one
            found_peak_nodes = [
                item.ref
                for item in relation.iter_members(OsmObjectTypes.node)
                if item.ref in osm_nodes
            ]
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
            peak_node = osm_nodes[found_peak_nodes[0]]

            yield self._route_data_factory.create_summit(
                official_name=relation.tags.name,
                alternate_names=relation.tags.get_alternate_names(),
                position=GeoPosition.from_decimal_degree(peak_node.lat, peak_node.lon),
                sector=get_sector_name(relation.id),
            )
            # Remove this peak node from osm_nodes because it is not needed anymore
            osm_nodes.pop(peak_node.id)

    def __create_summits_from_nodes(
        self,
        osm_nodes: Iterable[OverpassNode],
        get_sector_name: Callable[[int], str | None],
    ) -> Iterator[Summit]:
        """
        Creates (and yields) a Summit object for each node in `osm_nodes`.
        """
        for summit_element in osm_nodes:
            yield self._route_data_factory.create_summit(
                official_name=summit_element.tags.name,
                alternate_names=summit_element.tags.get_alternate_names(),
                position=GeoPosition.from_decimal_degree(summit_element.lat, summit_element.lon),
                sector=get_sector_name(summit_element.id),
            )

    def __store_external_source_attribution(self, pipe: Pipe) -> None:
        pipe.add_source(self._EXTERNAL_SOURCE_DESCRIPTION)

    def __store_summits(self, pipe: Pipe, summits: Iterable[Summit]) -> None:
        for summit in summits:
            try:
                pipe.add_summit(summit)
            except MergeConflictError as e:
                _logger.warning(e)
