"""
Base classes for some special kinds of Filters.
"""

from abc import abstractmethod
from typing import override

from trad.kernel.boundaries.filters import Filter
from trad.kernel.boundaries.pipes import Pipe


class SourceFilter(Filter):
    """
    Common base for all source filters, i.e. filters that do not read data from an input pipe but
    from some other source (e.g. a web service), and thus only need an output pipe.
    """

    @override
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        self._execute_source_filter(output_pipe)

    @abstractmethod
    def _execute_source_filter(self, output_pipe: Pipe) -> None:
        """
        The actual file execution method. Same as execute_filter() but without an input pipe.
        """


class SinkFilter(Filter):
    """
    Common base for all sink filters, i.e. filters that do not write data into an output pipe but
    to some other destination (e.g. a database file), and thus only need an input pipe.
    """

    @override
    def execute_filter(self, input_pipe: Pipe, output_pipe: Pipe) -> None:
        self._execute_sink_filter(input_pipe)

    @abstractmethod
    def _execute_sink_filter(self, input_pipe: Pipe) -> None:
        """
        The actual file execution method. Same as execute_filter() but without an output pipe.
        """
