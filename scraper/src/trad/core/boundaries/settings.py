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
    def get_output_dir(self) -> Path:
        """
        Returns the full path to the directory into which the created database files are written.
        """

    @abstractmethod
    def is_verbose(self) -> bool:
        """
        Returns True if the application is configured for verbose/debug output, or False if not.
        """
