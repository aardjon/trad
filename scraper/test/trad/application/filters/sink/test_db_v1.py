"""
Unit tests for the `trad.application.filters.sink.db_v1` module.
"""

from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import connect
from unittest.mock import Mock, call
from zoneinfo import ZoneInfo

import pytest
from time_machine import TimeMachineFixture

from trad.application.boundaries.database import (
    DataRow,
    DataRowContainer,
    RelationalDatabaseBoundary,
)
from trad.application.filters.sink.db_v1 import DbSchemaV1Filter
from trad.application.filters.sink.db_v1.dbschema import (
    AreasTable,
    DatabaseMetadataTable,
    ExternalDataSourcesTable,
    PostsTable,
    RoutesTable,
    SummitNamesTable,
    SummitsTable,
)
from trad.application.filters.source.route_data_factory import RouteDataFactory
from trad.application.pipes import CollectedData
from trad.infrastructure.sqlite3db import Sqlite3Database
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities.datasources import ExternalSource
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import Post, Summit


class TestDbSchemaV1Filter:
    _data_factory = RouteDataFactory(
        source_label="Unit Test",
        summit_sector_rank=1,
        summit_position_rank=3,
        route_rating_rank=1,
    )

    _example_sector = RankedValue.create_valid("Test", 1)

    def test_add_summit(self, tmp_path: Path) -> None:
        """
        Ensures that add_summit() executes the expected SQL statement (1), does it in exactly one
        database operation (2) and provides all query parameters separately (3).
        """
        input_pipe = CollectedData()
        input_pipe.add_summit(
            Summit(
                official_name="Foobar Rock",
                position=RankedValue.create_valid(GeoPosition.from_decimal_degree(13, 37), 3),
                sector=self._example_sector,
            )
        )

        fake_db_boundary = Mock(RelationalDatabaseBoundary)
        fake_db_boundary.execute_read.return_value = [DataRow({"rowid": 42})]

        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=fake_db_boundary)
        db_writer.execute_filter(input_pipe, output_pipe=Mock(Pipe))

        expected_summits_sql_statement = (
            f"INSERT INTO {SummitsTable.TABLE_NAME} ("
            f"{SummitsTable.COLUMN_LATITUDE}, "
            f"{SummitsTable.COLUMN_LONGITUDE}, "
            f"{SummitsTable.COLUMN_AREA_ID}"
            f") VALUES (?, ?, ("
            f"SELECT {AreasTable.COLUMN_ID} FROM {AreasTable.TABLE_NAME} "
            f"WHERE {AreasTable.COLUMN_NAME} = ? LIMIT 1"
            "))"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_summits_sql_statement,
            query_parameters=[130000000, 370000000, self._example_sector.value],
        )

        expected_sectors_sql_statement = (
            f"INSERT INTO {AreasTable.TABLE_NAME} ({AreasTable.COLUMN_NAME}) VALUES (?)"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_sectors_sql_statement, query_parameters=[self._example_sector.value]
        )

        self._check_database_finalization(fake_db_boundary)

    def test_add_route(self, tmp_path: Path) -> None:
        """
        Ensures that add_route() executes the expected SQL statement (1), does it in exactly one
        database operation (2) and provides all query parameters separately (3).
        """
        input_pipe = CollectedData()
        summit_id = input_pipe.add_summit(
            Summit(official_name="Mock Monument", sector=self._example_sector)
        )
        input_pipe.add_route(
            summit_id=summit_id,
            route=self._data_factory.create_route(
                route_name="Anxiety",
                directions="Don't go down!",
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
            f"INSERT INTO {RoutesTable.TABLE_NAME} ("
            f"{RoutesTable.COLUMN_SUMMIT_ID}, "
            f"{RoutesTable.COLUMN_ROUTE_NAME}, "
            f"{RoutesTable.COLUMN_ROUTE_GRADE}, "
            f"{RoutesTable.COLUMN_GRADE_AF}, "
            f"{RoutesTable.COLUMN_GRADE_RP}, "
            f"{RoutesTable.COLUMN_GRADE_OU}, "
            f"{RoutesTable.COLUMN_GRADE_JUMP}, "
            f"{RoutesTable.COLUMN_STARS}, "
            f"{RoutesTable.COLUMN_DANGER}, "
            f"{RoutesTable.COLUMN_ENTRY_LATITUDE}, "
            f"{RoutesTable.COLUMN_ENTRY_LONGITUDE}"
            f") VALUES (("
            f"SELECT {SummitNamesTable.COLUMN_SUMMIT_ID} FROM {SummitNamesTable.TABLE_NAME} "
            f"WHERE {SummitNamesTable.COLUMN_NAME}=? AND {SummitNamesTable.COLUMN_USAGE}=0 LIMIT 1"
            f"), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_sql_statement,
            query_parameters=["Mock Monument", "Anxiety", "", 10, 8, 9, 2, 1, True, 0, 0],
        )
        self._check_database_finalization(fake_db_boundary)

    def test_add_post(self, tmp_path: Path) -> None:
        """
        Ensures that app_post() executes the expected SQL statement (1), does it in exactly one
        database operation (2) and provides all query parameters separately (3).
        """
        input_pipe = CollectedData()
        input_pipe.add_source(ExternalSource("Testing", "[DOESNTMATTER]", "trad Authors"))
        summit_id = input_pipe.add_summit(
            Summit(official_name="Mock Monument", sector=self._example_sector)
        )
        route_id = input_pipe.add_route(
            summit_id=summit_id,
            route=self._data_factory.create_route(
                route_name="Anxiety",
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
                post_date=datetime.fromisoformat("2023-12-24T12:14:00+00:00"),
                comment="This is a great test!",
                rating=2,
                source_label="Testing",
            ),
        )

        fake_db_boundary = Mock(RelationalDatabaseBoundary)
        fake_db_boundary.execute_read.return_value = DataRowContainer(
            [DataRow({"rowid": 0})]  # Dummy row ID
        )

        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=fake_db_boundary)
        db_writer.execute_filter(input_pipe=input_pipe, output_pipe=Mock(Pipe))

        expected_sql_statement = (
            f"INSERT INTO {PostsTable.TABLE_NAME} ("
            f"{PostsTable.COLUMN_ROUTE_ID}, "
            f"{PostsTable.COLUMN_USER_NAME}, "
            f"{PostsTable.COLUMN_COMMENT}, "
            f"{PostsTable.COLUMN_POST_DATE}, "
            f"{PostsTable.COLUMN_RATING}, "
            f"{PostsTable.COLUMN_SOURCE_ID}"
            f") VALUES (("
            f"SELECT {RoutesTable.COLUMN_ID} FROM {RoutesTable.TABLE_NAME} WHERE "
            f"{RoutesTable.COLUMN_SUMMIT_ID}=("
            f"SELECT {SummitNamesTable.COLUMN_SUMMIT_ID} FROM {SummitNamesTable.TABLE_NAME} "
            f"WHERE {SummitNamesTable.COLUMN_NAME}=? AND {SummitNamesTable.COLUMN_USAGE}=0 LIMIT 1"
            f") AND {RoutesTable.COLUMN_ROUTE_NAME}=? LIMIT 1"
            f"), ?, ?, ?, ?, ("
            f"SELECT {ExternalDataSourcesTable.COLUMN_ID} "
            f"FROM {ExternalDataSourcesTable.TABLE_NAME} "
            f"WHERE {ExternalDataSourcesTable.COLUMN_LABEL}=? LIMIT 1"
            "))"
        )
        fake_db_boundary.execute_write.assert_any_call(
            query=expected_sql_statement,
            query_parameters=[
                "Mock Monument",
                "Anxiety",
                "John Doe",
                "This is a great test!",
                "2023-12-24T12:14:00+00:00",
                2,
                "Testing",
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

    @pytest.mark.parametrize(
        ("post_date", "expected_timestamp"),
        [
            pytest.param(
                datetime(2026, 9, 3, 18, 51, 29, tzinfo=UTC),
                "2026-09-03T18:51:29+00:00",
                id="UTC",
            ),
            pytest.param(
                datetime(2026, 9, 3, 18, 51, 29, tzinfo=ZoneInfo("Europe/Berlin")),
                "2026-09-03T16:51:29+00:00",
                id="CEST",
            ),
            pytest.param(
                datetime(2026, 12, 3, 18, 51, 29, tzinfo=ZoneInfo("Europe/Berlin")),
                "2026-12-03T17:51:29+00:00",
                id="CET",
            ),
        ],
    )
    def test_post_datetimes_utc(
        self,
        post_date: datetime,
        expected_timestamp: str,
        tmp_path: Path,
    ) -> None:
        """
        Ensures that the post timestamps are correctly written into the database as UTC.
        """
        input_pipe = CollectedData()
        input_pipe.add_source(ExternalSource("Test", "http://", "Someone"))
        summit_id = input_pipe.add_summit(
            self._data_factory.create_summit(
                "My Summit",
                sector="My Area",
            )
        )
        route_id = input_pipe.add_route(summit_id, self._data_factory.create_route("My Route"))
        input_pipe.add_post(
            route_id,
            Post(
                post_date=post_date,
                user_name="Me",
                comment="My Comment",
                rating=0,
                source_label="Test",
            ),
        )

        test_db = Sqlite3Database()
        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=test_db)
        db_writer.execute_filter(input_pipe=input_pipe, output_pipe=Mock(Pipe))

        connection = connect(db_writer.destination_file)
        post_data = list(
            connection.execute(f"SELECT {PostsTable.COLUMN_POST_DATE} FROM {PostsTable.TABLE_NAME}")
        )
        assert post_data[0][0] == expected_timestamp

    @pytest.mark.parametrize(
        ("compile_time", "expected_timestamp"),
        [
            pytest.param(
                datetime(2026, 9, 3, 0, 1, 42, tzinfo=UTC),
                "2026-09-03T00:01:42+00:00",
                id="UTC",
            ),
            pytest.param(
                datetime(2026, 11, 3, 0, 1, 42, tzinfo=ZoneInfo("Europe/Berlin")),
                "2026-11-02T23:01:42+00:00",
                id="CET",
            ),
            pytest.param(
                datetime(2026, 8, 3, 0, 1, 42, tzinfo=ZoneInfo("Europe/Berlin")),
                "2026-08-02T22:01:42+00:00",
                id="CEST",
            ),
        ],
    )
    def test_db_creation_timestamp_utc(
        self,
        compile_time: datetime,
        expected_timestamp: str,
        time_machine: TimeMachineFixture,
        tmp_path: Path,
    ) -> None:
        """Ensures that the DB compile time date is correctly stored as UTC."""
        time_machine.move_to(compile_time)
        test_db = Sqlite3Database()
        db_writer = DbSchemaV1Filter(output_directory=tmp_path, database_boundary=test_db)
        db_writer.execute_filter(input_pipe=CollectedData(), output_pipe=Mock(Pipe))

        connection = connect(db_writer.destination_file)
        db_meta_data = list(
            connection.execute(
                f"SELECT {DatabaseMetadataTable.COLUMN_COMPILE_TIME} FROM {DatabaseMetadataTable.TABLE_NAME}"
            )
        )
        assert db_meta_data[0][0] == expected_timestamp
