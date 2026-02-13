"""
Unit test for the trad.application.grades.fuzzy module
"""

from typing import Final

import pytest

from trad.application.grades import SaxonGrade
from trad.application.grades.fuzzy import FuzzyParser
from trad.kernel.errors import ValueParseError

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
    "XIIIa",
    "XIIIb",
    "XIIIc",
]


@pytest.mark.parametrize(
    ("grade_label", "expected_grade"),
    [  # Not grade at all
        ("", SaxonGrade()),
    ]
    # All "af" grades
    + [(s, SaxonGrade(af=i + 1)) for i, s in enumerate(all_grades)]
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
        ("II !", SaxonGrade(danger=True, af=2)),
        ("* VIIb !", SaxonGrade(danger=True, stars=1, af=8)),
    ]
    + [  # Some combinations and permutations
        ("** IXa (IXb) RP IXc", SaxonGrade(stars=2, af=13, ou=14, rp=15)),
        ("IXa RP IXc (IXb)", SaxonGrade(af=13, ou=14, rp=15)),
        ("! * VIIIb (VIIIc) RP IXa", SaxonGrade(danger=True, stars=1, af=11, ou=12, rp=13)),
        ("** IXa (IXb) RP IXc", SaxonGrade(stars=2, af=13, ou=14, rp=15)),
        ("VI RP VIIa", SaxonGrade(af=6, rp=7)),
        ("V (VI)", SaxonGrade(af=5, ou=6)),
        ("(IXc) RP Xa", SaxonGrade(ou=15, rp=16)),
        ("3/VI", SaxonGrade(af=6, jump=3)),
        ("1/VI (VIIa)", SaxonGrade(af=6, ou=7, jump=1)),
        ("2/IXb RP IXc", SaxonGrade(af=14, rp=15, jump=2)),
        ("! * 2/VIIb", SaxonGrade(danger=True, stars=1, af=8, jump=2)),
    ]
    + [  # ou or rp grades with jump
        ("VI (3/II)", SaxonGrade(af=6, ou=2)),
        ("4/VIIb (5/III)", SaxonGrade(jump=4, af=8, ou=3)),
        ("VIIIa RP 2/VIIIb", SaxonGrade(af=10, rp=11)),
        ("3/VIIb RP 3/VIIc", SaxonGrade(jump=3, af=8, rp=9)),
    ]
    + [  # More or less whitespaces
        ("4  ", SaxonGrade(jump=4)),
        ("4/I  ", SaxonGrade(jump=4, af=1)),
        ("3 / IV", SaxonGrade(jump=3, af=4)),
        (" III", SaxonGrade(af=3)),
        ("*IXa(IXb)RPIXc!", SaxonGrade(danger=True, stars=1, af=13, ou=14, rp=15)),
        (" IXc RP  Xa", SaxonGrade(af=15, rp=16)),
        ("VII b", SaxonGrade(af=8)),
        ("VI  (VIIIa) !", SaxonGrade(danger=True, af=6, ou=10)),
        ("VIIc (VIIIa )", SaxonGrade(af=9, ou=10)),
    ]
    + [  # Typos/Mistakes (close to real worls)
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
    ]
    + [  # Additional remarks or characters (real-world examples)
        ("IV ! anstr.", SaxonGrade(danger=True, af=4)),
        ("VI anstr.", SaxonGrade(af=6)),
        ("VIIc brüchig", SaxonGrade(af=9)),
        ("VI (original VIIIb)", SaxonGrade(af=6, ou=11)),
        ("VIIIc ?", SaxonGrade(af=12)),
        ("IXb, RP IXa", SaxonGrade(af=14, rp=13)),
    ]
    + [  # The longest possible climbing grade label (already stripped), just for fun :)
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
    parser = FuzzyParser()

    # First label has all parts set
    assert parser.parse_saxon_grade("* ! 3/V (VI) RP IV") == SaxonGrade(
        jump=3, af=5, ou=6, rp=4, stars=1, danger=True
    )

    # Subsequent requests must also return the expected grade, even if they do not use the
    # previously set parts.
    assert parser.parse_saxon_grade("VIIa") == SaxonGrade(af=7)
    assert parser.parse_saxon_grade("2") == SaxonGrade(jump=2)
