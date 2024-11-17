"""
Module for configuraing the logging system.

trad uses the normal Python logging framework, that's why this module is only about configuring this
tool to our needs.
"""

from logging import basicConfig


def configure_logging(default_log_level: int | str) -> None:
    """
    Configure the logging framework (i.e. the root logger) to output all messages with at the given
    log level.
    """
    basicConfig(
        format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
        level=default_log_level,
    )
