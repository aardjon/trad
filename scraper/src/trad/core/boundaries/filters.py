"""
Boundary interface to the filters component.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum, auto

from trad.crosscuttings.di import DependencyProvider


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

    FILLING = auto()
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
    finalization to be published. Normally, only one filter should run in this stage (e.g. exporting
    the storage to the final destination).
    """


class Filter(metaclass=ABCMeta):
    """
    Interface of a certain (architectural) "filter" that can be executed.

    A Filter instance defines a certain operation on the current pipe, like adding or converting
    data, but there may also be Filters for "meta tasks" like initialisation or finalisation. Each
    individual instance is only executed once, but it shall be possible to run different instances
    on the same pipe in parallel. Each Filter must be assigned to a certain stage to run in.
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
    def execute_filter(self) -> None:
        """
        Executes the operation of this Filter.

        In case of an unrecoverable error, this method may raise any Exception. The whole scraper
        run is cancelled in such a case.
        """


class FilterRegistry:
    """
    The registry managing all filters that should be executed.

    Each Filter class must be registered to this class by calling [register_filter_class()]. Filters
    are only instantiated when they are used.
    """

    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Create a new FilterRegistry with the given [dependency_provider].
        """
        self.__dependency_provider = dependency_provider
        self.__registered_filter_classes: list[type[Filter]] = []
        """
        All registered filter classes.
        """

    def get_filters(self, stage: FilterStage) -> list[Filter]:
        """
        Instantiates and returns all filters that are assigned to the given [stage], in an arbitrary
        order.
        """
        return [
            filter_class(self.__dependency_provider)
            for filter_class in self.__registered_filter_classes
            if filter_class.get_stage() == stage
        ]

    def register_filter_class(self, new_filter_class: Filter) -> None:
        """
        Registers [new_filter_class] for execution.
        """
        self.__registered_filter_classes.append(new_filter_class)
