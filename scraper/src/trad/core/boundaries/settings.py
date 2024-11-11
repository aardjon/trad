"""
Boundary interface to the settings component.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class SettingsBoundary(ABC):
    """
    Interface to the component managing the settings of the current run.
    """

    @abstractmethod
    def get_output_file(self) -> Path:
        """
        Returns the full path to the output database file that shall be created.
        """

    @abstractmethod
    def is_verbose(self) -> bool:
        """
        Returns True if the applicaiton is configured for verbose/debug output, or False if not.
        """
