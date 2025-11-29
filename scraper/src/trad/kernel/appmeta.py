"""
Static information about the application itself. This data does not change at runtime.
"""

from typing import Final

APPLICATION_NAME: Final = "trad.scraper"
""" The official name of the scraper application, as being displayed to the user. """

APPLICATION_VERSION: Final = "0.1.0"
"""
The current version of the scraper application.
If not on a tag (i.e. "development mode"), this is usually the version number that was included in
the last tag.
Please do not edit the version value manually here but use the `invoke version` command instead.
"""
