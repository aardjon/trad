"""
Implementation of a generic HTTP networking component.
"""
# Disable the "no-member" pylint message in this file because it causes too many false positives for
# the dynamic attributes and imports of the 'requests' library. The basic/static cases are still
# checked by Mypy, so it's not turned off completely.
# pylint: disable=no-member

from collections.abc import Callable
from typing import Final, override
from urllib.parse import urlsplit

import requests

from trad.application.boundaries.http import (
    HttpNetworkingBoundary,
    HttpRequestError,
    JsonData,
)
from trad.kernel.appmeta import APPLICATION_NAME, APPLICATION_VERSION


class RequestsHttp(HttpNetworkingBoundary):
    """
    Implementation of HTTP requests using the `requests` library. Besides being a wrapper for
    `requests`, this component ensures that certain connection settings like timeouts or user agent
    strings are the same for all HTTP connections.

    Furthermore, HTTP connections are reused (kept open) for each host, because we expect several
    subsequent requests to the same host in most cases.

    Library documentation: https://docs.python-requests.org/en/latest/index.html
    """

    _USER_AGENT_HEADER: Final = {"User-Agent": f"{APPLICATION_NAME}/{APPLICATION_VERSION}"}
    """
    The user agent string header to send with HTTP requests.
    """

    _REQUEST_TIMEOUT: Final = 60
    """
    The HTTP request timeout in seconds.
    This value is used as both *connection*  and *read*  timeout for HTTP requests (see
    https://docs.python-requests.org/en/latest/user/advanced/#timeouts more information).
    """

    def __init__(self, session_factory: Callable[[], requests.Session] | None = None) -> None:
        """
        Initializes a new RequestsHttp component instance.

        The new instance uses `session_factory` to create new HTTP sessions, or the default
        constructor as default. This parameter is mainly there for injection special (e.g. mocked)
        Sessions from unit tests, and should not be set in normal production code.
        """
        self._session_factory = session_factory or requests.Session
        """ Factory function for creating a new Session instance."""
        self._sessions: dict[str, requests.Session] = {}
        """ Session cache: Key is the host, value is the Sesison instance to use. """

    @override
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        response = self._retrieve_resource(
            url=url,
            url_params=url_params,
            query_content=None,
            configure_new_session=lambda _: None,
        )
        return response.text

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        def configure_session(session: requests.Session) -> None:
            session.headers.update({"Accept": "application/json"})

        response = self._retrieve_resource(
            url=url,
            url_params=url_params,
            query_content=query_content,
            configure_new_session=configure_session,
        )
        return JsonData(response.text)

    def _retrieve_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None,
        query_content: str | None,
        configure_new_session: _ConfigureSessionFunc,
    ) -> requests.models.Response:
        """
        Does the actual HTTP request, checks the response and returns the Response object (so that
        callers may do additional checks, if necessary). Raises HttpRequestError in case of any
        errors.
        """
        session = self._get_session_for_url(url, configure_new_session)

        try:
            response = session.get(
                url=url,
                params=url_params,
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

    def _get_session_for_url(
        self,
        url: str,
        configure_new_session: _ConfigureSessionFunc,
    ) -> requests.Session:
        """
        Returns the requests session to use for requesting the given URL.

        Sessions are cached in `self._sessions` and reused for all requests to the same host. A new
        session is created when requesting a host for the first time.
        """
        host = urlsplit(url).hostname
        if not host:
            raise ValueError(f"Unable to parse hostname from URL {url}")

        session = self._sessions.get(host)
        if session is None:
            session = self._session_factory()
            session.headers.update(self._USER_AGENT_HEADER)
            configure_new_session(session)
            self._sessions[host] = session
        return session


_ConfigureSessionFunc = Callable[[requests.Session], None]
"""
Signature of a function that configures a (newly created) requests.Session object as necessary
"""
