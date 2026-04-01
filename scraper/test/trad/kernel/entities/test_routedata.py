"""
Unit tests for the trad.kernel.entities.routedata module.
"""

from typing import Final

import pytest

from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.names import NormalizedName
from trad.kernel.entities.routedata import Summit

# Two example points that can be used by some test cases.
_example_position_1: Final = GeoPosition.from_decimal_degree(50.8965380, 14.0819149)  # Barbarine
_example_position_2: Final = GeoPosition.from_decimal_degree(50.9052275, 14.2189117)  # Teufelsturm


class TestSummit:
    """
    Unit tests for the Summit class.
    """

    @pytest.mark.parametrize("sector_name", [None, "Bielatal", "Großer Zschand"])
    def test_sector(self, sector_name: str | None) -> None:
        """
        Ensures that the provided sector name can be retrieved again.
        """
        summit = Summit(official_name="Mt Dummy", sector=sector_name)
        assert summit.sector == sector_name

    @pytest.mark.parametrize(
        ("summit", "expected_return_value"),
        [
            # Single names
            (Summit(official_name="Official"), "Official"),
            (Summit(alternate_names=["Alternate"]), "Alternate"),
            (Summit(unspecified_names=["Unspecified"]), "Unspecified"),
            # From lists, choose the first one
            (Summit(alternate_names=["A2", "A1"]), "A2"),
            (Summit(unspecified_names=["U3", "U5"]), "U3"),
            # From several usages, choose the highest priority
            (Summit(official_name="O", alternate_names=["A"], unspecified_names=["U"]), "O"),
            (Summit(alternate_names=["A"], unspecified_names=["U"]), "A"),
        ],
    )
    def test_name(self, summit: Summit, expected_return_value: str) -> None:
        """
        Tests the `name` property, i.e. that the correct one of all available names is selected.
        """
        assert summit.name == expected_return_value

    @pytest.mark.parametrize(
        ("summit", "expected_return_value"),
        [
            (
                Summit("Dummy", high_grade_position=GeoPosition(504620000, 147390000)),
                GeoPosition(504620000, 147390000),
            ),
            (
                Summit("Dummy", low_grade_position=GeoPosition(504620000, 147390000)),
                GeoPosition(504620000, 147390000),
            ),
            (
                Summit(
                    "Dummy",
                    high_grade_position=GeoPosition(147390000, 504620000),
                    low_grade_position=GeoPosition(504620000, 147390000),
                ),
                GeoPosition(147390000, 504620000),
            ),
        ],
    )
    def test_position(self, summit: Summit, expected_return_value: GeoPosition) -> None:
        """
        Tests the `position` property, i.e. that the correct position value is returned.
        """
        assert summit.position.is_equal_to(expected_return_value)

    @pytest.mark.parametrize(
        ("summit", "expected_id_base"),
        [
            # Single names
            (Summit(official_name="Official"), "Official"),
            (Summit(alternate_names=["Alternate"]), "Alternate"),
            (Summit(unspecified_names=["Unspecified"]), "Unspecified"),
            # From lists, choose the first one
            (Summit(alternate_names=["A2", "A1"]), "A2"),
            (Summit(unspecified_names=["U3", "U5"]), "U3"),
            # From several usages, choose the highest priority
            (Summit(official_name="O", alternate_names=["A"], unspecified_names=["U"]), "O"),
            (Summit(alternate_names=["A"], unspecified_names=["U"]), "A"),
        ],
    )
    def test_normalized_name(self, summit: Summit, expected_id_base: str) -> None:
        """
        Tests the generation of the normalized name. `expected_id_base` is the name string which is
        expected to be normalized, `summit` is the Summit object to test.
        """
        assert summit.normalized_name == NormalizedName(expected_id_base)

    @pytest.mark.parametrize(
        ("input_summit", "expected_output_summit"),
        [
            # Happy paths: Summit data is valid
            (Summit("No position", sector="Area 21"), Summit("No position", sector="Area 21")),
            (
                Summit("With Position", high_grade_position=_example_position_1, sector="Area 22"),
                Summit("With Position", high_grade_position=_example_position_1, sector="Area 22"),
            ),
            (
                Summit("With Position", low_grade_position=_example_position_1, sector="Area 23"),
                Summit("With Position", low_grade_position=_example_position_1, sector="Area 23"),
            ),
            (
                Summit("Official", alternate_names=["alt1", "alt2"], sector="Area 24"),
                Summit("Official", alternate_names=["alt1", "alt2"], sector="Area 24"),
            ),
            (
                Summit("Official", unspecified_names=["unspec_name"], sector="Area 25"),
                Summit("Official", unspecified_names=["unspec_name"], sector="Area 25"),
            ),
            # Auto-Fix paths: invalid data that can be fixed automatically
            # Official name is missing: Use the next best name as the ONLY one
            (
                Summit(alternate_names=["alt_name1", "alt_name2"], sector="Sector A"),
                Summit(official_name="alt_name1", sector="Sector A"),
            ),
            (
                Summit(unspecified_names=["unspec_name1", "unspec_name2"], sector="Sector B"),
                Summit(official_name="unspec_name1", sector="Sector B"),
            ),
        ],
    )
    def test_fix_invalid_data(
        self,
        input_summit: Summit,
        expected_output_summit: Summit,
    ) -> None:
        """
        Test the validation and automatic data fixing (fix_invalid_data() method):
         - Valid data must not be changed
         - Missing official name: Fixed automatically
        """
        input_summit.fix_invalid_data()
        assert input_summit == expected_output_summit
