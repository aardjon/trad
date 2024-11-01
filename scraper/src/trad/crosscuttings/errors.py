"""
Collection of some general exception types that can be useful in all parts of the application.
"""

class InvalidStateException(Exception):
    """
    Raised when an operation cannot be fulfilled due to an invalid application (or component) state.
    The reason is usually a programming or configuration error, the end user cannot do much about it
    when it happens unexpectedly at runtime.
    """
