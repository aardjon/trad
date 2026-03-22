"""
Filter for importing OSM data.

Data is retrieved from Nominatim and Overpass. The Nominatim API documentation can be found at
    https://nominatim.org/release-docs/develop/api/Overview/
For further information about the JSON format sent by the Overpass API, please refer to:
     - https://wiki.openstreetmap.org/wiki/OSM_JSON
     - https://dev.overpass-api.de/output_formats.html#json
     - https://wiki.openstreetmap.org/wiki/API_v0.6#JSON_Format
Interactive Overpass query editor: https://overpass-turbo.eu/
"""

from collections.abc import Callable, Collection, Iterable, Iterator
from enum import StrEnum
from itertools import chain
from logging import getLogger
from typing import Annotated, Final, Literal, override

from pydantic import ValidationError
from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic.main import BaseModel
from pydantic.type_adapter import TypeAdapter

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.application.filters._base import SourceFilter
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import ExternalSource, GeoPosition, Summit
from trad.kernel.errors import DataProcessingError, DataRetrievalError, MergeConflictError

_logger = getLogger(__name__)


class _OsmObjectTypes(StrEnum):
    """
    The supported types of OSM objects. The string values are the values Overpass/OSM sends as the
    `type` field JSON value.
    """

    node = "node"
    """ A single point. """

    relation = "relation"
    """ An arbitrary collection of several other objects. """


class _ReadOnlyPydanticModel(BaseModel):
    """
    Base class for Pydantic models that cannot be manipulated. This is the case for all data
    retrieved from some remote service.
    """

    model_config = ConfigDict(frozen=True)


class _NominatimArea(_ReadOnlyPydanticModel):
    osm_id: int


class _OverpassTags(_ReadOnlyPydanticModel):
    """
    Deserialized representation of the tags of a single OSM object. Currently we are mainly
    interested in the names, but this may change in the future.
    See the OSM wiki for tag documentation:
     - Possible name keys: https://wiki.openstreetmap.org/wiki/Names#Name_keys

    Some of the most important points:
     - The 'name' is the most-common, usual name, i.e. the one with the highest priority
     - 'official_name' can be used for somewhat uncommon or long offical names that are not used
       that often
     - 'name' should be exactly one single name
     - At least 'alt_name' may be a ; separated list with several names
    """

    name: str
    """ The default and most important name to use. """
    official_name: str | None = None
    """ If the official name is not very common. """
    alt_name: str | None = None
    loc_name: str | None = None
    nickname: str | None = None
    short_name: str | None = None

    access: str | None = None
    """
    Legal access restrictions, if any (as of https://wiki.openstreetmap.org/wiki/Key:access). If
    missing, everyone is officially allowed to climb here.
    """

    def get_alternate_names(self) -> list[str]:
        """
        Return a list of all "alternate" (i.e. non-official) names assigned to this object.
        """
        names = []
        for tag_value in (
            self.alt_name,
            self.official_name,
            self.loc_name,
            self.short_name,
            self.nickname,
        ):
            if tag_value:
                names.extend(self.split_value_list(tag_value))
        return names

    def split_value_list(self, tag_value: str | None) -> list[str]:
        """
        Return all single values from the given tag value as a list.

        Although regular strings, some tags may contain a list of several valie, which can be split
        using this method.
        """
        if not tag_value:
            return []
        return [value.strip() for value in tag_value.split(";")]


class _OverpassNode(_ReadOnlyPydanticModel):
    type: Literal[_OsmObjectTypes.node]
    id: int
    lat: float
    lon: float
    tags: _OverpassTags


class _OverpassRelationMember(_ReadOnlyPydanticModel):
    type: str
    ref: int


class _OverpassRelation(_ReadOnlyPydanticModel):
    id: int
    type: Literal[_OsmObjectTypes.relation]
    members: list[_OverpassRelationMember]
    tags: _OverpassTags

    def iter_members(self, type_filter: str) -> Iterator[_OverpassRelationMember]:
        """
        Iterate over all relation members of the type requested by `type_filter` (ignoring all
        others).
        """
        for item in self.members:
            if item.type == type_filter:
                yield item


_OverpassElement = Annotated[_OverpassNode | _OverpassRelation, Field(discriminator="type")]
"""
A single item of an Overpass response's 'elements' list: Can be either a node or a relation.
"""


class _OverpassElementsResponse(_ReadOnlyPydanticModel):
    elements: list[_OverpassElement]


class _OverpassNodesResponse(_ReadOnlyPydanticModel):
    elements: list[_OverpassNode]


