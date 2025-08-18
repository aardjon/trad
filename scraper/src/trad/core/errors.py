"""
Provides exception classes that may be raised during the scraping process.
"""


class FilterError(Exception):
    """
    Raised by Filters when they cannot continue because of an unrecoverable error. This usually leads
    to an abortion of the whole scraper.
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


class PipeDataError(Exception):
    """
    Raised by Pipes when they cannot process (e.g. store) a certain value.
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

    def __str__(self) -> str:
        return f"Referenced object '{self._object_name}' not found. Did you forget to add it?"


class MergeConflictError(PipeDataError):
    """
    Raised when a value cannot be added to a Pipe because it already contains a different
    (conflicting) value (and the conflict cannot be resolved automatically).
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

    def __str__(self) -> str:
        return (
            f"Cannot merge {self._object_type} data for '{self._object_name}' because of "
            f"conflicting {self._conflicting_attribute} values."
        )
