"""
Provides RankedValue, a generic tool for assigned a rank (priority) to a value.
"""

from typing import Final, Self, override

from trad.kernel.errors import InvalidStateError


class RankedValue[ValueType]:
    """
    Represents a value with an assigned rank. This can be useful when we need only one value, but
    expect to get several conflicting ones from different data sources. Each source defines ranks
    (aka "priorities") to the provided data, e.g. based on the general data quality or data
    precision. The merging algorithm can then choose the value with the best rank.

    The type parameter `ValueType` is the type of the stored value. It should not be `None` or
    `Optional`.

    The rank is a simple integer value, with smaller values being "better" ranks. Rank values
    higher than `WORST_PRODUCTION_QUALITY_RANK` are considered being too bad/inaccurate so they must
    never be written into a route database. They might still be useful for scraper internal usage
    (e.g. for logging or matching), so they are not ignored completely.
    Use `is_production_quality()` to check the data quality of a given value.

    RankedValue comes with an included representation of a null value, which can be created with
    `create_null()`. The returned instance means "there is no value" (similar to None) but allows to
    avoid repeated None checks in client code. Use `is_null()` to check if a given value is a null
    value.

    RankedValues compare to equal only if their values *and* their ranks are equal.
    """

    WORST_PRODUCTION_QUALITY_RANK: Final = 10
    """
    Threshold value for assigning the worst rank that can still be used for production values.
    """

    _NULL_VALUE_RANK: Final = WORST_PRODUCTION_QUALITY_RANK * 2
    """
    Special rank value that marks an instance as null object. This is the highest allowed rank,
    so that null values always come last when sorting by rank.
    """

    def __init__(self, value: ValueType | None, rank: int):
        """
        Initializes a new RankedValue instance.

        Do not use this constructor directly, prefer using one of the `create_valid()` and
        `create_null()` classmethods instead because they are more explicit.

        :param value: The value to be assigned to a rank, or none for null values.
        :param rank: The rank to be assigned to the given value.
        :raises ValueError: The given `rank` value is invalid.
        """
        if rank > self._NULL_VALUE_RANK:
            raise ValueError(f"Invalid rank value {rank}")
        self._value: ValueType | None = value
        self._rank = rank

    @classmethod
    def create_valid(cls, value: ValueType, rank: int) -> Self:
        """
        Create a new, valid RankedValue instance with the given `value` and `rank`.

        :param value: The value to be assigned to a rank.
        :param rank: The rank to be assigned to the given value.
        :raises ValueError: The given `rank` value is invalid.
        """
        if rank == cls._NULL_VALUE_RANK:
            raise ValueError(f"The rank value {rank} is reserved for null objects")
        return cls(value=value, rank=rank)

    @classmethod
    def create_null(cls) -> Self:
        """
        Create a null value instance. The returned object has a similar purpose than `None`, but
        helps to avoid a lot of None checks in the client code (Null Object design pattern). It's
        value is always None and its rank is always the worst/last.
        """
        return cls(value=None, rank=cls._NULL_VALUE_RANK)

    @property
    def value(self) -> ValueType:
        """
        Return the stored value. Raises if this instance is a null object.
        """
        if self._value is None:
            raise InvalidStateError("Null objects don't have a value")
        return self._value

    @property
    def rank(self) -> int:
        """
        Return the rank assigend to this value. A smaller value means "better" or "higher" rank.
        """
        return self._rank

    def is_production_quality(self) -> bool:
        """
        Return True if this value can be used for production (by means of data quality), e.g. end up
        in a route database.
        """
        return self._rank <= self.WORST_PRODUCTION_QUALITY_RANK

    def is_null(self) -> bool:
        """
        Return True if this instance represents a null object, False if not.
        """
        return self._rank == self._NULL_VALUE_RANK

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, RankedValue):
            return self._rank == other._rank and self._value == other._value
        return NotImplemented

    @override
    def __hash__(self) -> int:
        return hash((self.rank, self.value))
