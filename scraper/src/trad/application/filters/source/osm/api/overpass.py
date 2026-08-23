"""
Contains all details of the external Overpass API, i.e. the endpoint URLs as well as Pydantic models
representing the retrieved JSON data.

For some documentation, have a look at:
 - https://wiki.openstreetmap.org/wiki/OSM_JSON
 - https://dev.overpass-api.de/output_formats.html#json
 - https://wiki.openstreetmap.org/wiki/API_v0.6#JSON_Format
"""

from collections.abc import Iterator
from enum import StrEnum
from typing import Annotated, Final, Literal

from pydantic.fields import Field

from trad.application.filters.source.utils import ReadOnlyPydanticModel

OVERPASS_API_ENDPOINT: Final = "https://overpass-api.de/api/interpreter"


class OsmObjectTypes(StrEnum):
    """
    The supported types of OSM objects. The string values are the values Overpass/OSM sends as the
    `type` field JSON value.
    """

    node = "node"
    """ A single point. """

    relation = "relation"
    """ An arbitrary collection of several other objects. """


class OverpassTags(ReadOnlyPydanticModel):
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


class OverpassNode(ReadOnlyPydanticModel):
    type: Literal[OsmObjectTypes.node]
    id: int
    lat: float
    lon: float
    tags: OverpassTags


class OverpassRelationMember(ReadOnlyPydanticModel):
    type: str
    ref: int


class OverpassRelation(ReadOnlyPydanticModel):
    id: int
    type: Literal[OsmObjectTypes.relation]
    members: list[OverpassRelationMember]
    tags: OverpassTags

    def iter_members(self, type_filter: str) -> Iterator[OverpassRelationMember]:
        """
        Iterate over all relation members of the type requested by `type_filter` (ignoring all
        others).
        """
        for item in self.members:
            if item.type == type_filter:
                yield item


OverpassElement = Annotated[OverpassNode | OverpassRelation, Field(discriminator="type")]
"""
A single item of an Overpass response's 'elements' list: Can be either a node or a relation.
"""


class OverpassResponse(ReadOnlyPydanticModel):
    remark: str | None = None


class OverpassElementsResponse(OverpassResponse):
    elements: list[OverpassElement]


class OverpassNodesResponse(OverpassResponse):
    elements: list[OverpassNode]


class OverpassRelationsResponse(OverpassResponse):
    elements: list[OverpassRelation]
