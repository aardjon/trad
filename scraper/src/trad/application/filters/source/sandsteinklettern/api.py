"""
Contains all details of the external JSON API, i.e. the endpoint URLs as well as Pydantic models
representing the retrieved data.

For some documentation, have a look at:
- http://db-sandsteinklettern.gipfelbuch.de/bewert.htm for documentation of some of the JSON fields
- http://db-sandsteinklettern.gipfelbuch.de/adrhinw.htm for general information about the data

The yacguide sources can also give hints on how to interprete/parse certain fields:
https://github.com/YacGroup/yacguide/
"""

from datetime import datetime
from enum import StrEnum
from logging import getLogger
from typing import Annotated, Final, NewType

from pydantic import ValidationError
from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic.functional_validators import BeforeValidator
from pydantic.main import BaseModel
from pydantic.type_adapter import TypeAdapter

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.kernel.errors import DataProcessingError, DataRetrievalError

_logger = getLogger(__name__)

ApiItemIdType = NewType("ApiItemIdType", str)
"""
Type for uniquely identifying a single item in the external database.
"""


class _ReadOnlyPydanticModel(BaseModel):
    """
    Base class for Pydantic models that cannot be manipulated. This is the case for all data
    retrieved from some remote service.
    """

    model_config = ConfigDict(frozen=True)


class JsonGebiet(_ReadOnlyPydanticModel):
    """API representation of a single area, jsongebiet.php endpoint."""

    gebiet_id: ApiItemIdType = Field(alias="gebiet_ID")
    gebiet: str


class JsonSektor(_ReadOnlyPydanticModel):
    """API representation of a single sector, jsonteilgebiet.php endpoint."""

    sektor_id: ApiItemIdType = Field(alias="sektor_ID")
    gebietid: ApiItemIdType
    sektorname_d: str


class JsonGipfelTyp(StrEnum):
    """Known values of the "typ" field in the summit JSON response."""

    REGULAR = "G"
    CRAG = "M"
    BOULDER_BLOCK = "B"
    STONE_PIT = "S"
    ALPINE_PEAK = "A"
    UNACKNOWLEDGED = "N"
    CAVE = "H"
    PARKING = "P"
    INN = "W"
    CAMPING = "C"
    OUTLOOK = "T"
    HILL = "E"
    EMERGENCY = "Y"
    BIVOUAC = "D"
    OTHER = "X"
    UNDOCUMENTED = "U"  # TODO(aardjon): What's this?
    UNKNOWN = "UNKNOWN"
    """
    Another, unimplemented value.
    If this occurs, the API has probably been extended with new possible values that need to be
    added to this enum.
    """


class JsonGipfelStatus(StrEnum):
    """Known values of the "status" field in the summit JSON response."""

    OPEN = ""
    CLOSED = "X"
    PARTIALLY_CLOSED = "T"
    OCCASIONALLY_CLOSED = "Z"
    COLLAPSED = "E"
    UNKNOWN = "UNKNOWN"
    """
    Another, unimplemented value.
    If this occurs, the API has probably been extended with new possible values that need to be
    added to this enum.
    """


class JsonGipfel(_ReadOnlyPydanticModel):
    """API representation of a single summit, jsongipfel.php endpoint."""

    gipfel_id: ApiItemIdType = Field(alias="gipfel_ID")
    gipfelname_d: str
    gipfelname_cz: str
    typ: Annotated[JsonGipfelTyp, BeforeValidator(_validate_typ)]
    vgrd: str  # 14.04164
    ngrd: str  # 50.86254
    status: Annotated[JsonGipfelStatus, BeforeValidator(_validate_status)]

    @staticmethod
    def _validate_typ(json_value: str) -> JsonGipfelTyp:
        if json_value in JsonGipfelTyp:
            return JsonGipfelTyp(json_value)
        _logger.warning("Got unknown value '%s' for JsonGipfelTyp", json_value)
        return JsonGipfelTyp.UNKNOWN

    @staticmethod
    def _validate_status(json_value: str) -> JsonGipfelStatus:
        if json_value in JsonGipfelStatus:
            return JsonGipfelStatus(json_value)
        _logger.warning("Got unknown value '%s' for JsonGipfelStatus", json_value)
        return JsonGipfelStatus.UNKNOWN


class JsonWegStatus(StrEnum):
    """Known values of the "wegstatus" field in the route JSON response."""

    ACKNOWLEDGED = "1"
    TEMP_CLOSED = "2"
    CLOSED = "3"
    FIRST_ASCEND = "4"
    UNACKNOWLEDGED = "5"
    MENTION = "6"
    UNFINISHED = "7"
    UNKNOWN = "UNKOWN"
    """
    Another, unimplemented value.
    If this occurs, the API has probably been extended with new possible values that need to be
    added to this enum.
    """


