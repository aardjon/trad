"""
Filter for importing OSM data.
"""

from collections.abc import Iterable, Iterator
from logging import getLogger
from typing import Final, override

from pydantic import ValidationError
from pydantic.config import ConfigDict
from pydantic.main import BaseModel
from pydantic.type_adapter import TypeAdapter

from trad.adapters.boundaries.http import HttpNetworkingBoundary, HttpRequestError, JsonData
from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.core.entities import GeoPosition, Summit
from trad.core.errors import DataProcessingError, DataRetrievalError, MergeConflictError
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class _ReadOnlyPydanticModel(BaseModel):
    """
    Base class for Pydantic models that cannot be manipulated. This is the case for all data
    retrieved from some remote service.
    """

    model_config = ConfigDict(frozen=True)


class _NominatimArea(_ReadOnlyPydanticModel):
    osm_id: int


class _OverpassTag(_ReadOnlyPydanticModel):
    """
    Deserialized representation of the tags of a single OSM "peak" node. See the OSM wiki for tag
    documentation: Possible name keys: https://wiki.openstreetmap.org/wiki/Names#Name_keys

    Some of the most important points:
     - The 'name' is the most-common, usual name, i.e. the one with the highest priority
     - 'official_name' can be used for somewhat uncommon or long offical names that are not used
       that often
     - 'name' should be exactly one single name
     - At least 'alt_name' may be a ; separated list with several names
    """

    name: str  # The default and most important name to use
    official_name: str | None = None  # If the official name is not very common
    alt_name: str | None = None
    loc_name: str | None = None
    nickname: str | None = None
    short_name: str | None = None

    def split_name_list(self, tag_value: str | None) -> list[str]:
        """
        Return all names from the given tag value as a list.

        Although regular strings, some tag values may contain a list of several names, which can be
        split using this method.
        """
        if not tag_value:
            return []
        return [name.strip() for name in tag_value.split(";")]


class _OverpassNode(_ReadOnlyPydanticModel):
    lat: float
    lon: float
    tags: _OverpassTag

    def create_summit(self) -> Summit:
        """
        Create a new Summit object from this JSON data set.
        """
        return Summit(
            official_name=self.tags.name,
            alternate_names=self._get_alternate_names(),
            position=GeoPosition.from_decimal_degree(self.lat, self.lon),
        )

    def _get_alternate_names(self) -> list[str]:
        names = []
        for tag_value in (
            self.tags.alt_name,
            self.tags.official_name,
            self.tags.loc_name,
            self.tags.short_name,
            self.tags.nickname,
        ):
            if tag_value:
                names.extend(self.tags.split_name_list(tag_value))
        return names


class _OverpassResponse(_ReadOnlyPydanticModel):
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
