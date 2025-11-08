"""
Implementation of a generic HTTP networking component.
"""
# Disable the "no-member" pylint message in this file because it causes too many false positives for
# the dynamic attributes and imports of the 'requests' library. The basic/static cases are still
# checked by Mypy, so it's not turned off completely.
# pylint: disable=no-member

from typing import Final, override

import requests

from trad.application.boundaries.http import (
    HttpNetworkingBoundary,
    HttpRequestError,
    JsonData,
)


class RequestsHttp(HttpNetworkingBoundary):
    """
    Implementation of HTTP requests using the `requests` library. Besides being a wrapper for
    `requests`, this component ensures that certain connection settings like timeouts or user agent
    strings are the same for all HTTP connections.

    Library documentation: https://docs.python-requests.org/en/latest/index.html
    """

    _USER_AGENT_HEADER: Final = {"User-Agent": "TradRouteDbScraper/NONE"}
    """
    The user agent string header to send with HTTP requests.
    TODO(aardjon): We need a real version number to use here...
    """

    _REQUEST_TIMEOUT: Final = 60
    """ The HTTP request timeout in seconds. """

    @override
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        response = self._retrieve_resource(
            url=url,
            url_params=url_params,
            additional_headers={},
            query_content=None,
        )
        return response.text

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        response = self._retrieve_resource(
            url=url,
            url_params=url_params,
            additional_headers={"Accept": "application/json"},
            query_content=query_content,
        )
        return JsonData(response.text)

    def _retrieve_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None,
        additional_headers: dict[str, str],
        query_content: str | None,
    ) -> requests.models.Response:
        """
        Does the actual HTTP request, checks the response and returns the Response object (so that
        callers may do additional checks, if necessary). Raises HttpRequestError in case of any
        errors.
        """
        try:
            response = requests.get(
                url=url,
                params=url_params,
                headers=self._USER_AGENT_HEADER | additional_headers,
                data=query_content,
                timeout=self._REQUEST_TIMEOUT,
            )
        except requests.RequestException as e:
            raise HttpRequestError("HTTP request failed") from e
        if not response.ok:
            raise HttpRequestError(f"HTTP error {response.status_code}: {response.reason}")
        if response.status_code != requests.codes.ok:
            raise HttpRequestError(
                f"Unexpected HTTP response {response.status_code}: {response.reason}"
            )
        return response
