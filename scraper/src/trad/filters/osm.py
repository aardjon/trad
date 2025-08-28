"""
Filter for importing OSM data.
"""

from collections.abc import Iterable, Iterator
from enum import StrEnum
from logging import getLogger
from typing import Annotated, Final, Literal, override

from pydantic import ValidationError
from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic.main import BaseModel
from pydantic.type_adapter import TypeAdapter

from trad.adapters.boundaries.http import HttpNetworkingBoundary, HttpRequestError, JsonData
from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.core.entities import Summit
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

    Data is retrieved from Nominatim and Overpass. The Nominatim API documentation can be found at
    https://nominatim.org/release-docs/develop/api/Overview/
    For further information about the JSON format sent by the Overpass API, please refer to:
     - https://wiki.openstreetmap.org/wiki/OSM_JSON
     - https://dev.overpass-api.de/output_formats.html#json
     - https://wiki.openstreetmap.org/wiki/API_v0.6#JSON_Format
    """

    _NOMINATIM_API_ENDPOINT: Final = "https://nominatim.openstreetmap.org/search"
    _OVERPASS_API_ENDPOINT: Final = "https://overpass-api.de/api/interpreter"

    @override
    def __init__(self, dependency_provider: DependencyProvider) -> None:
        super().__init__(dependency_provider)
        self._http_boundary = dependency_provider.provide(HttpNetworkingBoundary)

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
        nominatim_json_data = self.__get_nominatim_area_data()
        area_id = self.__process_nominatim_response(nominatim_json_data)
        overpass_json_data = self.__get_overpass_summit_nodes(area_id)
        summits = self.__process_overpass_response(overpass_json_data)
        self.__store_summits(pipe, summits)
        _logger.debug("'%s' filter finished", self.get_name())

    def __get_nominatim_area_data(self) -> JsonData:
        area_name: Final = "Sächsische Schweiz"
        _logger.debug("Retrieving ID for area '%s' from Nominatim", area_name)
        try:
            response_json = self._http_boundary.retrieve_json_resource(
                url=self._NOMINATIM_API_ENDPOINT,
                url_params={"q": area_name, "limit": 1, "format": "jsonv2"},
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Nominatim request failed") from e
        return response_json

    def __process_nominatim_response(self, json_data: JsonData) -> int:
        type_adapter = TypeAdapter(list[_NominatimArea])
        try:
            area_elements = type_adapter.validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected data from Nominatim") from e
        if not (area_elements := type_adapter.validate_json(json_data, strict=True)):
            raise DataProcessingError("Received an empty area list from Nominatim")
        return int(area_elements[0].osm_id)

    def __get_overpass_summit_nodes(self, area_id: int) -> JsonData:
        node_tags: Final = {
            "natural": "peak",
            "climbing:trad": "yes",
        }
        _logger.debug("Querying all summits within area ID %s from Overpass", area_id)
        tag_filter = "".join(f'["{t}"="{v}"]' for t, v in node_tags.items())
        query = f"""
            [out:json][timeout:25];
            area({area_id})->.searchArea;
            (
                node{tag_filter}(area.searchArea);
            );
            out body;
        """
        try:
            return self._http_boundary.retrieve_json_resource(
                url=self._OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Overpass request failed") from e

    def __process_overpass_response(self, json_data: JsonData) -> Iterator[Summit]:
        try:
            osm_response = _OverpassResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected data from Overpass") from e

        _logger.debug("Processing %d summits", len(osm_response.elements))
        for element in osm_response.elements:
            yield element.create_summit()

    def __store_summits(self, pipe: Pipe, summits: Iterable[Summit]) -> None:
        for summit in summits:
            try:
                pipe.add_or_enrich_summit(summit)
            except MergeConflictError as e:
                _logger.warning(e)
