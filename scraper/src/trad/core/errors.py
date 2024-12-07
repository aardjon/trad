"""
Provides exception classes that may be raised during the scraping process.
"""


class FilterError(Exception):
    """
    Raised by Filter when they cannot continue because of an unrecoverable error. This usually leads
    to an abortion of the whole scraper.
    """


class DataRetrievalError(FilterError):
    """
    Raised after an error while trying to retrieve route data. May be caused by network or
    permission problems, for example.
    """


class DataProcessingError(FilterError):
    """
    Raised when the retrieved data cannot be processed, for example because it is of an unexpected
    structure or format.
    """
