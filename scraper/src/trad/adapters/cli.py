"""
Implementation of the `trad.core.boundaries.settings` interface, which gives access to the user's
application configuration.
"""

from argparse import ArgumentParser
from pathlib import Path
from typing import override

from trad.core.boundaries.settings import SettingsBoundary


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
        self.__is_verbose = args.verbose
        self.__output_file = args.output_file

    def __parse_command_line(self):
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
            "output_file",
            help="path to the route database file to create (must not exist already)",
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
        return parser

    @override
    def is_verbose(self) -> bool:
        return self.__is_verbose

    @override
    def get_output_file(self) -> Path:
        return self.__output_file
