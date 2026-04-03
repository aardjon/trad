"""
Unit tests for the trad.kernel.entities.ranked module.
"""

import pytest

from trad.kernel.entities.ranked import RankedValue
from trad.kernel.errors import InvalidStateError


def _unused(value: object) -> None:
    """
    Explictily marks the given value as unused to silence the linter.
    """


class TestRankedValue:
    """
    Unit tests for the RankedValue class.
    """

    @pytest.mark.parametrize(
        ("value", "rank"),
        [
            (42, 1),
            ("test", 2),
            ({"pi": 3.14}, 3),
        ],
    )
    def test_values(self, value: object, rank: int) -> None:
        """
        Ensure the correct behaviour of valid values:
        - It works with different data types
        - The provided value can be retrieved again
        - The provided rank can be retrieved again
        - `is_null()` returns False
        """
        ranked_value = RankedValue.create_valid(value=value, rank=rank)
        assert not ranked_value.is_null()
        assert ranked_value.rank == rank
        assert ranked_value.value == value

    def test_null(self) -> None:
        """
        Ensure that null values behave as expected:
        - `is_null()` returns True
        - `is_production_quality()` returns False
        - Accessing their value raises InvalidStateError
        - Their rank is worse than `WORST_PRODUCTION_QUALITY_RANK`, with at least 5 ranks in between
        """
        ranked_value = RankedValue[object].create_null()
        assert ranked_value.is_null()
        assert ranked_value.rank > (RankedValue.WORST_PRODUCTION_QUALITY_RANK + 5)
        with pytest.raises(InvalidStateError):
            _unused(ranked_value.value)

    @pytest.mark.parametrize(
        ("rank", "expect_production_quality"),
        [
            pytest.param(1, True, id="Lowest rank value"),
            (2, True),
            (5, True),
            pytest.param(10, True, id="Highest possible production grade rank"),
            (11, False),
            pytest.param(14, False, id="Highest possible non-null object rank"),
        ],
    )
    def test_production_quality(self, rank: int, *, expect_production_quality: bool) -> None:
        """
        Ensure that `is_production_quality()` returns the expected value for different ranks.
        Don't check null values here.
        """
        ranked_value = RankedValue.create_valid("Dummy value", rank)
        assert not ranked_value.is_null()
        assert ranked_value.is_production_quality() == expect_production_quality

    @pytest.mark.parametrize(
        "invalid_rank",
        [
            20,  # Reserved (rank of null values)
            21,
            100,
        ],
    )
    def test_create_valid_invalid_rank(self, invalid_rank: int) -> None:
        """
        Ensure that object creation fails for invalid ranks when using the `create_valid()`
        classmethod.
        """
        with pytest.raises(ValueError, match=f"rank value {invalid_rank}"):
            RankedValue.create_valid("Valid value", invalid_rank)

    @pytest.mark.parametrize(
        ("ranked_value1", "ranked_value2", "expect_equal"),
        [
            (RankedValue("42", 1), RankedValue("42", 1), True),
            (RankedValue("42", 1), RankedValue("42", 2), False),
            (RankedValue("42", 1), RankedValue("24", 1), False),
            (RankedValue("24", 2), RankedValue("42", 1), False),
            (RankedValue("25", 3), RankedValue.create_null(), False),
            (RankedValue.create_null(), RankedValue("23", 3), False),
            (RankedValue.create_null(), RankedValue.create_null(), True),
        ],
    )
    def test_equality[T](
        self,
        ranked_value1: RankedValue[T],
        ranked_value2: RankedValue[T],
        *,
        expect_equal: bool,
    ) -> None:
        """
        Ensure that the equality operator works as expected
        """
        assert (ranked_value1 == ranked_value2) == expect_equal
