"""
Unit tests for the trad.infrastructure.requests module.
"""

from collections.abc import Callable, Iterator
from typing import Final
from unittest.mock import ANY, Mock
from urllib.parse import urlsplit

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout
from requests.models import Response
from requests.sessions import Session

from trad.application.boundaries.http import HttpRequestError
from trad.infrastructure.requests import RequestsHttp
from trad.kernel.appmeta import APPLICATION_NAME, APPLICATION_VERSION


class TestRequestsHttp:
    """
    Unit tests for the RequestsHttp component class.

    Note that these test cases shall *not* cause real network requests.
    """

    _TEST_BASE_URL: Final = "https://www.fomori.de/trad/testing"
    _EXPECTED_REQUEST_TIMEOUT: Final = 60
    _EXPECTED_USER_AGENT: Final = f"{APPLICATION_NAME}/{APPLICATION_VERSION}"

    @pytest.mark.parametrize(
        "url_params",
        [
            (  # Single parameter
                {"param": "data"},
            ),
            (  # Multiple parameters
                {"param1": "data1", "param2": 13},
            ),
            (  # Empty parameters
                {},
            ),
            (  # No parameters
                None,
            ),
        ],
    )
    @pytest.mark.parametrize(
        "response_data",
        [
            "Response Text",
            "",
        ],
    )
    def test_retrieve_text_resource_good(
        self,
        url_params: dict[str, str | int] | None,
        response_data: str,
        requests_session: Mock,
    ) -> None:
        """
        Ensures the correct behaviour of the retrieve_text_resource() method for normal use cases:
         - The correct User-Agent header must be sent
         - The correct request timeout must be set
         - The URL and their parameters must be forwarded correctly
         - The response content is returned as-is
        """
        requests_session.get.return_value = Mock(Response, status_code=200, text=response_data)
        http_component = RequestsHttp(lambda: requests_session)
        response = http_component.retrieve_text_resource(
            url=self._TEST_BASE_URL,
            url_params=url_params,
        )

        # Ensure that the response data is returned as expected
        assert response == response_data

        # Ensure that all parameters are forwarded and the timeout is set correctly
        requests_session.get.assert_called_once_with(
            url=self._TEST_BASE_URL,
            params=url_params,
            data=None,
            timeout=self._EXPECTED_REQUEST_TIMEOUT,
        )

        # Ensure that the expected headers are sent
        assert requests_session.headers.get("User-Agent") == self._EXPECTED_USER_AGENT

    @pytest.mark.parametrize(
        ("url_params", "query_content"),
        [
            (  # Single parameter
                {"param": "data"},
                "example content",
            ),
            (  # Multiple parameters
                {"param1": "data1", "param2": "data2"},
                "data=request",
            ),
            (  # Empty parameters
                {},
                "data=request",
            ),
            (  # No parameters
                None,
                "data=request",
            ),
            (  # Empty content
                {"param": 42},
                "",
            ),
            (  # No content
                {"param": ""},
                None,
            ),
            (  # Simple URL request
                {},
                None,
            ),
        ],
    )
    @pytest.mark.parametrize(
        "response_data",
        [
            '{"json": "yes"}',  # Valid JSON response
            "invalid JSON data",  # Invalid JSON response
            "",  # Empty response
        ],
    )
    def test_retrieve_json_resource_good(
        self,
        url_params: dict[str, str | int] | None,
        query_content: str | None,
        response_data: str,
        requests_session: Mock,
    ) -> None:
        """
        Ensures the correct behaviour of the retrieve_json_resource() method for normal use cases:
         - The correct User-Agent header must be sent
         - The correct request timeout must be set
         - The URL, their parameters and the query content must be forwarded correctly
         - The response content is returned as-is (no matter if it is valid JSON or not)
        """
        requests_session.get.return_value = Mock(Response, status_code=200, text=response_data)
        http_component = RequestsHttp(lambda: requests_session)
        response = http_component.retrieve_json_resource(
            url=self._TEST_BASE_URL,
            url_params=url_params,
            query_content=query_content,
        )

        # Ensure that the response data is returned as expected
        assert response == response_data

        # Ensure that all parameters are forwarded and the timeout is set correctly
        requests_session.get.assert_called_once_with(
            url=self._TEST_BASE_URL,
            params=url_params,
            data=query_content,
            timeout=self._EXPECTED_REQUEST_TIMEOUT,
        )

        # Ensure that the expected headers are sent
        assert requests_session.headers.get("User-Agent") == self._EXPECTED_USER_AGENT
        assert requests_session.headers.get("Accept") == "application/json"

    @pytest.mark.parametrize(
        "send_request",
        [
            lambda component, url: component.retrieve_text_resource(url=url),
            lambda component, url: component.retrieve_json_resource(url=url),
        ],
    )
    @pytest.mark.parametrize(
        "response_code_or_exception",
        [
            # Possible network problems
            RequestsConnectionError(),
            Timeout(),
            HTTPError(),
            # HTTP status codes that trigger an error
            102,
            204,
            208,
            301,
            400,
            401,
            500,
            503,
        ],
    )
    def test_retrieve_resource_errors(
        self,
        response_code_or_exception: int | Exception,
        send_request: Callable[[RequestsHttp, str], str],
        requests_session: Mock,
    ) -> None:
        """
        Ensures that the retrieve_*_resource() methods raise an HttpRequestError in case of request
        or HTTP errors.
        """
        requests_session.get.side_effect = (
            [Mock(Response, status_code=response_code_or_exception, reason="Fake Failure")]
            if isinstance(response_code_or_exception, int)
            else response_code_or_exception
        )
        http_component = RequestsHttp(lambda: requests_session)
        with pytest.raises(HttpRequestError):
            send_request(http_component, self._TEST_BASE_URL)

    @pytest.mark.parametrize(
        ("request_resources", "expected_session_calls"),
        [
            pytest.param(
                [
                    ("https://www.fomori.de/api/docs", {}),
                    ("https://www.fomori.de/api/docs", {}),
                ],
                {"www.fomori.de": 2},
                id="Same URL",
            ),
            pytest.param(
                [
                    ("https://www.fomori.de/api/docs1", {}),
                    ("https://www.fomori.de/api/docs2", {}),
                ],
                {"www.fomori.de": 2},
                id="Same host, different endpoints",
            ),
            pytest.param(
                [
                    ("https://www.fomori.de/api", {"tpye": "html"}),
                    ("https://www.fomori.de/api", {"type": "json"}),
                ],
                {"www.fomori.de": 2},
                id="Same endpoint, different parameters",
            ),
            pytest.param(
                [
                    ("https://www.example.com", {}),
                    ("https://www.fomori.de", {}),
                ],
                {"www.example.com": 1, "www.fomori.de": 1},
                id="Different hosts, single request each",
            ),
            pytest.param(
                [
                    ("https://www.example.com/api", {}),
                    ("https://www.fomori.de", {"cat": 42}),
                    ("https://www.example.com", {}),
                    ("https://www.fomori.de/cat/37", {"type": "text"}),
                    ("https://www.fomori.de", {}),
                ],
                {
                    "www.example.com": 2,
                    "www.fomori.de": 3,
                },
                id="Different hosts, multiple requests each",
            ),
            pytest.param(
                [],
                {},
                id="No request",
            ),
        ],
    )
    def test_reuse_session(
        self,
        request_resources: list[tuple[str, dict[str, str | int] | None]],
        expected_session_calls: dict[str, int],
    ) -> None:
        """
        Ensure that the session is reused for subsequent requests to the same host.

        - Each host gets its own session
        - For the same host, the session is reused
            - Even for different URL parameters
            - Even for different API endpoints
        - Sessions are created on demand only
        """
        created_sessions: list[Mock] = []  # All created created sessions

        def create_session() -> Session:
            nonlocal created_sessions
            session = _create_session_mock()
            session.get.return_value = Mock(Response, status_code=200, text="")
            created_sessions.append(session)
            return session

        http_component = RequestsHttp(create_session)

        # Do the appropriate number of requests
        for url, params in request_resources:
            http_component.retrieve_json_resource(
                url=url,
                url_params=params,
            )

        # Make sure the number of created sessions equals the number of expected hosts
        assert len(created_sessions) == len(expected_session_calls)

        def extract_hostname(url: str) -> str:
            """Return the hostname part of the given url."""
            return urlsplit(url).netloc

        found_hosts: list[str] = []  # Stores the host names for which we already found a session
        for session in created_sessions:
            # Collect all host that were requested by this session
            hosts = list(
                {extract_hostname(call.kwargs["url"]) for call in session.get.call_args_list}
            )

            # Make sure that the get() calls to this session all go to the same host
            assert len(hosts) == 1
            hostname = hosts[0]

            # Make sure this host name has not been requested by another session
            assert hostname not in found_hosts

            # Make sure a request to this nost name is expected at all
            assert hostname in expected_session_calls

            # Make sure the actual number of get() call of this host's session is as expected
            assert session.get.call_count == expected_session_calls[hostname]

            # Remember the host for the next iteration
            found_hosts.append(hostname)

    def test_retry_config(self, requests_session: Mock) -> None:
        """
        Ensures that HTTP requests is configured to retry on certain errors.

        The retry itself is done by the `requests` library, that's why we don't explicitly test it
        here (assuming that the library works). Instead, we just verify the retry configuration of
        the used session.
        """
        # Do a dummy request to create the session
        requests_session.get.return_value = Mock(Response, status_code=200, text="")
        http_component = RequestsHttp(lambda: requests_session)
        http_component.retrieve_json_resource(url=self._TEST_BASE_URL)

        expected_prefixes: Final = ["http://", "https://"]
        expected_retry_count: Final = 5
        expect_retry_on_status_codes: Final = [429, 504]

        # Ensure that a connection adapter with the expected retry configuration was mounted into
        # the session for all protocols
        assert requests_session.mount.call_count == len(expected_prefixes)
        for prefix in expected_prefixes:
            requests_session.mount.assert_any_call(prefix=prefix, adapter=ANY)
            mounted_adapter = next(
                c.kwargs["adapter"]
                for c in requests_session.mount.call_args_list
                if c.kwargs["prefix"] == prefix
            )
            # Retry on status codes 429 and 504
            for status_code in expect_retry_on_status_codes:
                assert status_code in mounted_adapter.max_retries.status_forcelist
            # Allow the expected total count of tries
            assert mounted_adapter.max_retries.total == expected_retry_count
            # Respect "Retry-After" header, if any
            assert mounted_adapter.max_retries.respect_retry_after_header is True


@pytest.fixture
def requests_session() -> Iterator[Mock]:
    """
    Fixture providing a mocked requests.Session created with `_create_session_mock()`. This fixture
    is provided for convenience to make test cases with only one session a bit more readable.
    """
    return _create_session_mock()


def _create_session_mock() -> Mock:
    """
    Create a mocked requests.Session containing a regular (but empty) `headers` dict. Using this
    mock prevents the unit tests from doing real network requests, and allows them to control the
    request behaviour.
    """
    mocked_session = Mock(spec=Session)
    mocked_session.headers = {}
    return mocked_session
