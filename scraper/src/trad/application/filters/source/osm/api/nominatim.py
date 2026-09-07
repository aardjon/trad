"""
Contains all details of the external Nominatim API, i.e. the endpoint URLs as well as Pydantic
models representing the retrieved JSON data.

The Nominatim API documentation can be found at
    https://nominatim.org/release-docs/develop/api/Overview/
"""

from typing import Final

from trad.application.filters.source.utils import ReadOnlyPydanticModel

NOMINATIM_API_ENDPOINT: Final = "https://nominatim.openstreetmap.org/search"


class NominatimArea(ReadOnlyPydanticModel):
    """
    A single geographical area in the Nominatim API response.
    """

    osm_id: int
