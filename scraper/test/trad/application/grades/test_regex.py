"""
Unit test for the trad.application.grades.regex module
"""

import pytest

from trad.application.grades import SaxonGrade
from trad.application.grades.regex import RegexBasedParser
from trad.kernel.errors import ValueParseError

from . import common_grade_parse_expectations, ensure_parser_resuability


@pytest.mark.parametrize(
    ("grade_label", "expected_grade"),
    [
        *common_grade_parse_expectations,
        ("** IXa (IXb) RP IXc", SaxonGrade(stars=2, af=13, ou=14, rp=15)),
    ],
)
def test_parse_saxon_grade_happy_paths(
    grade_label: str,
    expected_grade: SaxonGrade,
) -> None:
    """
    Ensures that the parse_saxon_grade() method parses the given (valid!) strings correctly.
    """
    parser = RegexBasedParser()
    grade = parser.parse_saxon_grade(grade_label)
    assert grade == expected_grade


@pytest.mark.parametrize(
    "grade_label",
    [
        "Vb",  # There are no sub-grades in grade V
        "Vlll",  # Using lowercase L instead of upper-case I
        "i",  # Wrong case of a grade letter
        "VIIA",  # Wrong case of a sub-grade letter
        # Invalid Roman Numbers:
        "IIII",
        "VV",
        # Syntax errors:
        "VII VI",
        "V (III",
        "V/2",
        "RP Xa XIc",
        "III, II",
        # Out-of-scale grades:
        "7",
        "8",
        "9",
        "XIVa",
    ],
)
def test_parse_saxon_grade_errors(grade_label: str) -> None:
    """
    Ensures that the parse_saxon_grade() method raises ValueParseError for invalid grade labels.
    """
    parser = RegexBasedParser()
    with pytest.raises(ValueParseError):
        parser.parse_saxon_grade(grade_label)


def test_reusability() -> None:
    """
    Ensures that Parser instances can be reused, i.e. reset their internal state for new labels.
    """
    ensure_parser_resuability(RegexBasedParser())
