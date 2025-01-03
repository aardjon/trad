"""
Integration test for the database creation via the V1 pipe and the underlying database
infrastructure.
"""

import datetime
from pathlib import Path
from sqlite3 import connect
from typing import Final

from trad.adapters.pipes.db_v1.pipe import DbSchemaV1Pipe
from trad.core.entities import Post, Route, Summit
from trad.infrastructure.sqlite3db import Sqlite3Database


def test_schema_v1_db_creation(tmp_path: Path) -> None:
    post_date: Final = datetime.datetime.now(tz=datetime.UTC)
    post_rating: Final = 2
    expected_index_count: Final = (
        2  # 'summits' and 'routes' tables each have one user-defined index
    )

    pipe = DbSchemaV1Pipe(output_directory=tmp_path, database_boundary=Sqlite3Database())
    pipe.initialize_pipe()
    pipe.add_summit_data(Summit(name="Falkenturm"))
    pipe.add_route_data(summit_name="Falkenturm", route=Route(route_name="AW", grade="II"))
    pipe.add_post_data(
        summit_name="Falkenturm",
        route_name="AW",
        post=Post(
            user_name="John Doe",
            comment="This is great!",
            post_date=post_date,
            rating=post_rating,
        ),
    )

    expected_db_file = tmp_path.joinpath("routedb_v1.sqlite")
    assert expected_db_file.exists()

    connection = connect(str(expected_db_file))

    # Ensure the summit has been added
    result_set = list(connection.execute("SELECT summit_name FROM summits"))
    assert len(result_set) == 1
    assert result_set[0][0] == "Falkenturm"

    # Ensure the route has been added
    result_set = list(connection.execute("SELECT route_name, route_grade FROM routes"))
    assert len(result_set) == 1
    assert result_set[0][0] == "AW"
    assert result_set[0][1] == "II"

    # Ensure the post has been added
    result_set = list(connection.execute("SELECT user_name, comment, post_date, rating FROM posts"))
    assert len(result_set) == 1
    assert result_set[0][0] == "John Doe"
    assert result_set[0][1] == "This is great!"
    assert datetime.datetime.fromisoformat(result_set[0][2]) == post_date
    assert result_set[0][3] == post_rating

    # Ensure that all indices have been created (ignoring the "autoindex" ones)
    result_set = list(
        connection.execute(
            "SELECT * FROM sqlite_master WHERE type='index' AND name NOT LIKE '%autoindex%'"
        )
    )
    assert len(result_set) == expected_index_count


def test_schema_v1_metadata_creation(tmp_path: Path) -> None:
    """Ensures that the database metadata is written correctly."""
    pipe = DbSchemaV1Pipe(output_directory=tmp_path, database_boundary=Sqlite3Database())
    pipe.initialize_pipe()

    expected_db_file = tmp_path.joinpath("routedb_v1.sqlite")
    assert expected_db_file.exists()

    connection = connect(str(expected_db_file))

    result_set = list(
        connection.execute(
            "SELECT schema_version_major, schema_version_minor, compile_time, vendor "
            "FROM database_metadata"
        )
    )
    assert len(result_set) == 1

    # Check schema version
    assert result_set[0][0] == 1
    assert result_set[0][1] == 0

    # Check vendor string
    assert result_set[0][3] == ""

    # Compare the creation time. Since the test takes a small amount of time, we cannot simply check
    # for equality. Instead, check that the time difference is not too big instead, assuming that
    # the test never needs more than a few seconds to run.
    current_time: Final = datetime.datetime.now(tz=datetime.UTC)
    compile_time = datetime.datetime.fromisoformat(result_set[0][2])
    max_allowed_difference: Final = 30
    assert (current_time - compile_time).total_seconds() < max_allowed_difference
