"""
Provides an access point to the external OpenStreetMap APIs.

Interactive Overpass query editor: https://overpass-turbo.eu/
"""

from collections.abc import Collection
from logging import getLogger
from typing import Final

from pydantic import ValidationError
from pydantic.type_adapter import TypeAdapter

from trad.application.boundaries.http import HttpNetworkingBoundary, HttpRequestError
from trad.application.filters.source.osm.api.nominatim import NOMINATIM_API_ENDPOINT, NominatimArea
from trad.application.filters.source.osm.api.overpass import (
    OVERPASS_API_ENDPOINT,
    OsmObjectTypes,
    OverpassElement,
    OverpassElementsResponse,
    OverpassNode,
    OverpassNodesResponse,
    OverpassRelation,
    OverpassRelationsResponse,
)
from trad.kernel.errors import DataProcessingError, DataRetrievalError

_logger = getLogger(__name__)


class OsmApiReceiver:
    """
    Represents an endpoint for querying the OpenStreetMap API. Responsible for choosing the correct
    API for the requested usecase, for providing/creating all necessary options, query strings etc.
    and for parsing/validating the reponses. All methods of this class return Pydantic model objects
    (derived from _ReadOnlyPydanticModel), never plain JSON strings.
    """

    _OVERPASS_TIMEOUT: Final = 25
    """ Overpass query timeout in seconds. """

    def __init__(self, http_boundary: HttpNetworkingBoundary):
        """Create a new OsmApiReceiver instance which uses the given HTTP boundary instance."""
        self._http_boundary = http_boundary

    def retrieve_area_by_name(self, area_name: str) -> NominatimArea:
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
                url=NOMINATIM_API_ENDPOINT,
                url_params={"q": area_name, "limit": 1, "format": "jsonv2"},
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Nominatim request failed") from e

        type_adapter = TypeAdapter(list[NominatimArea])
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
        self, area_id: int, element_filter: dict[OsmObjectTypes, dict[str, str]]
    ) -> list[OverpassElement]:
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
                url=OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={full_query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Overpass request failed") from e

        try:
            osm_response = OverpassElementsResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected data from Overpass") from e

        if osm_response.remark:
            _logger.warning("Remark from Overpass: %s", osm_response.remark)

        return osm_response.elements

    def retrieve_nodes_by_ids(
        self,
        osm_ids: Collection[int],
        node_filter: dict[str, str],
    ) -> list[OverpassNode]:
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
        nodes_request = ",".join(f"{nid}" for nid in osm_ids)
        query = self.__build_overpass_query(
            f"""
            (
                node(id: {nodes_request}){tag_filter};
            );
            """
        )

        try:
            json_data = self._http_boundary.retrieve_json_resource(
                url=OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Overpass request failed") from e

        try:
            osm_response = OverpassNodesResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected node data from Overpass") from e

        if osm_response.remark:
            _logger.warning("Remark from Overpass: %s", osm_response.remark)

        return osm_response.elements

    def retrieve_parent_relations(
        self,
        node_ids: Collection[int],
        relation_ids: Collection[int],
        rel_filter: dict[str, str],
    ) -> list[OverpassRelation]:
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
                url=OVERPASS_API_ENDPOINT,
                url_params={},
                query_content=f"data={query}",
            )
        except HttpRequestError as e:
            raise DataRetrievalError("Parent relation Overpass request failed") from e

        try:
            osm_response = OverpassRelationsResponse.model_validate_json(json_data, strict=True)
        except ValidationError as e:
            raise DataProcessingError("Retrieved unexpected node data from Overpass") from e

        if osm_response.remark:
            _logger.warning("Remark from Overpass: %s", osm_response.remark)

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
