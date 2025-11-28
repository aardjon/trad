"""
Unit test for the trad.infrastructure.grade_regex module
"""

from typing import Final

import pytest

from trad.application.boundaries.grade_parser import SaxonGrade
from trad.infrastructure.grade_regex import RegexBasedParser

all_grades: Final = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VIIa",
    "VIIb",
    "VIIc",
    "VIIIa",
    "VIIIb",
    "VIIIc",
    "IXa",
    "IXb",
    "IXc",
    "Xa",
    "Xb",
    "Xc",
    "XIa",
    "XIb",
    "XIc",
    "XIIa",
    "XIIb",
    "XIIc",
]


@pytest.mark.parametrize(
    ("grade_label", "expected_grade"),
    # All "af" grades
    [(s, SaxonGrade(af=i + 1)) for i, s in enumerate(all_grades)]
    # All "ou" grades
    + [(f"({s})", SaxonGrade(ou=i + 1)) for i, s in enumerate(all_grades)]
    # All "rp" grades
    + [(f"RP {s}", SaxonGrade(rp=i + 1)) for i, s in enumerate(all_grades)]
    # All jump grades
    + [(str(j), SaxonGrade(jump=j)) for j in range(1, 6 + 1)]
    + [
        # Stars and danger marks (also in combination)
        ("! I", SaxonGrade(danger=True, af=1)),
        ("* II", SaxonGrade(stars=1, af=2)),
        ("! * III", SaxonGrade(danger=True, stars=1, af=3)),
        ("** IV", SaxonGrade(stars=2, af=4)),
        ("! ** V", SaxonGrade(danger=True, stars=2, af=5)),
    ]
    + [  # Some combinations (real-world examples)
        ("** IXa (IXb) RP IXc", SaxonGrade(stars=2, af=13, ou=14, rp=15)),
        ("! * VIIIb (VIIIc) RP IXa", SaxonGrade(danger=True, stars=1, af=11, ou=12, rp=13)),
        ("** IXa (IXb) RP IXc", SaxonGrade(stars=2, af=13, ou=14, rp=15)),
        ("VI RP VIIa", SaxonGrade(af=6, rp=7)),
        ("V (VI)", SaxonGrade(af=5, ou=6)),
        ("(IXc) RP Xa", SaxonGrade(ou=15, rp=16)),
        ("3/VI", SaxonGrade(af=6, jump=3)),
        ("1/VI (VIIa)", SaxonGrade(af=6, ou=7, jump=1)),
        ("2/IXb RP IXc", SaxonGrade(af=14, rp=15, jump=2)),
        ("! * 2/VIIb", SaxonGrade(danger=True, stars=1, af=8, jump=2)),
        # The longest possible climbing grade label (already stripped), just for fun :)
        ("!**3/VIIIa(VIIIb)RPVIIIc", SaxonGrade(danger=True, stars=2, af=10, ou=11, rp=12, jump=3)),
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
