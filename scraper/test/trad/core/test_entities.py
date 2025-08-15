"""
Unit tests for the core.entities module.
"""

import pytest

from trad.core.entities import GeoPosition, Summit, UniqueIdentifier


class TestGeoPosition:
    """
    Unit tests for the GeoPosition class.
    """

    @pytest.mark.parametrize(
        ("latlon_float", "latlon_int", "latlon_str"),
        [
            # Normal, valid values in all hemispheres
            (
                (50.462, 14.739),
                (504620000, 147390000),
                "50.462°N 14.739°E",
            ),
            (
                (-13.1234567, -7.1234567),
                (-131234567, -71234567),
                "13.1234567°S 7.1234567°W",
            ),
            (
                (-47.11, 42.0),
                (-471100000, 420000000),
                "47.11°S 42°E",
            ),
            (
                (9, -13.370815),
                (90000000, -133708150),
                "9°N 13.370815°W",
            ),
            # Extreme values: North pole and south pole
            (
                (90, 180),
                (900000000, 1800000000),
                "90°N 180°E",
            ),
            (
                (-90, -180),
                (-900000000, -1800000000),
                "90°S 180°W",
            ),
            # Extreme values: Zero (the hemisphere is lost because Python removes any zero sign)
            ((0, 0), (0, 0), "0°N 0°E"),
            ((-0, 0), (0, 0), "0°N 0°E"),
            ((0, -0), (0, 0), "0°N 0°E"),
            ((-0, -0), (0, 0), "0°N 0°E"),
        ],
    )
    def test_conversion(
        self,
        latlon_float: tuple[float, float],
        latlon_int: tuple[int, int],
        latlon_str: str,
    ) -> None:
        """
        Ensures the correct conversion of coordinate values between different formats.
        """
        pos = GeoPosition.from_decimal_degree(latlon_float[0], latlon_float[1])
        assert pos.latitude_int == latlon_int[0]
        assert pos.longitude_int == latlon_int[1]
        assert pos.latitude_decimal_degree == latlon_float[0]
        assert pos.longitude_decimal_degree == latlon_float[1]
        assert str(pos) == latlon_str

    @pytest.mark.parametrize(
        (
            "latlon_float",
            "latlon_int",
        ),
        [
            # One value is invalid
            ((90.1, 7), (901000000, 70000000)),
            ((-90.1, 7), (-901000000, 70000000)),
            ((7, 180.1), (70000000, 1801000000)),
            ((7, -180.1), (70000000, 1801000000)),
            # Both values are invalid
            ((-90.1, -180.1), (70000000, 1801000000)),
            ((90.1, 180.1), (70000000, 1801000000)),
        ],
    )
    def test_invalid_values(
        self,
        latlon_float: tuple[float, float],
        latlon_int: tuple[int, int],
    ) -> None:
        """
        Ensures that the construction methods do not accept invalid values.
        """
        with pytest.raises(ValueError, match="value must be within"):
            GeoPosition.from_decimal_degree(latlon_float[0], latlon_float[1])

        with pytest.raises(ValueError, match="value must be within"):
            GeoPosition(latlon_int[0], latlon_int[1])


class TestUniqueIdentifier:
    """
    Unit tests for the UniqueIdentifer class.
    """

    @pytest.mark.parametrize(
        ("object_name", "expected_identifier"),
        [
            ("AbCDe", "abcde"),  # Lower-case the name
            ("aäböcüdße", "abcde"),  # Remove german umlauts
            ("ab cd,ef-gh", "ab_cd_ef_gh"),  # Split at space and punctuation
            ("ef cd ab", "ab_cd_ef"),  # Order the segments correctly
            # Some real-world examples from Sächsische Schweiz, combining conversions
            ("Gamrigkegel", "gamrigkegel"),
            ("Müllerstein", "mllerstein"),
            ("Berggießhübler Turm, Westlicher", "berggiehbler_turm_westlicher"),
            ("Zerborstener Turm, Erster", "erster_turm_zerborstener"),
            ("Erster zerborstener Turm", "erster_turm_zerborstener"),
            ("Glück-Auf-Turm", "auf_glck_turm"),
            ("Glück Auf Turm", "auf_glck_turm"),
            ("Liebespaar, Südturm", "liebespaar_sdturm"),
            ("Liebespaar Südturm", "liebespaar_sdturm"),
            ("Lokomotive - Esse", "esse_lokomotive"),
            ("Lokomotive-Esse", "esse_lokomotive"),
        ],
    )
    def test_creation(self, object_name: str, expected_identifier: str) -> None:
        """
        Tests the correct generation of the unique identifier str and the string representation.
        """
        identifier = UniqueIdentifier(object_name)
        assert str(identifier) == expected_identifier

    @pytest.mark.parametrize(
        ("a", "b", "expect_equality"),
        [
            (UniqueIdentifier("qwertz"), UniqueIdentifier("qwertz"), True),
            (UniqueIdentifier("qwertz"), UniqueIdentifier("QwErTz"), True),
            (UniqueIdentifier("qwertz"), UniqueIdentifier("qwarks"), False),
        ],
    )
    def test_comparison(
        self, a: UniqueIdentifier, b: UniqueIdentifier, *, expect_equality: bool
    ) -> None:
        """
        Ensures that the equality comparison of unique identifiers works as expected.
        """
        assert (a == b) is expect_equality
        assert (a != b) is not expect_equality

    def test_dict_support(self) -> None:
        """
        Ensures that UniqueIdentifier objects can be used as dict keys.
        """
        ident1 = UniqueIdentifier("test1")
        ident2 = UniqueIdentifier("test2")

        id_dict = {ident1: "A", ident2: "B"}
        assert len(id_dict) == 2  # noqa: PLR2004
        assert ident1 in id_dict
        assert ident2 in id_dict
        assert id_dict[ident1] == "A"
        assert id_dict[ident2] == "B"
        assert id_dict[UniqueIdentifier("TesT1")] == "A"
        assert id_dict[UniqueIdentifier("TesT2")] == "B"


class TestSummit:
    """
    Unit tests for the Summit class.
    """

    def test_unique_identifier(self) -> None:
        """
        Tests the generation of the unique identifier.
        """
        dummy_summit_name = "Test Summit"
        summit = Summit(name=dummy_summit_name)
        assert summit.unique_identifier == UniqueIdentifier(dummy_summit_name)
