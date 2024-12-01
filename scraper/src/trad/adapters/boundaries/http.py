"""
Boundary interface from the `adapters` rings to the HTTP component in the `infrastructure` ring.
Allows to easily mock all network access in unit tests.
"""

from abc import ABCMeta, abstractmethod


class HttpNetworkingBoundary(metaclass=ABCMeta):
    """
    Interface of a generic networking interface that allows to access remote resources by their URL
    via HTTP(S).
    """

    @abstractmethod
    def retrieve_text_resource(self, url: str) -> str:
        """
        Retrieve and return the text content of the resource at the requested [url].

        If the resource is available in different formats, the one best matching "text" is chosen.
        Raises in case of problems, such as:
         - Connection problem
         - Resource not available
         - Not a text resource
        """