class _OverpassRelationsResponse(_ReadOnlyPydanticModel):
    elements: list[_OverpassRelation]


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

    def __get_osm_summit_elements(self, area_id: int) -> list[_OverpassElement]:
        common_tags: Final = {"sport": "climbing", "climbing:trad": "yes"}
        element_filter: Final = {
            _OsmObjectTypes.node: self._OVERPASS_PEAK_NODE_TAGS | common_tags,
            _OsmObjectTypes.relation: {"type": "site", "climbing": "crag"} | common_tags,
        }
        return self._osm_api_receiver.retrieve_elements_from_area(area_id, element_filter)

    def __separate_elements_by_type(
        self, osm_elements: Collection[_OverpassElement]
    ) -> tuple[dict[int, _OverpassNode], list[_OverpassRelation]]:
        """
        Extracts all nodes and relations from `osm_element` into two separate collections, because
        they have to be handled differently. Returns a tuple of all nodes and all relations:
         - First: Dict of node IDs and OSM node elements
         - Second: List of OSM relation elements
        """
        osm_nodes = {elem.id: elem for elem in osm_elements if isinstance(elem, _OverpassNode)}
        osm_relations = [elem for elem in osm_elements if isinstance(elem, _OverpassRelation)]
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
        self, osm_nodes: dict[int, _OverpassNode], osm_relations: Collection[_OverpassRelation]
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
            for item in relation.iter_members(_OsmObjectTypes.node)
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

    def __remove_forbidden_nodes(self, osm_nodes: dict[int, _OverpassNode]) -> None:
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
        osm_nodes: dict[int, _OverpassNode],
        osm_relations: Collection[_OverpassRelation],
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
                for item in relation.iter_members(_OsmObjectTypes.node)
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

            yield Summit(
                official_name=relation.tags.name,
                alternate_names=relation.tags.get_alternate_names(),
                high_grade_position=GeoPosition.from_decimal_degree(peak_node.lat, peak_node.lon),
                sector=get_sector_name(relation.id),
            )
            # Remove this peak node from osm_nodes because it is not needed anymore
            osm_nodes.pop(peak_node.id)

    def __create_summits_from_nodes(
        self,
        osm_nodes: Iterable[_OverpassNode],
        get_sector_name: Callable[[int], str | None],
    ) -> Iterator[Summit]:
        """
        Creates (and yields) a Summit object for each node in `osm_nodes`.
        """
        for summit_element in osm_nodes:
            yield Summit(
                official_name=summit_element.tags.name,
                alternate_names=summit_element.tags.get_alternate_names(),
                high_grade_position=GeoPosition.from_decimal_degree(
                    summit_element.lat, summit_element.lon
                ),
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


class OsmApiReceiver:
    """
    Represents an endpoint for querying the OpenStreetMap API. Responsible for choosing the correct
    API for the requested usecase, for providing/creating all necessary options, query strings etc.
    and for parsing/validating the reponses. All methods of this class return Pydantic model objects
    (derived from _ReadOnlyPydanticModel), never plain JSON strings.
    """

    _NOMINATIM_API_ENDPOINT: Final = "https://nominatim.openstreetmap.org/search"
    _OVERPASS_API_ENDPOINT: Final = "https://overpass-api.de/api/interpreter"
    _OVERPASS_TIMEOUT: Final = 25
    """ Overpass query timeout in seconds. """

    def __init__(self, http_boundary: HttpNetworkingBoundary):
        """Create a new OsmApiReceiver instance which uses the given HTTP boundary instance."""
        self._http_boundary = http_boundary

    def retrieve_area_by_name(self, area_name: str) -> _NominatimArea:
        """
        Requests and returns the area object that represents the area named `area_name`. This is
        done querying Nominatim.
        If no such area was found (or the response cannot be parsed), a DataProcessingError is
        raised. If the area name is ambiguous, only the first retrieved element is returned. In case
        of network/connection problems, a DataRetrievalError is raised.
        """
        _logger.debug("Retrieving ID for area '%s' from Nominatim", area_name)
        try:
            response_json = self._http_boundary.retrieve_json_resource(
                url=self._NOMINATIM_API_ENDPOINT,
                url_params={"q": area_name, "limit": 1, "format": "jsonv2"},
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Nominatim request failed") from e

        type_adapter = TypeAdapter(list[_NominatimArea])
        try:
            area_elements = type_adapter.validate_json(response_json, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected data from Nominatim") from e
        if not area_elements:
            raise DataProcessingError("Received an empty area list from Nominatim")
        if len(area_elements) > 1:
            _logger.warning(
                "Found %d areas named %s, using only the first one!", len(area_elements), area_name
            )
        return area_elements[0]

    def retrieve_elements_from_area(
        self, area_id: int, element_filter: dict[_OsmObjectTypes, dict[str, str]]
    ) -> list[_OverpassElement]:
        """
        Requests and returns all elements within the area identified by `area_id`. This is done by
        querying the Overpass API.

        `element_filter` should be used to filter the returned elements: The outer dict keys are the
        element types to request, and the assigned (value) dict defines OSM tags (dict keys) and
        values (dict values) and element must match to be returned.

        Returns an empty list if no matches were found. Raises DataProcessingError in case of any
        data processing error, or DataRetrievalError in case of network/connection problems.
        """
        _logger.debug(
            "Querying elements within area ID %s from Overpass, using filter %s",
            area_id,
            element_filter,
        )

        element_clauses = []
        for object_type, tags in element_filter.items():
            tag_filter = "".join(f'["{t}"="{v}"]' for t, v in tags.items())
            element_clauses.append(f"{object_type}{tag_filter}(area.searchArea);")

        element_query = "\n".join(element_clauses)
        full_query = self.__build_overpass_query(
            f"""
            area({area_id})->.searchArea;
            (
                {element_query}
            );
            """
        )

        try:
            json_data = self._http_boundary.retrieve_json_resource(
                url=self._OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={full_query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Overpass request failed") from e

        try:
            osm_response = _OverpassElementsResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected data from Overpass") from e

        return osm_response.elements

    def retrieve_nodes_by_ids(
        self,
        osm_ids: Collection[int],
        node_filter: dict[str, str],
    ) -> list[_OverpassNode]:
        """
        Request and return the node objects that are identified by the given `osm_ids`. This is done
        by querying the Overpass API.

        `node_filter` can be used to filter the returned elements: It defines the OSM tags (dict
        keys) and values (dict values) a node must provide to be returned.

        Returns an empty list if no matches were found. Raises DataProcessingError in case of any
        data processing error, or DataRetrievalError in case of network/connection problems.
        """
        _logger.debug("Querying %d IDs from Overpass, using filter %s", len(osm_ids), node_filter)

        tag_filter = "".join(f'["{t}"="{v}"]' for t, v in node_filter.items())
        node_requests = "\n".join(f"node({nid}){tag_filter};" for nid in osm_ids)
        query = self.__build_overpass_query(
            f"""
            (
                {node_requests}
            );
            """
        )

        try:
            json_data = self._http_boundary.retrieve_json_resource(
                url=self._OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Overpass request failed") from e

        try:
            osm_response = _OverpassNodesResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected node data from Overpass") from e

        return osm_response.elements

    def retrieve_parent_relations(
        self,
        node_ids: Collection[int],
        relation_ids: Collection[int],
        rel_filter: dict[str, str],
    ) -> list[_OverpassRelation]:
        """
        Request and return the relation objects that are the parents of the node and relation
        objects identified by `node_ids` and `relation_ids`. This is done by querying the Overpass
        API. `rel_filter` defines the OSM tags (dict keys) and values (dict values) a relation must
        provide to be returned.

        Returns an empty list if no matches were found. Raises DataProcessingError in case of any
        data processing error, or DataRetrievalError in case of network/connection problems.
        """
        _logger.debug(
            "Querying parent relations of %d IDs from Overpass, using filter %s",
            len(node_ids) + len(relation_ids),
            rel_filter,
        )

        tag_filter = "".join(f'["{t}"="{v}"]' for t, v in rel_filter.items())
        relation_id_str = ", ".join(str(i) for i in relation_ids)
        node_id_str = ", ".join(str(i) for i in node_ids)
        query = self.__build_overpass_query(
            f"""
            (
                relation(id: {relation_id_str});
            )->.rels;
            (
                node(id: {node_id_str});
            )->.nodes;

            (
                rel(br.rels);
                rel(bn.nodes);
            )->.all;

            relation.all{tag_filter}->.filtered;
            .filtered
            """
        )

        try:
            json_data = self._http_boundary.retrieve_json_resource(
                url=self._OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Parent relation Overpass request failed") from e

        try:
            osm_response = _OverpassRelationsResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected node data from Overpass") from e

        return osm_response.elements

    def __build_overpass_query(self, element_query: str) -> str:
        """
        Create and return a complete query string which can be sent to the Overpass API.
        `element_query` is the query part that actually requests data elements. This methos adds
        necessary headers or options and returns the resulting string.
        """
        return f"""
            [out:json][timeout:{self._OVERPASS_TIMEOUT}];
            {element_query}
            out body;
        """
