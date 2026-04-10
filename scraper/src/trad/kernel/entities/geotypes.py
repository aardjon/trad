"""
Provides utilities for representing geographical points.
"""

from math import cos, pi, sqrt
from typing import Final, Self, override


class GeoPosition:
    """
    A single geographical point in the WGS 84 geodetic system. It provides a maximum precision of
    geographic coordinates of about 1 cm (7 decimal places), which is the same as used by OSM.

    The coordinate values can be provided either as normal decimal degree values (float) or as
    integer values. Both provide the same precision, but the integer values are multiplied by
    10.000.000 to provide the same precision without the drawbacks of the floating point
    representation. The integer representation is the same as in the route database, to avoid
    unnecessary conversions.

    GeoPosition does not override the equality operator (==) on purpose, because the meaning of
    "equal positions" is not exactly intuitive and can depend on the use cases. That's why there are
    specialized methods (e.g. `is_equal_to()` and `is_within_radius()`) which implement different
    meanings of "equality".
    """

    _COORDINATE_PRECISION: Final = 10000000

    def __init__(self, latitude: int, longitude: int):
        """
        Create a new instance with the given (integer) coordinate values. Raises [ValueError] if
        invalid values are given.
        """
        if abs(latitude) > 90 * self._COORDINATE_PRECISION:
            raise ValueError("Latitude value must be within [-90, 90]")
        if abs(longitude) > 180 * self._COORDINATE_PRECISION:
            raise ValueError("Longitude value must be within [-180, 180]")

        self._latitude = latitude
        self._longitude = longitude

    @classmethod
    def from_decimal_degree(cls, latitude: float, longitude: float) -> Self:
        """
        Create a new GeoPosition instance from the given decimal degree values.
        """
        return cls(
            latitude=int(latitude * cls._COORDINATE_PRECISION),
            longitude=int(longitude * cls._COORDINATE_PRECISION),
        )

    @property
    def latitude_int(self) -> int:
        """
        The latitude value as integer within [-900000000, 900000000].
        """
        return self._latitude

    @property
    def longitude_int(self) -> int:
        """
        The longitude value as integer within [-1800000000, 1800000000]
        """
        return self._longitude

    @property
    def latitude_decimal_degree(self) -> float:
        """
        The latitude value as decimal degree.
        """
        return float(self._latitude) / self._COORDINATE_PRECISION

    @property
    def longitude_decimal_degree(self) -> float:
        """
        The longitude value as decimal degree.
        """
        return float(self._longitude) / self._COORDINATE_PRECISION

    def is_equal_to(self, other: Self) -> bool:
        """
        Return True if `self` and `other` are exactly equal, i.e. have the same internal latitude
        and longitude values.

        This is used for an exact data check, mainly in (but not limited to) unit tests. Two exactly
        equal coordinates from different sources may result in slighlty different internal values
        due to floating point operations/representation, so this check may return False for them.
        You may want to consider using `is_within_radius()` with a small distance in such cases.
        """
        return self.latitude_int == other.latitude_int and self.longitude_int == other.longitude_int

    def is_within_radius(self, other: Self, max_distance: float) -> bool:
        """
        Return True if the distance between `self` and `other` is smaller (or equal) `max_distance`
        meters, False if not. "Distance" means a direct, straight line - terrain and earth's
        curvature are ignored, so this check becomes less accurate as max_distance increases. Also,
        due to the involved floating point operations, the distance calculation may not be too
        precise in some cases.
        """
        # This simple distance calculation uses the Pythagorean theorem but improves it by
        # estimating the distance between two latitudes. This is good enough for the smaller
        # distances in the scale of hundreds of meters we are expecting in this application.
        # For more information and a detailled explanation, please have a look at
        # https://en.kompf.de/gps/distcalc.html (we are using the "Improved method" here).
        longitude_distance: Final = 111.3 * 1000  # We want the distance in meters
        average_lat = (self.latitude_decimal_degree + other.latitude_decimal_degree) / 2 * pi / 180
        dlat = longitude_distance * (self.latitude_decimal_degree - other.latitude_decimal_degree)
        dlon = (
            longitude_distance
            * cos(average_lat)
            * (self.longitude_decimal_degree - other.longitude_decimal_degree)
        )
        dist = sqrt(dlat * dlat + dlon * dlon)
        return dist <= max_distance

    @override
    def __str__(self) -> str:
        hemisphere_lat = "N" if self._latitude >= 0 else "S"
        hemisphere_lon = "E" if self._longitude >= 0 else "W"
        lat_str = f"{abs(self.latitude_decimal_degree):.7f}".rstrip("0").rstrip(".")
        lon_str = f"{abs(self.longitude_decimal_degree):.7f}".rstrip("0").rstrip(".")
        return f"{lat_str}°{hemisphere_lat} {lon_str}°{hemisphere_lon}"

    @override
    def __repr__(self) -> str:
        return str(self)
