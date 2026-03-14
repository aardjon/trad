"""
"Fuzzy" implementation of the grade string parser component.

This implementation can be used for evaluating free text user input.
"""

from typing import Final, override

from trad.application.grades import GradeParser, SaxonGrade
from trad.kernel.entities import NO_GRADE
from trad.kernel.errors import ValueParseError


class FuzzyParser(GradeParser):
    """
    Evaluates free text climbing grade labels that may have been entered by users. This parser tries
    to get grade values from a string, ignoring parts of it if necessary. However, the results may
    be wrong or less accurate in some cases.
    """

    _grade_string_map: Final = {
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
        "XIIIa": 25,
        "XIIIb": 26,
        "XIIIc": 27,
    }

    _maximum_jump_grade: Final = 7

    def __init__(self) -> None:
        """Create a new FuzzyParser instance."""
        self._last_jump = NO_GRADE
        self._af = NO_GRADE
        self._ou = NO_GRADE
        self._rp = NO_GRADE
        self._dangerous = False
        self._stars = 0

    @override
    def parse_saxon_grade(self, grade_label: str) -> SaxonGrade:
        # Reset the internal state to the default
        self._last_jump = NO_GRADE
        self._af = NO_GRADE
        self._ou = NO_GRADE
        self._rp = NO_GRADE
        self._dangerous = False
        self._stars = 0

        # Note: The call order is important because each one modifies the label string in a certain
        # way
        label_string = self._parse_danger_marks(grade_label)
        label_string = self._parse_stars(label_string)
        label_string = self._parse_ou_grade(label_string)
        label_string = self._parse_rp_grade(label_string)
        self._parse_af_grade(label_string)

        return SaxonGrade(
            jump=self._last_jump,
            af=self._af,
            ou=self._ou,
            rp=self._rp,
            danger=self._dangerous,
            stars=self._stars,
        )

    def _parse_af_grade(self, label: str) -> None:
        af_label = self._parse_jump_grade(label)
        self._af = self._parse_climbing_grade(af_label)

    def _parse_ou_grade(self, label: str) -> str:
        start_idx = label.find("(")
        end_idx = label.rfind(")")
        if start_idx < 0 and end_idx < 0:
            return label

        ou_label = label[start_idx + 1 : end_idx]
        ou_label = self._parse_jump_grade(ou_label)
        self._ou = self._parse_climbing_grade(ou_label)

        return label[:start_idx].strip() + label[end_idx + 1 :].strip()

    def _parse_rp_grade(self, label: str) -> str:
        idx = label.find("RP")
        if idx < 0:
            return label

        rp_label = label[idx + 2 :]
        rp_label = self._parse_jump_grade(rp_label)
        self._rp = self._parse_climbing_grade(rp_label)
        return label[:idx].strip()

    def _parse_danger_marks(self, label: str) -> str:
        if "!" in label:
            self._dangerous = True
            return label.replace("!", "")
        return label

    def _parse_stars(self, label: str) -> str:
        self._stars = label.count("*")
        return label.replace("*", "")

    def _parse_jump_grade(self, label: str) -> str:
        """
        The jump is a single digit at the beginning of the string. It may be standalone, or
        separated from the 'af' grade by a /
        """
        self._last_jump = NO_GRADE
        stripped_label = label.strip()

        slash_pos = stripped_label.find("/")
        if slash_pos == 0:
            # Starts with / --> syntax error
            raise ValueParseError("single grade", stripped_label)

        if slash_pos > 0:
            jump_label = stripped_label[0:slash_pos]
        elif stripped_label.isnumeric():
            jump_label = stripped_label
        else:
            return label

        try:
            jump_grade = int(jump_label)
        except ValueError as e:
            raise ValueParseError("single jump grade", jump_label) from e

        if 0 < jump_grade <= self._maximum_jump_grade:
            self._last_jump = jump_grade
        else:
            raise ValueParseError("single jump grade", jump_label)

        return stripped_label[len(jump_label) :].replace("/", "")

    def _parse_climbing_grade(self, single_grade: str) -> int:
        stripped_grade = single_grade.strip()
        if not stripped_grade:
            return NO_GRADE

        grade = self._parse_single_grade(stripped_grade)
        if grade == NO_GRADE:
            grade = self._guess_single_grade(stripped_grade)
        return grade

    def _parse_single_grade(self, single_grade: str) -> int:
        """
        Try to map the given string to a certain grade
        """
        normalized_grade = single_grade.strip()

        # Fix some common typing mistakes (e.g. casing). Order is important!
        for oldstr, newstr in (
            ("i", "I"),
            ("l", "I"),
            ("v", "V"),
            ("x", "X"),
            ("C", "c"),
            ("B", "b"),
            ("A", "a"),
            ("7a", "VIIa"),
            ("7b", "VIIb"),
            ("7c", "VIIc"),
            ("8a", "VIIIa"),
            ("8b", "VIIIb"),
            ("8c", "VIIIc"),
            ("9a", "IXa"),
            ("9b", "IXb"),
            ("9c", "IXc"),
            ("10a", "Xa"),
            ("10b", "Xb"),
            ("10c", "Xc"),
            ("11a", "XIa"),
            ("11b", "XIb"),
            ("11c", "XIc"),
            ("12a", "XIIa"),
            ("12b", "XIIb"),
            ("12c", "XIIc"),
            ("13a", "XIIIa"),
            ("13b", "XIIIb"),
            ("13c", "XIIIc"),
            ("1", "I"),
            ("2", "II"),
            ("3", "III"),
            ("4", "IV"),
            ("5", "V"),
            ("6", "VI"),
            (" ", ""),  # Remove intermediate spaces
        ):
            normalized_grade = normalized_grade.replace(oldstr, newstr)

        return self._grade_string_map.get(normalized_grade, NO_GRADE)

    def _guess_single_grade(self, single_grade: str) -> int:
        """
        If no grade value can be parsed for sure, try to guess by searching for valid grade labels
        within the given string.
        """
        unprocessed_string = single_grade
        found_labels = []
        for label in sorted(
            (g for g in self._grade_string_map if g), key=lambda s: len(s), reverse=True
        ):
            if unprocessed_string.count(label) > 0:
                found_labels.append(label)
                unprocessed_string = unprocessed_string.replace(label, "")

        if len(found_labels) == 1:
            return self._grade_string_map[found_labels[0]]
        # Found no or multiple different grades
        raise ValueParseError("single climbing grade", single_grade)
