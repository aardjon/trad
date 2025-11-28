"""
Implementation of the grade string parser component.

Useful tool for testing/debugging regular expressions: https://regex101.com/
"""

import re
from re import Match
from typing import Final, override

from trad.application.boundaries.grade_parser import GradeParser, SaxonGrade
from trad.kernel.errors import ValueParseError


class RegexBasedParser(GradeParser):
    """
    Parses climbing grade labels with regular expressions ('re' module).
    """

    _saxon_grade_regex: Final = re.compile(
        r"""
        ^
        (?P<d>\!)?          # Optional danger mark ("!") in group "d"
        (?P<s>\*{0,2})      # Zero, one or two stars ("*") in group "s"
        (?:       # Optional jump and af grades in the "j1"/"j2" (jump) and "af1"/"af2" (af) groups:
            (?P<j1>\d)                           # Only a jump grade
            | (?P<j2>\d)\/(?P<af1>[IVX]+[abc]?)  # Both jump and af grades, separated by slash ("/")
            | (?P<af2>[IVX]+[abc]?)              # Only af grade
        )?
        (?:\((?P<ou>[IVX]+[abc]?)\))?    # Optional ou grade in group "ou"
        (?:RP(?P<rp>[IVX]+[abc]?))?      # Optional rp grade in group "rp"
        $
        """,
        re.VERBOSE,
    )
    """
    The regular expression for evaluating grade strings. Already compiled to improve runtime
    performance (because it is used very often).
    """

    @override
    def parse_saxon_grade(self, grade_label: str) -> SaxonGrade:
        stripped = self._normalize(grade_label)

        matches = self._saxon_grade_regex.match(stripped)
        if not matches:
            raise ValueParseError("climbing grade", grade_label)

        return SaxonGrade(
            danger=self._is_dangerous(matches),
            stars=self._get_star_count(matches),
            af=self._get_af_grade(matches),
            ou=self._get_ou_grade(matches),
            rp=self._get_rp_grade(matches),
            jump=self._get_jump_grade(matches),
        )

    def _normalize(self, grade_string: str) -> str:
        return grade_string.replace(" ", "")

    def _is_dangerous(self, matches: Match[str]) -> bool:
        return bool(matches.group("d"))

    def _get_star_count(self, matches: Match[str]) -> int:
        return len(matches.group("s"))

    def _get_jump_grade(self, re_match: Match[str]) -> int:
        jump_string = re_match.group("j1") or re_match.group("j2")
        return self._convert_jump_grade(jump_string)

    def _get_ou_grade(self, re_match: Match[str]) -> int:
        ou = re_match.group("ou")
        return self._convert_saxon_grade(ou)

    def _get_rp_grade(self, re_match: Match[str]) -> int:
        rp = re_match.group("rp")
        return self._convert_saxon_grade(rp)

    def _get_af_grade(self, re_match: Match[str]) -> int:
        af = re_match.group("af1") or re_match.group("af2")

        return self._convert_saxon_grade(af)

    def _convert_saxon_grade(self, grade: str | None) -> int:
        grade_string_map: Final = {
            None: 0,
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VIIa": 7,
            "VIIb": 8,
            "VIIc": 9,
            "VIIIa": 10,
            "VIIIb": 11,
            "VIIIc": 12,
            "IXa": 13,
            "IXb": 14,
            "IXc": 15,
            "Xa": 16,
            "Xb": 17,
            "Xc": 18,
            "XIa": 19,
            "XIb": 20,
            "XIc": 21,
            "XIIa": 22,
            "XIIb": 23,
            "XIIc": 24,
        }
        return grade_string_map[grade]

    def _convert_jump_grade(self, grade: str | None) -> int:
        grade_string_map: Final = {
            None: 0,
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
        }
        return grade_string_map[grade]
