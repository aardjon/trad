"""
Boundary from the `filters` to the `pipes` component.
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path


class RouteDbCreatingPipe(metaclass=ABCMeta):
    """
    Interface to the Pipe component all Filters work on.

    The pipe is the shared storage that filters can read from and write their modified data into.
    The concrete structure and technical details of the pipe storage are hidden behind this
    interface, so that there may be different implementations (e.g. for different schema versions).
    The goal is that no filters need to be modified in case (only) the storage structure changes.

    Because there is only one pipe and filters may run in parallel, all pipe operations must be
    thread-safe.

    The pipe has an internal state: It must be initialized (by calling initialize_pipe()) before any
    other operation is allowed. If any method is called in the wrong state, it throws an
    InvalidStateError.
    """

    @abstractmethod
    def initialize_pipe(self, destination_path: Path) -> None:
        """
        Initializes the pipe for writing the created route database file into the given
        [destination_path].

        Must be called exactly once prior to any other operation.
        """