class JsonWeg(_ReadOnlyPydanticModel):
    """API representation of a single route, jsonwege.php endpoint."""

    weg_id: ApiItemIdType = Field(alias="weg_ID")
    gipfelid: ApiItemIdType
    wegname_d: str
    wegname_cz: str
    schwierigkeit: str
    wegbeschr_d: str
    wegstatus: Annotated[JsonWegStatus, BeforeValidator(_validate_wegstatus)]

    @staticmethod
    def _validate_wegstatus(json_value: str) -> JsonWegStatus:
        if json_value in JsonWegStatus:
            return JsonWegStatus(json_value)
        if json_value == "0":
            # Seems to be the same as "1", that's why we also map it to ACKNOWLEDGED
            return JsonWegStatus.ACKNOWLEDGED
        _logger.warning("Got unknown value '%s' for JsonWegStatus", json_value)
        return JsonWegStatus.UNKNOWN


class JsonKomment(_ReadOnlyPydanticModel):
    """API representation of a single post, jsonkomment.php endpoint."""

    komment_id: ApiItemIdType = Field(alias="komment_ID")
    datum: datetime
    wegid: ApiItemIdType
    kommentar: str
    username: str
    qual: str


class SandsteinkletternApiReceiver:
    """
    Represents an endpoint for querying the sandsteinklettern API. Responsible for choosing the
    correct endpoint for the requested usecase, for providing/creating all necessary options, query
    strings etc. and for parsing/validating the reponses. All methods of this class return Pydantic
    model objects (derived from _ReadOnlyPydanticModel), never plain JSON strings.
    """

    _API_BASE: Final = "http://db-sandsteinklettern.gipfelbuch.de/"
    _API_APP_KEY: Final = "trad"

    def __init__(self, http_boundary: HttpNetworkingBoundary):
        """
        Create a new SandsteinkletternApiReceiver instance which uses the given HTTP boundary
        instance.
        """
        self._http_boundary = http_boundary

    def _create_url_params(
        self, additional_params: dict[str, str | ApiItemIdType]
    ) -> dict[str, str | int]:
        params: dict[str, str | int] = {key: str(value) for key, value in additional_params.items()}
        params.update({"app": self._API_APP_KEY})
        return params

    def _retrieve_item_list[ItemType](
        self,
        endpoint: str,
        endpoint_params: dict[str, str | ApiItemIdType],
        type_adapter: TypeAdapter[list[ItemType]],
    ) -> list[ItemType]:
        try:
            response_json = self._http_boundary.retrieve_json_resource(
                url=f"{self._API_BASE}{endpoint}",
                url_params=self._create_url_params(endpoint_params),
            )
        except HttpRequestError as e:
            raise DataRetrievalError("sandsteinklettern.de request failed") from e

        try:
            elements = type_adapter.validate_json(response_json, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected data from sandsteinklettern.de") from e
        return elements

    def retrieve_areas(self, country_name: str) -> list[JsonGebiet]:
        """Retrieve all areas within the given country."""
        _logger.debug("Retrieving all areas within country '%s'", country_name)
        area_elements = self._retrieve_item_list(
            "jsongebiet.php",
            {"land": country_name},
            type_adapter=TypeAdapter(list[JsonGebiet]),
        )

        if not area_elements:
            raise DataProcessingError("Received an empty area list from sandsteinklettern.de")
        return area_elements

    def retrieve_sectors(self, area_id: ApiItemIdType) -> list[JsonSektor]:
        """Retrieve all sectors within the area with the given `area_id`."""
        _logger.debug("Retrieving all sectors of area '%s'", area_id)
        sector_elements = self._retrieve_item_list(
            "jsonteilgebiet.php",
            {"gebietid": area_id},
            type_adapter=TypeAdapter(list[JsonSektor]),
        )

        if not sector_elements:
            raise DataProcessingError("Received an empty sector list from sandsteinklettern.de")
        return sector_elements

    def retrieve_summits(self, sector_id: ApiItemIdType) -> list[JsonGipfel]:
        """Retrieve all summits within the sector with the given `sector_id`."""
        _logger.debug("Retrieving all summits of sector '%s'", sector_id)
        return self._retrieve_item_list(
            "jsongipfel.php",
            {"sektorid": sector_id},
            type_adapter=TypeAdapter(list[JsonGipfel]),
        )

    def retrieve_routes(self, sector_id: ApiItemIdType) -> list[JsonWeg]:
        """Retrieve all routes within the sector with the given `sector_id`."""
        _logger.debug("Retrieving all routes of sector '%s'", sector_id)
        return self._retrieve_item_list(
            "jsonwege.php",
            {"sektorid": sector_id},
            type_adapter=TypeAdapter(list[JsonWeg]),
        )

    def retrieve_posts(self, sector_id: ApiItemIdType) -> list[JsonKomment]:
        """Retrieve all posts within the sector with the given `sector_id`."""
        _logger.debug("Retrieving all posts of sector '%s'", sector_id)
        return self._retrieve_item_list(
            "jsonkomment.php",
            {"sektorid": sector_id},
            type_adapter=TypeAdapter(list[JsonKomment]),
        )
