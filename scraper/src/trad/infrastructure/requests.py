"""
Implementation of a generic HTTP networking component.
"""

from typing import Final, override

from requests import get as requests_get

from trad.adapters.boundaries.http import HttpNetworkingBoundary, JsonData


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
        page = requests_get(
            url=url,
            params=url_params,
            headers=self._USER_AGENT_HEADER,
            timeout=self._REQUEST_TIMEOUT,
        )
        return page.text

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        response = requests_get(
            url=url,
            params=url_params,
            headers=self._USER_AGENT_HEADER | {"Accept": "application/json"},
            data=query_content,
            timeout=self._REQUEST_TIMEOUT,
        )
        return JsonData(response.text)
