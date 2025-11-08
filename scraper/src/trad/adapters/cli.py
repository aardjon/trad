"""
Implementation of the `trad.kernel.boundaries.settings` interface, which gives access to the user's
application configuration.
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import override

from trad.kernel.boundaries.settings import SettingsBoundary


class CliSettings(SettingsBoundary):
    """
    Settings implementation taking all configuration from the command line arguments.
    """

    def __init__(self) -> None:
        """
        Creates a new instance from the applications command line.

        In case of parsing errors, the application may immediately exit() from this constructor.
        """
        args = self.__parse_command_line()
        self.__is_verbose: bool = args.verbose
        self.__output_dir: Path = args.output_dir
        self.__log_file: list[Path] | None = args.logfile
        self.__record_traffic: list[Path] | None = args.record_traffic
        self.__replay_traffic: list[Path] | None = args.replay_traffic

    def __parse_command_line(self) -> Namespace:
        """Returns the parsed command line."""
        parser = self.__create_parser()
        return parser.parse_args()

    def __create_parser(self) -> ArgumentParser:
        """
        Creates the `argparse` parser and configures the allowed CLI arguments and options as well
        as their help texts. Returns the configured parser object.
        """
        parser = ArgumentParser()
        parser.add_argument(
            "output_dir",
            help="path to the directory to create the route database file(s) in",
            type=Path,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            help="activate more detailed debug output",
            required=False,
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "-l",
            "--logfile",
            nargs=1,
            required=False,
            type=Path,
            help="write debug log into the given file",
        )

        recorder_group = parser.add_mutually_exclusive_group()
        recorder_group.add_argument(
            "--record-traffic",
            nargs=1,
            required=False,
            type=Path,
            help="record all network traffic and store it into the directory following this option",
        )
        recorder_group.add_argument(
            "--replay-traffic",
            nargs=1,
            required=False,
            type=Path,
            help="replay the network traffic stored in the directory following this option",
        )
        return parser

    @override
    def is_verbose(self) -> bool:
        return self.__is_verbose

    @override
    def get_log_file(self) -> Path | None:
        return self.__log_file[0] if self.__log_file else None

    @override
    def get_output_dir(self) -> Path:
        return self.__output_dir

    @override
    def is_record_traffic_mode(self) -> bool:
        return bool(self.__record_traffic)

    @override
    def is_replay_traffic_mode(self) -> bool:
        return bool(self.__replay_traffic)

    @override
    def get_traffic_recordings_path(self) -> Path | None:
        return (
            self.__record_traffic[0]
            if self.__record_traffic
            else (self.__replay_traffic[0] if self.__replay_traffic else None)
        )
