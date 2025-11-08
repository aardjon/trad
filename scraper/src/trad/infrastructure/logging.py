"""
Module for configuring the logging system.

trad uses the normal Python logging framework, that's why this module is only about configuring this
tool to our needs.

Call `initialize_logging()` first, then configure the desired output channels by calling any of the
`configure_*` functions. To define a different log level for single channels, use
`configure_log_channel()`.
"""

import sys
from logging import DEBUG, FileHandler, Formatter, Handler, StreamHandler, getLogger
from pathlib import Path

_log_formatter = Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
""" Global formatter for all log messages. """


def initialize_logging() -> None:
    """
    Initializes the logging framework (i.e. the root logger) for outputting messages. You still have
    to call any of the `configure_*_logging()` functions to actually get any output
    """
    root_logger = getLogger()
    root_logger.setLevel(DEBUG)


def _configure_log_handler(handler: Handler, log_level: int | str) -> None:
    handler.setFormatter(_log_formatter)
    handler.setLevel(log_level)
    root_logger = getLogger()
    root_logger.addHandler(handler)


def configure_console_logging(log_level: int | str) -> None:
    """
    Configure the logging framework to output messages of the given `log_level` (or higher) to the
    standard output.
    """
    handler = StreamHandler(sys.stdout)
    _configure_log_handler(handler, log_level)


def configure_file_logging(logfile: Path, log_level: int | str) -> None:
    """
    Configure the logging framework to append messages of the given `log_level` (or higher) to the
    given `logfile`.
    """
    handler = FileHandler(logfile, mode="w")
    _configure_log_handler(handler, log_level)


def configure_log_channel(log_channel: str, log_level: int | str) -> None:
    """
    Configure `log_channel` to output only messages of the given `log_level` or higher.
    """
    logger = getLogger(log_channel)
    logger.setLevel(log_level)
