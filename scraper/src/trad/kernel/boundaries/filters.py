"""
Boundary interface to the filters component.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Iterator

from trad.kernel.boundaries.pipes import Pipe


class Filter(metaclass=ABCMeta):
    """
    Interface of a certain (architectural) "Filter" that can be executed.

    A Filter instance reads data from a single input source (either a Pipe or an external data
    source), performs a certain operation on it (e.g. adding or converting data) and writes the
    changed data into a single output source (either another Pipe or some external format). Each
    individual instance is only executed once, but it shall be possible to run different instances
    on the same pipes in parallel. Each Filter must be assigned to a certain stage to run in.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        The name of this filter.

        Can be used for identifying a certain processing step e.g. in progress log/error output, and
        should therefore be unique.
        """

    @abstractmethod
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        """
        Executes the operation of this Filter, reading data either from the given `input_pipe' or an
        external source, and writing transformed data either to the given `output_pipe` or an
        external destination.

        In case of an unrecoverable error, this method may raise any Exception. The whole scraper
        run is cancelled in such a case.
        """


class FilterFactory(metaclass=ABCMeta):
    """
    The factory for creating all Filters that should be executed.

    Filters are only instantiated when they are used.
    """

    @abstractmethod
    def get_stage_count(self) -> int:
        """
        Returns the total number of stages to execute Filters in.
        """

    @abstractmethod
    def iter_filter_stages(self) -> Iterator[list[Filter]]:
        """
        Iterates through all filter stages, each returned item being the list of all Filters to
        execute in the current stage (in an arbitrary order or even in parallel).
        """
