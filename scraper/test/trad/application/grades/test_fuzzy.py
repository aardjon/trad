"""
Unit test for the trad.application.grades.fuzzy module
"""

import pytest

from trad.application.grades import SaxonGrade
from trad.application.grades.fuzzy import FuzzyParser
from trad.kernel.errors import ValueParseError

from . import common_grade_parse_expectations, ensure_parser_resuability


@pytest.mark.parametrize(
    ("grade_label", "expected_grade"),
    [
        *common_grade_parse_expectations,
        # No grade at all
        ("", SaxonGrade()),
        # Stars and danger marks (also in combination)
        ("II !", SaxonGrade(danger=True, af=2)),
        ("* VIIb !", SaxonGrade(danger=True, stars=1, af=8)),
        # Some combinations and permutations
        ("IXa RP IXc (IXb)", SaxonGrade(af=13, ou=14, rp=15)),
        # ou or rp grades with jump
        ("VI (3/II)", SaxonGrade(af=6, ou=2)),
        ("4/VIIb (5/III)", SaxonGrade(jump=4, af=8, ou=3)),
        ("VIIIa RP 2/VIIIb", SaxonGrade(af=10, rp=11)),
        ("3/VIIb RP 3/VIIc", SaxonGrade(jump=3, af=8, rp=9)),
        # More or less whitespaces
        ("4  ", SaxonGrade(jump=4)),
        ("4/I  ", SaxonGrade(jump=4, af=1)),
        ("3 / IV", SaxonGrade(jump=3, af=4)),
        (" III", SaxonGrade(af=3)),
        ("*IXa(IXb)RPIXc!", SaxonGrade(danger=True, stars=1, af=13, ou=14, rp=15)),
        (" IXc RP  Xa", SaxonGrade(af=15, rp=16)),
        ("VII b", SaxonGrade(af=8)),
        ("VI  (VIIIa) !", SaxonGrade(danger=True, af=6, ou=10)),
        ("VIIc (VIIIa )", SaxonGrade(af=9, ou=10)),
        # Typos/Mistakes (close to real worls)
        ("VIib", SaxonGrade(af=8)),
        ("VIib (ViIIa) RPvIiIc", SaxonGrade(af=8, ou=10, rp=12)),
        ("lXA (lXC) RP lXB", SaxonGrade(af=13, rp=14, ou=15)),
        ("RP Vlllc", SaxonGrade(rp=12)),
        ("1/1", SaxonGrade(jump=1, af=1)),
        ("Vb", SaxonGrade(af=5)),
        # The same grade is there multiple times
        ("VV", SaxonGrade(af=5)),
        ("VIIa VIIa", SaxonGrade(af=7)),
        # Some people use arabic numbers instead of roman ones
        ("7a", SaxonGrade(af=7)),
        ("7b", SaxonGrade(af=8)),
        ("7c", SaxonGrade(af=9)),
        ("8a", SaxonGrade(af=10)),
        ("8b", SaxonGrade(af=11)),
        ("8c", SaxonGrade(af=12)),
        ("9a", SaxonGrade(af=13)),
        ("9b", SaxonGrade(af=14)),
        ("9c", SaxonGrade(af=15)),
        ("RP 10a", SaxonGrade(rp=16)),
        ("RP 10b", SaxonGrade(rp=17)),
        ("RP 10c", SaxonGrade(rp=18)),
        ("(11a)", SaxonGrade(ou=19)),
        ("(11b)", SaxonGrade(ou=20)),
        ("(11c)", SaxonGrade(ou=21)),
        ("12a", SaxonGrade(af=22)),
        ("12b", SaxonGrade(af=23)),
        ("12c", SaxonGrade(af=24)),
        ("13a", SaxonGrade(af=25)),
        ("13b", SaxonGrade(af=26)),
        ("13c", SaxonGrade(af=27)),
        # Additional remarks or characters (real-world examples)
        ("IV ! anstr.", SaxonGrade(danger=True, af=4)),
        ("VI anstr.", SaxonGrade(af=6)),
        ("VIIc brüchig", SaxonGrade(af=9)),
        ("VI (original VIIIb)", SaxonGrade(af=6, ou=11)),
        ("VIIIc ?", SaxonGrade(af=12)),
        ("IXb, RP IXa", SaxonGrade(af=14, rp=13)),
    ],
)
def test_parse_saxon_grade_happy_paths(
    grade_label: str,
    expected_grade: SaxonGrade,
) -> None:
    """
    Ensures that the parse_saxon_grade() method parses the given (valid!) strings correctly.
    """
    parser = FuzzyParser()
    grade = parser.parse_saxon_grade(grade_label)
    assert grade == expected_grade


@pytest.mark.parametrize(
    "grade_label",
    [
        # Invalid grades:
        "IIII",
        "VII",
        # Not unique:
        "VIIc VIIb",
        "VI IV",
        "RP Xa XIc",
        "III, II",
        # Syntax errors:
        "-",
        "V (III",
        "V/2",
        "3-4/I",
        "/III",
        "/",
        # Out-of-scale grades:
        "8",
        "9",
        "XIVa",
        # Some real-world examples:
        "VIIb (VIIIa od.5/VI)",
        "VIIc (VIIIc-IXb)",
        "VIIIa-VIIIc",
        "RP VIIb, VIIa",
        "6/VI (VIIc- VIIIb)",
    ],
)
def test_parse_saxon_grade_errors(grade_label: str) -> None:
    """
    Ensures that the parse_saxon_grade() method raises ValueParseError for invalid grade labels.
    """
    parser = FuzzyParser()
    with pytest.raises(ValueParseError):
        parser.parse_saxon_grade(grade_label)


def test_reusability() -> None:
    """
    Ensures that Parser instances can be reused, i.e. reset their internal state for new labels.
    """
    ensure_parser_resuability(FuzzyParser())
