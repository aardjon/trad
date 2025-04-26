"""
Unit tests for the trad.infrastructure.requests module.
"""

from collections.abc import Callable
from typing import Final
from unittest.mock import ANY, Mock, patch

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout
from requests.models import Response

from trad.adapters.boundaries.http import HttpRequestError
from trad.infrastructure.requests import RequestsHttp


@patch("trad.infrastructure.requests.requests.get")
class TestRequestsHttp:
    """
    Unit tests for the RequestsHttp component class.

    Note that these test cases shall *not* cause real network requests.
    """

    _TEST_BASE_URL: Final = "https://www.fomori.de/trad/testing"
    _EXPECTED_REQUEST_TIMEOUT: Final = 60
    _EXPECTED_USER_AGENT: Final = "TradRouteDbScraper/NONE"

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
        mocked_requests_get: Mock,
        url_params: dict[str, str | int] | None,
        response_data: str,
    ) -> None:
        """
        Ensures the correct behaviour of the retrieve_text_resource() method for normal use cases:
         - The correct User-Agent header must be sent
         - The correct request timeout must be set
         - The URL and their parameters must be forwarded correctly
         - The response content is returned as-is
        """
        mocked_requests_get.return_value = Mock(Response, status_code=200, text=response_data)
        http_component = RequestsHttp()
        response = http_component.retrieve_text_resource(
            url=self._TEST_BASE_URL,
            url_params=url_params,
        )

        # Ensure that the response data is returned as expected
        assert response == response_data

        # Ensure that all parameters are forwarded and the timeout is set correctly
        mocked_requests_get.assert_called_once_with(
            url=self._TEST_BASE_URL,
            params=url_params,
            data=None,
            headers=ANY,
            timeout=self._EXPECTED_REQUEST_TIMEOUT,
        )

        # Ensure that the expected headers are sent
        headers = mocked_requests_get.call_args_list[0].kwargs["headers"]
        assert headers.get("User-Agent") == self._EXPECTED_USER_AGENT

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
        mocked_requests_get: Mock,
        url_params: dict[str, str | int] | None,
        query_content: str | None,
        response_data: str,
    ) -> None:
        """
        Ensures the correct behaviour of the retrieve_json_resource() method for normal use cases:
         - The correct User-Agent header must be sent
         - The correct request timeout must be set
         - The URL, their parameters and the query content must be forwarded correctly
         - The response content is returned as-is (no matter if it is valid JSON or not)
        """
        mocked_requests_get.return_value = Mock(Response, status_code=200, text=response_data)
        http_component = RequestsHttp()
        response = http_component.retrieve_json_resource(
            url=self._TEST_BASE_URL,
            url_params=url_params,
            query_content=query_content,
        )

        # Ensure that the response data is returned as expected
        assert response == response_data

        # Ensure that all parameters are forwarded and the timeout is set correctly
        mocked_requests_get.assert_called_once_with(
            url=self._TEST_BASE_URL,
            params=url_params,
            data=query_content,
            headers=ANY,
            timeout=self._EXPECTED_REQUEST_TIMEOUT,
        )

        # Ensure that the expected headers are sent
        headers = mocked_requests_get.call_args_list[0].kwargs["headers"]
        assert headers.get("User-Agent") == self._EXPECTED_USER_AGENT
        assert headers.get("Accept") == "application/json"

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
        mocked_requests_get: Mock,
        response_code_or_exception: int | Exception,
        send_request: Callable[[RequestsHttp, str], str],
    ) -> None:
        """
        Ensures that the retrieve_*_resource() methods raise an HttpRequestError in case of request
        or HTTP errors.
        """
        mocked_requests_get.side_effect = (
            [Mock(Response, status_code=response_code_or_exception, reason="Fake Failure")]
            if isinstance(response_code_or_exception, int)
            else response_code_or_exception
        )
        http_component = RequestsHttp()
        with pytest.raises(HttpRequestError):
            send_request(http_component, self._TEST_BASE_URL)
