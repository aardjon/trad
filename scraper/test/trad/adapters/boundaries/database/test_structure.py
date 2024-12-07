"""
Unit tests for the trad.adapters.boundaries.database module.
"""

from contextlib import AbstractContextManager, nullcontext

import pytest

from trad.adapters.boundaries.database.common import EntityName
from trad.adapters.boundaries.database.structure import (
    ColumnDefinition,
    ColumnType,
    CreateTableQuery,
)


@pytest.mark.parametrize(
    (
        "column_names",
        "primary_key",
        "unique_constraints",
        "run_context",
    ),
    [
        (
            ["id"],
            ["id"],
            None,
            nullcontext(),
        ),
        (
            ["id", "key"],
            ["id", "key"],
            [["key"]],
            nullcontext(),
        ),
        (  # Primary key column undefined
            ["id"],
            ["id", "undefined"],
            None,
            pytest.raises(ValueError, match=".+primary key.*undefined column.*"),
        ),
        (  # Unique constraint column undefined
            ["id"],
            ["id"],
            [["undefined"]],
            pytest.raises(ValueError, match=".+unique constraint.*undefined column.*"),
        ),
    ],
)
def test_create_table_query(
    column_names: list[str],
    primary_key: list[EntityName],
    unique_constraints: list[list[EntityName]] | None,
    run_context: AbstractContextManager[None],
) -> None:
    """
    Test for the CreateTableQuery class:
     - Must accept valid specifications (including multiple columns)
     - Primary Keys must not refer to undefined columns
     - Constraints must not refer to undefined columns
    """
    with run_context:
        query = CreateTableQuery(
            table_name="test",
            column_definition=[
                ColumnDefinition(name=name, type=ColumnType.INTEGER) for name in column_names
            ],
            primary_key=primary_key,
            unique_constraints=unique_constraints,
        )
        assert query.table_name == "test"
