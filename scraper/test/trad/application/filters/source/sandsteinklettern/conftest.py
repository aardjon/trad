"""
Provides common fixtures that are used by the unit test modules for
trad.application.filters.source.sandsteinklettern.

Some fixtures in this module provide test data which is statically defined in the JSON files in the
same directory:
 - minimal_data_sample.json: A minimal data set containing a single route on a single summit.
 - full_data_sample.json: A more complex data set containing several sectors, summits, routes and
   posts.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Final, Literal, cast, override
from unittest.mock import Mock

import pytest

from trad.application.boundaries.http import HttpNetworkingBoundary, JsonData
from trad.application.filters.source.sandsteinklettern.filter import SandsteinkletternDataFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.pipes import Pipe

_EXPECTED_BASE_URL: Final = "http://db-sandsteinklettern.gipfelbuch.de/"
""" The API URL expected to be requested. """

_AREAS_ENDPOINT: Final = "jsongebiet.php"
_SECTORS_ENDPOINT = "jsonteilgebiet.php"
_SUMMITS_ENDPOINT = "jsongipfel.php"
_ROUTES_ENDPOINT = "jsonwege.php"
_POSTS_ENDPOINT = "jsonkomment.php"

_RawJsonData = list[dict[str, str]]
""" A single JSON data set that can be returned by the (fake) remote API). """

JsonTestData = dict[Literal["areas", "sectors", "summits", "routes", "posts"], _RawJsonData]
""" JSON data loaded from one of the prepared data files. """

PreparedFilterRunner = Callable[[JsonTestData], CollectedData]
"""
A callable that takes a single `sample_json` parameter (of type JsonTestData), executes a certain
filter with it and returns the resulting output Pipe.
"""


@pytest.fixture
def run_prepared_filter() -> PreparedFilterRunner:
    """
    Provides a callable that takes a single `sample_json` parameter (of type JsonTestData), executes
    the Sandsteinklettern source filter with a _FakeNetwork instance providing this JSON data
    sample, and returns the resulting output Pipe.
    """

    def inner(sample_json: JsonTestData) -> CollectedData:
        fake_network = _create_fake_network(sample_json)
        data_filter = SandsteinkletternDataFilter(fake_network)
        output_pipe = CollectedData()
        data_filter.execute_filter(input_pipe=Mock(Pipe), output_pipe=output_pipe)
        return output_pipe

    return inner


@pytest.fixture
def minimal_data_sample() -> JsonTestData:
    """
    Fixture providing a minimal working test data sample (from "minimal_data_sample.json").
    """
    return _load_prepared_test_data("minimal_data_sample.json")


@pytest.fixture
def full_data_sample() -> JsonTestData:
    """
    Fixture providing a full working test data sample (from "full_data_sample.json").
    """
    return _load_prepared_test_data("full_data_sample.json")


def _load_prepared_test_data(data_file: str) -> JsonTestData:
    """
    Load and return the prepared test JSON data from the given `data_file`.
    """
    dir_name = Path(__file__).parent
    return cast(JsonTestData, json.loads(dir_name.joinpath(data_file).read_text(encoding="utf-8")))


def _create_fake_network(json_response_data: JsonTestData) -> HttpNetworkingBoundary:
    """
    Returns a new, _FakeNetwork instance preconfigured to provide the given 'json_response_data'
    (which can be loaded from the prepared test data files).
    """
    fake_network = FakeNetwork(_EXPECTED_BASE_URL)
    fake_network.add_json_response(
        _AREAS_ENDPOINT,
        required_url_param="land",
        response=json_response_data["areas"],
    )
    fake_network.add_json_response(
        _SECTORS_ENDPOINT,
        required_url_param="gebietid",
        response=json_response_data["sectors"],
    )

    fake_network.add_json_response(
        _SUMMITS_ENDPOINT,
        required_url_param="sektorid",
        response=json_response_data["summits"],
    )
    fake_network.add_json_response(
        _ROUTES_ENDPOINT,
        required_url_param="sektorid",
        response=json_response_data["routes"],
    )
    fake_network.add_json_response(
        _POSTS_ENDPOINT,
        required_url_param="sektorid",
        response=json_response_data["posts"],
    )
    return fake_network


class FakeNetwork(HttpNetworkingBoundary):
    """
    Fake networking component that doesn't do any real network requests but responds with
    pre-configured data.

    It also ensures some general request attributes, e.g. that no request contains any content, or
    that all requests contain the API key.
    """

    def __init__(self, expected_base_url: str) -> None:
        self._expected_base_url: Final = expected_base_url
        """ The API URL expected to be requested. All other URLs will cause an error. """
        self._predefined_responses: dict[str, dict[str, _RawJsonData]] = {}

    def _ensure_url_parameters(self, url_params: dict[str, str | int]) -> None:
        """
        Ensure that the necessary API key is sent with the given request, along with other parameter
        conditions.
        """
        expected_parameter_count = 2

        assert url_params.get("app", "") == "trad"
        assert len(url_params) == expected_parameter_count

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        assert url.startswith(self._expected_base_url)
        # Make sure that URL params are always provided and contain the API key
        assert url_params
        self._ensure_url_parameters(url_params)
        # Make sure no content is sent with requests
        assert not query_content

        predefined_responses = self._predefined_responses.get(url.split("/")[-1], None)
        assert predefined_responses is not None, f"Requesting an unexpected API end point '{url}'"

        del url_params["app"]
        url_param_key, url_param_value = next(iter(url_params.items()))
        responses = predefined_responses[url_param_key]
        return JsonData(
            json.dumps(
                [response for response in responses if response[url_param_key] == url_param_value]
            )
        )

    def add_json_response(
        self,
        api_endpoint: str,
        required_url_param: str,
        response: list[dict[str, str]],
    ) -> None:
        """
        Register the given `response` to be sent when `api_endpoint` is requested with the
        `required_url_param` URL parameter. Any previous registration for this request is replaced.
        """
        self._predefined_responses.setdefault(api_endpoint, {})[required_url_param] = response

    @override
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        # This method must not be called by the filter
        pytest.fail("Filter is not supposed to retrieve any text resources")
