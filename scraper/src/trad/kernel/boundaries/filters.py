"""
Boundary interface to the filters component.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum, auto

from trad.kernel.boundaries.pipes import Pipe


class FilterStage(Enum):
    """
    Definition of the manipulations a filter can do to the destination storage (the "pipe"). Each
    filter is assigned to a certain stage, depending on what it does. Several filters of the same
    state may run in an arbitrary order or even in parallel.
    """

    INITIALIZATION = auto()
    """
    The storage has not been created yet. Normally, only one filter should run in this stage
    (e.g. initializing the storage).
    """

    IMPORTING = auto()
    """
    The storage already contains some but still uncomplete data. This is the state in which most
    filters run, additional data shall be added in this stage.
    """

    OPTIMIZATION = auto()
    """
    The storage contains all data. Filters running in this stage may e.g. reorganize or optimize the
    data but are not supposed to add or delete actual business data.
    """

    FINALIZATION = auto()
    """
    The storage data has its final state and is ready to be used, but may still need some
    finalization to be published (e.g. writing the storage to its final destination). Normally, only
    one filter should run in this stage.
    """


class Filter(metaclass=ABCMeta):
    """
    Interface of a certain (architectural) "Filter" that can be executed.

    A Filter instance reads data from a singlen input source (either a Pipe or an external data
    source), performs a certain operation on it (e.g. adding or converting data) and writes the
    changed data into a single output source (either another Pipe or some external format). Each
    individual instance is only executed once, but it shall be possible to run different instances
    on the same pipes in parallel. Each Filter must be assigned to a certain stage to run in.
    """

    @staticmethod
    @abstractmethod
    def get_stage() -> FilterStage:
        """
        The stage this filter is assigned to (i.e. has to run in).
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
    The factory for creating all filters that should be executed.

    Filters are only instantiated when they are used.
    """

    @abstractmethod
    def create_filters(self, stage: FilterStage) -> list[Filter]:
        """
        Instantiates and returns all filters that are assigned to the given [stage], in an arbitrary
        order.
        """
