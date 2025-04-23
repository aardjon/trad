"""
Boundary interface from the `adapters` rings to the HTTP component in the `infrastructure` ring.
Allows to easily mock all network access in unit tests.
"""

from abc import ABCMeta, abstractmethod
from typing import NewType

JsonData = NewType("JsonData", str)
"""
Represents a string of arbitrary JSON data.
"""


class HttpNetworkingBoundary(metaclass=ABCMeta):
    """
    Interface of a generic networking interface that allows to access remote resources by their URL
    via HTTP(S).
    """

    @abstractmethod
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        """
        Retrieve and return the text content of the resource at the requested [url].
        [url_params] are additional parameters to be sent as part of the URL, and will be appended
        (and encoded) appropriately.

        If the resource is available in different formats, the one best matching "text" is chosen.
        Raises in case of problems, such as:
         - Connection problem
         - Connection timeout
         - Resource not available
         - Not a text resource
        """

    @abstractmethod
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        """
        Retrieve and return the (binary) JSON content of the resource at the requested [url].
        [url_params] are additional parameters to be sent as part of the URL, and will be appended
        (and encoded) appropriately, while [query_content] is sent as the request body as-is.

        Raises in case of problems, such as:
         - Connection problem
         - Connection timeout
         - Resource not available
        """
