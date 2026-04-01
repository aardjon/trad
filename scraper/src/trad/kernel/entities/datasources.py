"""
Provides types for managing information about data sources.
"""

from dataclasses import dataclass
from typing import override


@dataclass
class ExternalSource:
    """
    Represents an external source from which data is imported. External sources are uniquely
    identified by their label.
    """

    label: str
    """ Display name of this data source. This name must be unique within the route DB. """

    url: str
    """
    Landing page URL (not an API endpoint!) a user may visit by browser to get further
    information about this data source.
    """

    attribution: str
    """ Attribution string (e.g. author names) for the data from this source. """

    license_name: str | None = None
    """
    Short, human readable name of the data license, if any. None if there is no explicit license
    (but e.g. some individual agreement).
    """

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExternalSource):
            return NotImplemented
        return self.label == other.label

    @override
    def __hash__(self) -> int:
        return hash(self.label)
