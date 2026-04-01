"""
Provides types representing or managing object names.
"""

import string
from typing import override


class NormalizedName:
    """
    A normalized name of a single physical object (i.e. a summit or a route on a summit). It is not
    meant to be displayed to users. Objects of this class can be compared (but not ordered) and
    hashed (e.g. to use them as dict keys).

    The normalized name is based on the input strings and is used to map slightly different object
    name variants (e.g. different punctuation or permutations) to each other. It does not match
    completely different names, though. Also, since there may be objects with the same name, it is
    not guaranteed to be unique.
    """

    def __init__(self, object_name: str):
        """
        Create a new normalized representation from the given `object_name`.
        """
        self._normalized_string = self.__normalize(object_name)
        """ The normalized name string. """

    @staticmethod
    def __normalize(object_name: str) -> str:
        """Does the actual name normalization."""
        normalized_name = object_name.lower()
        # Remove non-ASCII characters
        normalized_name = "".join(c for c in normalized_name if c in string.printable)
        # Replace punctuation characters with spaces
        normalized_name = "".join(
            c if c not in string.punctuation else " " for c in normalized_name
        )
        # Order the single segments alphabetically, and rejoin them with single underscores
        return "_".join(sorted(normalized_name.split()))

    @override
    def __str__(self) -> str:
        return self._normalized_string

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NormalizedName):
            return NotImplemented
        return self._normalized_string == other._normalized_string

    @override
    def __hash__(self) -> int:
        return hash(self._normalized_string)
