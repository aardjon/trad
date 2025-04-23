"""
Implementation of a generic HTTP networking component.
"""

from typing import Final, override

import requests

from trad.adapters.boundaries.http import HttpNetworkingBoundary, JsonData


class RequestsHttp(HttpNetworkingBoundary):
    """
    Implementation of HTTP requests using the `requests` library.

    Library documentation: https://docs.python-requests.org/en/latest/index.html
    """

    _REQUEST_TIMEOUT: Final = 60
    """ The HTTP request timeout in seconds. """

    @override
    def retrieve_text_resource(self, url: str) -> str:
        page = requests.get(
            url=url,
            headers={"User-Agent": "Thunder Client (https://www.thunderclient.com)"},
            timeout=self._REQUEST_TIMEOUT,
        )
        return page.text

    @override
    def retrieve_json_resource(
        self,
        url: str,
        query_params: dict[str, str | int],
        query_content: str | None = None,
    ) -> JsonData:
        response = requests.get(
            url=url,
            params=query_params,
            headers={"User-Agent": "trad routedb scraper", "Accept": "application/json"},
            data=query_content,
            timeout=self._REQUEST_TIMEOUT,
        )
        return JsonData(response.text)
