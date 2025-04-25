"""
Implementation of a generic HTTP networking component.
"""

from typing import Final, override

from requests import codes
from requests import get as requests_get
from requests.exceptions import RequestException

from trad.adapters.boundaries.http import HttpNetworkingBoundary, HttpRequestError, JsonData


class RequestsHttp(HttpNetworkingBoundary):
    """
    Implementation of HTTP requests using the `requests` library.

    Library documentation: https://docs.python-requests.org/en/latest/index.html
    """

    _USER_AGENT_HEADER: Final = {"User-Agent": "TradRouteDbScraper/NONE"}
    """
    The user agent string to send with HTTP requests.
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
        try:
            response = requests_get(
                url=url,
                params=url_params,
                headers=self._USER_AGENT_HEADER,
                timeout=self._REQUEST_TIMEOUT,
            )
        except RequestException as e:
            raise HttpRequestError("HTTP request failed") from e
        if not response.ok:
            raise HttpRequestError(f"HTTP error {response.status_code}: {response.reason}")
        if response.status_code != codes.ok:
            raise HttpRequestError(
                f"Unexpected HTTP repsonse {response.status_code}: {response.reason}"
            )
        return response.text

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        try:
            response = requests_get(
                url=url,
                params=url_params,
                headers=self._USER_AGENT_HEADER | {"Accept": "application/json"},
                data=query_content,
                timeout=self._REQUEST_TIMEOUT,
            )
        except RequestException as e:
            raise HttpRequestError("HTTP request failed") from e
        if not response.ok:
            raise HttpRequestError(f"HTTP error {response.status_code}: {response.reason}")
        if response.status_code != codes.ok:
            raise HttpRequestError(
                f"Unexpected HTTP repsonse {response.status_code}: {response.reason}"
            )
        return JsonData(response.text)
