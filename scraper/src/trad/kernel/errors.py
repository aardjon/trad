"""
Provides exception classes that may be raised during the scraping process.
"""

from typing import override


class FilterError(Exception):
    """
    Raised by Filters when they cannot continue because of an unrecoverable error. This usually
    leads to an abortion of the whole scraper.
    """


class DataRetrievalError(FilterError):
    """
    Raised after an error while trying to retrieve route data. May be caused by network or
    permission problems, for example.
    """


class DataProcessingError(FilterError):
    """
    Raised when the retrieved data cannot be processed, for example because it is of an unexpected
    structure or format.
    """


class MergeConflictError(DataProcessingError):
    """
    Raised when a value cannot be processed because it already contains a different (conflicting)
    value (and the conflict cannot be resolved automatically).
    """

    def __init__(self, object_type: str, object_name: str, conflicting_attribute: str):
        """
        Creates a new Exception notifying about a conflict on the `conflicting_attribute` property
        of an `object_type` object with the name `object_name`. `object_type` is e.g. "route" or
        "summit", `conflicting_attribute` is the name of the conflicting data field.
        """
        super().__init__()
        self._object_type = object_type
        self._object_name = object_name
        self._conflicting_attribute = conflicting_attribute

    @override
    def __str__(self) -> str:
        return (
            f"Cannot merge {self._object_type} data for '{self._object_name}' because of "
            f"conflicting {self._conflicting_attribute} values."
        )


class IncompleteDataError(DataProcessingError):
    """
    Raised when an entity object is missing some mandatory data which must be set.

    This problem cannot be fixed automatically.
    """

    def __init__(self, incomplete_object: object, missing_property_name: str):
        """
        Creates a new Exception notifying about missing data on the `incomplete_object` entity.
        `missing_property_name` gives the name of the missing/empty attribute.
        """
        super().__init__()
        self._incomplete_entity = incomplete_object
        self._missing_property_name = missing_property_name

    @override
    def __str__(self) -> str:
        return (
            f"Missing '{self._missing_property_name}' data in 'str({self._incomplete_entity})' "
            "object."
        )


class ValueParseError(DataProcessingError):
    """
    Raised when a string cannot be parsed because of an invalid/unexpected format.
    """

    def __init__(self, value_type: str, invalid_value: str):
        """
        Creates a new Exception notifying about a parse error while trying to parse the
        `invalid_value` string into an object of type `value_type`.
        """
        super().__init__()
        self._value_type = value_type
        self._invalid_value = invalid_value

    @override
    def __str__(self) -> str:
        return f"Value '{self._invalid_value}' is not a valid {self._value_type})."


class PipeDataError(Exception):
    """
    Raised by Pipes when they cannot fulfil a certain request.
    """


class EntityNotFoundError(PipeDataError):
    """
    Raised when an entity the operation depends on is missing in the pipe (e.g. trying to add a
    route to a non-existing summit). In many cases these are programming errors that can be fixed by
    adding the missing entity first. In general, the end user cannot do much about it when it
    happens unexpectedly at runtime.
    """

    def __init__(self, object_name: str):
        """
        Creates a new Exception notifying about a missing object named `object_name`.
        """
        super().__init__()
        self._object_name = object_name

    @override
    def __str__(self) -> str:
        return f"Referenced object '{self._object_name}' not found. Did you forget to add it?"


class InvalidStateError(Exception):
    """
    Raised when an operation cannot be fulfilled due to an invalid application (or component) state.
    The reason is usually a programming or configuration error, the end user cannot do much about it
    when it happens unexpectedly at runtime.
    """
