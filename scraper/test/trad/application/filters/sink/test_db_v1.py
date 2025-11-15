"""
Unit tests for the `trad.application.filters.sink.db_v1` module.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, call

from trad.application.boundaries.database import (
    DataRow,
    DataRowContainer,
    RelationalDatabaseBoundary,
)
from trad.application.filters.sink.db_v1 import DbSchemaV1Filter
from trad.application.filters.sink.db_v1.dbschema import (
    PostsTable,
    RoutesTable,
    SummitNamesTable,
    SummitsTable,
)
from trad.application.pipe import CollectedData
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import UNDEFINED_GEOPOSITION, GeoPosition, Post, Route, Summit


class TestDbSchemaV1Filter:
    def test_add_summit(self, tmp_path: Path) -> None:
        """
        Ensures that add_summit() executes the expected SQL statement (1), does it in exactly one
        database operation (2) and provides all query parameters separately (3).
        """
        input_pipe = CollectedData()
        input_pipe.add_summit(
            Summit(
                official_name="Foobar Rock",
                high_grade_position=GeoPosition.from_decimal_degree(13, 37),
            )
        )

        fake_db_boundary = Mock(RelationalDatabaseBoundary)
        fake_db_boundary.execute_read.return_value = [DataRow({"rowid": 42})]

        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=fake_db_boundary)
        db_writer.execute_filter(input_pipe, output_pipe=Mock(Pipe))

        expected_summits_sql_statement = (
            f"INSERT INTO {SummitsTable.TABLE_NAME} ("
            f"{SummitsTable.COLUMN_LATITUDE}, "
            f"{SummitsTable.COLUMN_LONGITUDE}"
            f") VALUES (?, ?) "
            f"ON CONFLICT DO UPDATE SET "
            f"{SummitsTable.COLUMN_LATITUDE}=excluded.{SummitsTable.COLUMN_LATITUDE}, "
            f"{SummitsTable.COLUMN_LONGITUDE}=excluded.{SummitsTable.COLUMN_LONGITUDE} "
            f"WHERE {SummitsTable.COLUMN_LATITUDE}={UNDEFINED_GEOPOSITION.latitude_int} "
            f"AND {SummitsTable.COLUMN_LONGITUDE}={UNDEFINED_GEOPOSITION.longitude_int}"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_summits_sql_statement, query_parameters=[130000000, 370000000]
        )
        self._check_database_finalization(fake_db_boundary)

    def test_add_route(self, tmp_path: Path) -> None:
        """
        Ensures that add_route() executes the expected SQL statement (1), does it in exactly one
        database operation (2) and provides all query parameters separately (3).
        """
        input_pipe = CollectedData()
        summit_id = input_pipe.add_summit(Summit(official_name="Mock Monument"))
        input_pipe.add_route(
            summit_id=summit_id,
            route=Route(
                route_name="Anxiety",
                grade="VIIb",
                grade_rp=8,
                grade_af=10,
                grade_ou=9,
                grade_jump=2,
                star_count=1,
                dangerous=True,
            ),
        )

        fake_db_boundary = Mock(RelationalDatabaseBoundary)
        fake_db_boundary.execute_read.return_value = DataRowContainer(
            [DataRow({"rowid": 0})]  # Dummy row ID
        )

        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=fake_db_boundary)
        db_writer.execute_filter(input_pipe, output_pipe=Mock(Pipe))

        expected_sql_statement = (
            f"INSERT OR IGNORE INTO {RoutesTable.TABLE_NAME} ("
            f"{RoutesTable.COLUMN_SUMMIT_ID}, "
            f"{RoutesTable.COLUMN_ROUTE_NAME}, "
            f"{RoutesTable.COLUMN_ROUTE_GRADE}, "
            f"{RoutesTable.COLUMN_GRADE_AF}, "
            f"{RoutesTable.COLUMN_GRADE_RP}, "
            f"{RoutesTable.COLUMN_GRADE_OU}, "
            f"{RoutesTable.COLUMN_GRADE_JUMP}, "
            f"{RoutesTable.COLUMN_STARS}, "
            f"{RoutesTable.COLUMN_DANGER}"
            f") VALUES (("
            f"SELECT {SummitNamesTable.COLUMN_SUMMIT_ID} FROM {SummitNamesTable.TABLE_NAME} "
            f"WHERE {SummitNamesTable.COLUMN_NAME}=? AND {SummitNamesTable.COLUMN_USAGE}=0 LIMIT 1"
            f"), ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_sql_statement,
            query_parameters=["Mock Monument", "Anxiety", "VIIb", 10, 8, 9, 2, 1, True],
        )
        self._check_database_finalization(fake_db_boundary)

    def test_add_post(self, tmp_path: Path) -> None:
        """
        Ensures that app_post() executes the expected SQL statement (1), does it in exactly one
        database operation (2) and provides all query parameters separately (3).
        """
        input_pipe = CollectedData()
        summit_id = input_pipe.add_summit(Summit(official_name="Mock Monument"))
        route_id = input_pipe.add_route(
            summit_id=summit_id,
            route=Route(
                route_name="Anxiety",
                grade="VIIb",
                grade_rp=8,
                grade_af=10,
                grade_ou=9,
                grade_jump=2,
                star_count=1,
                dangerous=True,
            ),
        )
        input_pipe.add_post(
            route_id=route_id,
            post=Post(
                user_name="John Doe",
                post_date=datetime.fromisoformat("2023-12-24T13:14:00+01:00"),
                comment="This is a great test!",
                rating=2,
            ),
        )

        fake_db_boundary = Mock(RelationalDatabaseBoundary)
        fake_db_boundary.execute_read.return_value = DataRowContainer(
            [DataRow({"rowid": 0})]  # Dummy row ID
        )

        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=fake_db_boundary)
        db_writer.execute_filter(input_pipe=input_pipe, output_pipe=Mock(Pipe))

        expected_sql_statement = (
            f"INSERT OR IGNORE INTO {PostsTable.TABLE_NAME} ("
            f"{PostsTable.COLUMN_ROUTE_ID}, "
            f"{PostsTable.COLUMN_USER_NAME}, "
            f"{PostsTable.COLUMN_COMMENT}, "
            f"{PostsTable.COLUMN_POST_DATE}, "
            f"{PostsTable.COLUMN_RATING}"
            f") VALUES (("
            f"SELECT {RoutesTable.COLUMN_ID} FROM {RoutesTable.TABLE_NAME} WHERE "
            f"{RoutesTable.COLUMN_SUMMIT_ID}=("
            f"SELECT {SummitNamesTable.COLUMN_SUMMIT_ID} FROM {SummitNamesTable.TABLE_NAME} "
            f"WHERE {SummitNamesTable.COLUMN_NAME}=? AND {SummitNamesTable.COLUMN_USAGE}=0 LIMIT 1"
            f") AND {RoutesTable.COLUMN_ROUTE_NAME}=? LIMIT 1"
            f"), ?, ?, ?, ?)"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_sql_statement,
            query_parameters=[
                "Mock Monument",
                "Anxiety",
                "John Doe",
                "This is a great test!",
                "2023-12-24T13:14:00+01:00",
                2,
            ],
        )
        self._check_database_finalization(fake_db_boundary)

    def _check_database_finalization(self, fake_db_boundary: Mock) -> None:
        """
        Ensures that the filter executes the VACUUM and ANALYZE commands and disconnects the
        database.
        """
        expected_sql_commands = ["ANALYZE", "VACUUM"]

        fake_db_boundary.execute_write.assert_has_calls(
            [call(command) for command in expected_sql_commands],
            any_order=False,
        )
        fake_db_boundary.disconnect.assert_called_once()
