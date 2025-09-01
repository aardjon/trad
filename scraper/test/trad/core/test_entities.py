"""
Unit tests for the core.entities module.
"""

from contextlib import AbstractContextManager, nullcontext

import pytest

from trad.core.entities import GeoPosition, NormalizedName, Summit
from trad.core.errors import MergeConflictError


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

    @pytest.mark.parametrize(
        ("point1", "point2", "expected_result"),
        [
            (  # Completely different positions
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                GeoPosition.from_decimal_degree(50.9421666, 14.0399232),
                False,
            ),
            (  # Latitude is the same
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                GeoPosition.from_decimal_degree(50.9424815, 14.0399232),
                False,
            ),
            (  # Longitude is the same
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                GeoPosition.from_decimal_degree(50.9421666, 14.0396597),
                False,
            ),
            (  # Equal positions
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                True,
            ),
        ],
    )
    def test_is_equal_to(
        self, *, point1: GeoPosition, point2: GeoPosition, expected_result: bool
    ) -> None:
        """
        Ensures that the `is_within_radius()` method works as expected:
         - Only return True if the latitude and longitude integers of both positions are equal
         - The operands can be swapped
        """
        assert point1.is_equal_to(point2) == expected_result
        assert point2.is_equal_to(point1) == expected_result

    @pytest.mark.parametrize(
        ("point1", "point2", "distance", "expected_result"),
        [
            (  # Distance of the two points is between 39 and 40 meters
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),  # Rhombus
                GeoPosition.from_decimal_degree(50.9421666, 14.0399232),  # Bärensteinscheibe
                40.0,
                True,
            ),
            (  # Distance of the two points is between 39 and 40 meters
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),  # Rhombus
                GeoPosition.from_decimal_degree(50.9421666, 14.0399232),  # Bärensteinscheibe
                39.1,
                False,
            ),
            (  # Both points are the same
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                GeoPosition.from_decimal_degree(50.9424815, 14.0396597),
                0.5,
                True,
            ),
        ],
    )
    def test_is_within_radius(
        self,
        *,
        point1: GeoPosition,
        point2: GeoPosition,
        distance: float,
        expected_result: bool,
    ) -> None:
        """
        Checks that the `is_within_radius()` method works as expected:
         - Distance calculation is correct with a precision of about one meter
         - The operands can be swapped
         - Also works for equal points
        """
        assert point1.is_within_radius(point2, distance) == expected_result
        assert point2.is_within_radius(point1, distance) == expected_result


class TestNormalizedName:
    """
    Unit tests for the NormalizedName class.
    """

    @pytest.mark.parametrize(
        ("object_name", "expected_normalization"),
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
    def test_creation(self, object_name: str, expected_normalization: str) -> None:
        """
        Tests the correct normalization and the string representation of the input value.
        """
        norm_name = NormalizedName(object_name)
        assert str(norm_name) == expected_normalization

    @pytest.mark.parametrize(
        ("a", "b", "expect_equality"),
        [
            (NormalizedName("qwertz"), NormalizedName("qwertz"), True),
            (NormalizedName("qwertz"), NormalizedName("QwErTz"), True),
            (NormalizedName("qwertz"), NormalizedName("qwarks"), False),
        ],
    )
    def test_comparison(
        self, a: NormalizedName, b: NormalizedName, *, expect_equality: bool
    ) -> None:
        """
        Ensures that the equality comparison of NormalizedNames works as expected.
        """
        assert (a == b) is expect_equality
        assert (a != b) is not expect_equality

    def test_dict_support(self) -> None:
        """
        Ensures that NormalizedName objects can be used as dict keys.
        """
        ident1 = NormalizedName("test1")
        ident2 = NormalizedName("test2")

        id_dict = {ident1: "A", ident2: "B"}
        assert len(id_dict) == 2  # noqa: PLR2004
        assert ident1 in id_dict
        assert ident2 in id_dict
        assert id_dict[ident1] == "A"
        assert id_dict[ident2] == "B"
        assert id_dict[NormalizedName("TesT1")] == "A"
        assert id_dict[NormalizedName("TesT2")] == "B"


class TestSummit:
    """
    Unit tests for the Summit class.
    """

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
        ("existing_summit", "summit_to_merge", "expected_summit", "failure_context"),
        [
            # Merge position data into an existing summit
            (
                Summit("Summit 1"),
                Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
                nullcontext(),
            ),
            (
                Summit("Summit 1"),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                nullcontext(),
            ),
            (
                Summit("Summit 1", high_grade_position=GeoPosition(504567000, 147650000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                Summit(
                    "Summit 1",
                    high_grade_position=GeoPosition(504567000, 147650000),
                    low_grade_position=GeoPosition(504620000, 147390000),
                ),
                nullcontext(),
            ),
            (
                Summit("Summit 1", low_grade_position=GeoPosition(504567000, 147650000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit 1", low_grade_position=GeoPosition(504567000, 147650000)),
                nullcontext(),
            ),
            # Merging equal position datá must not raise an error
            (
                Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
                Summit(
                    "Summit 1",
                    alternate_names=["Summit 2"],
                    high_grade_position=GeoPosition(504620000, 147390000),
                ),
                Summit(
                    "Summit 1",
                    alternate_names=["Summit 2"],
                    high_grade_position=GeoPosition(504620000, 147390000),
                ),
                nullcontext(),
            ),
            # Merge multiple names in various variants
            (
                Summit(official_name="Official", alternate_names=["Alt1", "Alt2"]),
                Summit(official_name="Official", alternate_names=["Alt3"]),
                Summit(official_name="Official", alternate_names=["Alt1", "Alt2", "Alt3"]),
                nullcontext(),
            ),
            (
                Summit(official_name="Official", alternate_names=["Alt2"]),
                Summit(alternate_names=["Official", "Alt3"]),
                Summit(official_name="Official", alternate_names=["Alt2", "Alt3"]),
                nullcontext(),
            ),
            (
                Summit(unspecified_names=["Unspec"]),
                Summit(official_name="Name", alternate_names=["Alt1", "Alt2"]),
                Summit(
                    official_name="Name",
                    alternate_names=["Alt1", "Alt2"],
                    unspecified_names=["Unspec"],
                ),
                nullcontext(),
            ),
            # Error Cases
            (
                Summit("Summit", high_grade_position=GeoPosition(504620000, 147390000)),
                Summit("Summit", high_grade_position=GeoPosition(404620000, 247390000)),
                Summit("Summit", high_grade_position=GeoPosition(504620000, 147390000)),
                pytest.raises(MergeConflictError),
            ),
        ],
    )
    def test_enrich(
        self,
        existing_summit: Summit,
        summit_to_merge: Summit,
        expected_summit: Summit,
        failure_context: AbstractContextManager[None],
    ) -> None:
        """
        Tests the enrichment ("merge") of an existing Summit object with data from another one:

        - Position data is added if there is none already
        - The official name is set if it is not already
        - All alternate and unspecified names are added to the existing Summit
        - The official name must not be included in the alternate names list
        - Unresolvable merge conflicts raise a MergeConflictError (preserving existing data)
        """
        with failure_context:
            existing_summit.enrich(summit_to_merge)

            assert existing_summit.official_name == expected_summit.official_name
            assert sorted(existing_summit.alternate_names) == sorted(
                expected_summit.alternate_names
            )
            assert sorted(existing_summit.unspecified_names) == sorted(
                expected_summit.unspecified_names
            )
            assert existing_summit.high_grade_position.is_equal_to(
                expected_summit.high_grade_position
            )

            assert existing_summit.low_grade_position.is_equal_to(
                expected_summit.low_grade_position
            )
