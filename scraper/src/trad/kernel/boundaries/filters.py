"""
Boundary interface to the filters component.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum, auto

from trad.kernel.boundaries.pipes import Pipe


class FilterStage(Enum):
    """
    Definition of the processing steps a Filter can be executed in. The stages are executed in that
    order. Several filters of the same stage can run in an arbitrary order or even in parallel.
    """

    IMPORTING = auto()
    """
    The data is being imported from various sources (there is no input Pipe). This is the state in
    which most filters run, additional data shall be added in this stage. At its end, the Pipe may
    contain multiple business objects for each physical one, providing different parts of the final
    data.
    """

    MERGING = auto()
    """
    The imported data is being merged. At the end of this stage, the Pipe contains a single
    (data-complete) business object for each physical one.
    """

    WRITING = auto()
    """
    The processed data is being written to the final destination(s). No output Pipe is written by
    this stage.
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
