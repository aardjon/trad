"""
Implementation of a generic HTTP networking component.
"""

from typing import override

import requests

from trad.adapters.boundaries.http import HttpNetworkingBoundary


class RequestsHttp(HttpNetworkingBoundary):
    """
    Implementation of HTTP requests using the `requests` library.

    Library documentation: https://docs.python-requests.org/en/latest/index.html
    """

    @override
    def retrieve_text_resource(self, url: str) -> str:
        page = requests.get(
            url=url,
            headers={"User-Agent": "Thunder Client (https://www.thunderclient.com)"},
            timeout=None,
        )
        return page.text
