"""
Filter for importing OSM data.

Data is retrieved from Nominatim and Overpass. The Nominatim API documentation can be found at
    https://nominatim.org/release-docs/develop/api/Overview/
For further information about the JSON format sent by the Overpass API, please refer to:
     - https://wiki.openstreetmap.org/wiki/OSM_JSON
     - https://dev.overpass-api.de/output_formats.html#json
     - https://wiki.openstreetmap.org/wiki/API_v0.6#JSON_Format
"""

from collections.abc import Collection, Iterable, Iterator
from enum import StrEnum
from logging import getLogger
from typing import Annotated, Final, Literal, override

from pydantic import ValidationError
from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic.main import BaseModel
from pydantic.type_adapter import TypeAdapter

from trad.adapters.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.core.entities import GeoPosition, Summit
from trad.core.errors import DataProcessingError, DataRetrievalError, MergeConflictError
from trad.crosscuttings.di import DependencyProvider

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


class OsmSummitDataFilter(Filter):
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

    _OVERPASS_PEAK_NODE_TAGS: Final = {"natural": "peak"}
    """ OSM node tags by which we recognize a single summit point. """

    @override
    def __init__(self, dependency_provider: DependencyProvider) -> None:
        super().__init__(dependency_provider)
        self._osm_api_receiver = OsmApiReceiver(
            http_boundary=dependency_provider.provide(HttpNetworkingBoundary)
        )

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.IMPORTING

    @override
    def get_name(self) -> str:
        return "OpenStreetMap"

    @override
    def execute_filter(self, pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        area_id = self.__get_area_id()

        # Get all OSM nodes for that area
        osm_elements = self.__get_osm_summit_elements(area_id)
        _logger.debug("Retrieved %d OSM elements", len(osm_elements))

        # Create Summit objects
        summits_from_nodes = self.__create_summits_from_nodes(osm_elements)

        # Send all summits to the pipe
        self.__store_summits(pipe, summits_from_nodes)
        _logger.debug("Processed summits from %d nodes", len(osm_elements))
        _logger.debug("'%s' filter finished", self.get_name())

    def __get_area_id(self) -> int:
        area_name: Final = "Sächsische Schweiz"
        return int(self._osm_api_receiver.retrieve_area_by_name(area_name).osm_id)

    def __get_osm_summit_elements(self, area_id: int) -> list[_OverpassElement]:
        common_tags: Final = {"sport": "climbing", "climbing:trad": "yes"}
        element_filter: Final = {
            _OsmObjectTypes.node: self._OVERPASS_PEAK_NODE_TAGS | common_tags,
        }
        return self._osm_api_receiver.retrieve_elements_from_area(area_id, element_filter)

    def __create_summits_from_nodes(self, osm_nodes: Iterable[_OverpassNode]) -> Iterator[Summit]:
        """
        Creates (and yields) a Summit object for each node in `osm_nodes`.
        """
        for summit_element in osm_nodes:
            yield Summit(
                official_name=summit_element.tags.name,
                alternate_names=summit_element.tags.get_alternate_names(),
                position=GeoPosition.from_decimal_degree(summit_element.lat, summit_element.lon),
            )

    def __store_summits(self, pipe: Pipe, summits: Iterable[Summit]) -> None:
        for summit in summits:
            try:
                pipe.add_or_enrich_summit(summit)
            except MergeConflictError as e:
                _logger.warning(e)


class OsmApiReceiver:
    """
    Represents an endpoint for querying the OpenStreetMap API. Responsible for choosing the correct
    API for the requested usecase, for providing/creating all necessary options, query strings etc.
    and vor parsing/validating the reponses. All methods of this class return Pydantic model objects
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
