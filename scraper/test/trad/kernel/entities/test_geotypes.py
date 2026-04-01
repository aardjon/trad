"""
Unit tests for the trad.kernel.entities.geotypes module.
"""

import pytest

from trad.kernel.entities.geotypes import GeoPosition


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
