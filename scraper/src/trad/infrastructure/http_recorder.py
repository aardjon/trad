"""
HTTP boundary which allows to record network traffic and replay it later. This is mainly meant for
testing and debugging without depending on external resources, if using old data is acceptable.
Also, it reduces network traffic and speeds up data retrieval.

To record network traffic, use `TrafficRecorder`. To replay, use `TrafficPlayer`.
"""

from hashlib import sha1
from pathlib import Path
from typing import Final, override
from uuid import uuid4

from pydantic import BaseModel, TypeAdapter

from trad.adapters.boundaries.http import HttpNetworkingBoundary, JsonData


class TrafficRecorder(HttpNetworkingBoundary):
    """
    Networking implementation that decorates a another HTTP boundary to record all requests and
    their reponses to disk. An instance of this component class decorates (as in *Decorator* design
    pattern) a real network boundary, whose traffic shall be recorded.
    """

    def __init__(self, output_path: Path, delegate_boundary: HttpNetworkingBoundary):
        """
        Create a new instance which delegates all requests to the given `delegate_boundary` and
        writes all recorded data into the `output_path` directory. If the directory is not empty,
        existing data is not explicitly deleted but may be overwritten (especially the index file).
        If the directory doesn't exist, it is created.
        """
        self._delegate = delegate_boundary
        """ Delegate to forward networks requests to. """
        self._output_path = output_path
        """ The directory to write recorded data into. """
        self._record_index: list[_RecordIndexEntry] = []
        """ List of recorded requests, to be written into the index file after each request. """
        self._output_path.mkdir(parents=True, exist_ok=True)

    @override
    def retrieve_text_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
    ) -> str:
        content = self._delegate.retrieve_text_resource(url, url_params)
        self._record_request(url, url_params, request_payload=None, response_payload=content)
        return content

    @override
    def retrieve_json_resource(
        self,
        url: str,
        url_params: dict[str, str | int] | None = None,
        query_content: str | None = None,
    ) -> JsonData:
        content = self._delegate.retrieve_json_resource(url, url_params, query_content)
        self._record_request(
            url, url_params, request_payload=query_content, response_payload=content
        )
        return content

    def _record_request(
        self,
        url: str,
        url_params: dict[str, str | int] | None,
        request_payload: str | None,
        response_payload: str,
    ) -> None:
        """Record the given request data."""
        payload_file = self._store_response_payload(response_payload)

        entry = _RecordIndexEntry(
            url=url,
            params_hash=_RecordIndexEntry.calculate_params_hash(url_params),
            payload_hash=_RecordIndexEntry.calculate_payload_hash(request_payload),
            file_name=payload_file,
        )
        self._record_index.append(entry)

        self._store_record_index()

    def _store_response_payload(self, payload: str) -> str:
        """Write the given response `payload` into a new file, and return its file name."""
        file_name = uuid4().hex
        self._output_path.joinpath(file_name).write_text(data=payload)
        return file_name

    def _store_record_index(self) -> None:
        """Write the whole record index into the index file (replacing it)."""
        json_data = _RecordIndex.dump_json(self._record_index)
        self._output_path.joinpath(_record_index_file_name).write_text(json_data.decode("utf-8"))


_record_index_file_name: Final = "index.json"
""" Name of the file containing the record index (i.e. the "table of contents"). """


class _RecordIndexEntry(BaseModel):
    """
    A single entry of the record index (as stored in the index json file). Identifies a single HTTP
    request and points to the data file whith the retrieved response payload.
    """

    url: str
    """ The requested URL. """
    params_hash: str
    """ SHA-1 hash of the requested URL parameters. """
    payload_hash: str
    """ SHA-1 hash of the request playload. """
    file_name: str
    """ File name containing the reponse payload. The file is loacted next to the index file."""

    @staticmethod
    def calculate_params_hash(url_params: dict[str, str | int] | None) -> str:
        """Calculate the hash value for the given URL parameters."""
        return sha1(str(url_params).encode("utf8"), usedforsecurity=False).hexdigest()

    @staticmethod
    def calculate_payload_hash(payload: str | None) -> str:
        """Calculate the hash value for the given payload."""
        return sha1(str(payload).encode("utf8"), usedforsecurity=False).hexdigest()


_RecordIndex = TypeAdapter(list[_RecordIndexEntry])
""" Pydantic model type representing the whole record index. """
