"""
Boundary interface from the `application` ring to the grade parser component in the `infrastructure`
ring.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SaxonGrade:
    """
    Represents a parsed saxon climbing grade definition.

    A single grade is a positive integer number with 1 being the easiest difficulty. A value of 0
    is used if no grade is given.
    """

    stars: int = 0
    """ The number of stars ("*"). """
    danger: bool = False
    """ True if there is a danger mark ("!"), otherwise False. """
    af: int = 0
    """ The numeric 'AF' grade, or 0 if no climbing is required. """
    ou: int = 0
    """ The numeric 'OU' grade, or 0 if no support is required. """
    rp: int = 0
    """ The numeric 'RP' grade, or 0 if the RP style difficulty is the same as for AF. """
    jump: int = 0
    """ The numeric grade for a jump, or 0 if there is no jump. """


class GradeParser(ABC):
    """
    A parser for reading grade strings.
    """

    @abstractmethod
    def parse_saxon_grade(self, grade_label: str) -> SaxonGrade:
        """
        Parses the given saxon grade label (e.g. "*IV") into a new `SaxonGrade` instance. Raises
        ValueParseError in case the label is not a valid saxon grade.
        """
