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

    @abstractmethod
    def get_log_file(self) -> Path | None:
        """
        Returns the file to write debug logs into, or None if file logging is disabled.
        """

    @abstractmethod
    def is_record_traffic_mode(self) -> bool:
        """
        Returns True if network traffic shall be recorded, otherwise False. All recorded traffic
        shall be written into the directory returned by `get_traffic_recordings_path()`. Must be
        False when `is_replay_traffic_mode()` is True.
        """

    @abstractmethod
    def is_replay_traffic_mode(self) -> bool:
        """
        Returns True if recorded network traffic shall be replayed (instead of doing real network
        requests), otherwise False. The recorded network traffic is read from the directory returned
        by `get_traffic_recordings_path()`. Must be False when `is_record_traffic_mode()` is True.
        """

    @abstractmethod
    def get_traffic_recordings_path(self) -> Path | None:
        """
        Returns the Path to write/read recorded network traffic into/from, or None if no traffic
        shall be recorded or replayed (depending on the settings of `is_record_traffic_mode()` and
        `is_replay_traffic_mode()`). Returns None if neither recording nor replaying network traffic
        is enabled, which is the normal case in a production environment.
        """
