"""
Some general tools that can be commonly used by all source filters.
"""

from pydantic.config import ConfigDict
from pydantic.main import BaseModel


class ReadOnlyPydanticModel(BaseModel):
    """
    Common base class for Pydantic models that cannot be manipulated. This is the case for all data
    retrieved from some remote service.
    """

    model_config = ConfigDict(frozen=True)
