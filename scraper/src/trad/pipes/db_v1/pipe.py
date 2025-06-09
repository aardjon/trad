"""
Concrete pipe implementation writing a route database with schema version 1.
"""

import datetime
from logging import getLogger
from pathlib import Path
from typing import Final, override

from trad.adapters.boundaries.database import RelationalDatabaseBoundary, SqlStatement
from trad.core.boundaries.pipes import Pipe
from trad.core.entities import UNDEFINED_GEOPOSITION, Post, Route, Summit
from trad.crosscuttings.appmeta import APPLICATION_NAME, APPLICATION_VERSION
from trad.pipes.db_v1.dbschema import (
    DatabaseMetadataTable,
    DatabaseSchema,
    PostsTable,
    RoutesTable,
    SummitsTable,
)

_logger = getLogger(__name__)


class DbSchemaV1Pipe(Pipe):
    """
    Pipe implementation for creating a route database file (schema version 1) that can be used with
    the trad mobile app.

    This class encapsulates all knowledge about the structure of the route database in this
    particular schema version.
    """

    _DB_FILE_NAME: Final = "routedb_v1.sqlite"
    """ File name to use for the destination database file. """

    def __init__(self, output_directory: Path, database_boundary: RelationalDatabaseBoundary):
        """
        Create a new pipe that writes the generated database file into the given [output_directory],
        using the provided [database_boundary].
        """
        self.__destination_file = output_directory.joinpath(self._DB_FILE_NAME)
        self.__database_boundary = database_boundary

    @override
    def initialize_pipe(self) -> None:
        _logger.debug("Initializing routedb pipe for writing into %s", self.__destination_file)
        self.__database_boundary.connect(self.__destination_file, overwrite=True)

        schema = DatabaseSchema()
        self._create_schema(schema)
        self._write_metadata(schema)

    def _create_schema(self, schema_definition: DatabaseSchema) -> None:
        _logger.debug("Creating database schema")
        for table_definition in schema_definition.get_table_schemata():
            # Create the table
            self.__database_boundary.execute_write(query=table_definition.table_ddl())
            # Create all indices for this table
            for index_creation_statement in table_definition.index_ddl():
                self.__database_boundary.execute_write(query=index_creation_statement)

    def _write_metadata(self, schema_definition: DatabaseSchema) -> None:
        _logger.debug("Writing database metadata")
        column_list = [
            DatabaseMetadataTable.COLUMN_SCHEMA_VERSION_MAJOR,
            DatabaseMetadataTable.COLUMN_SCHEMA_VERSION_MINOR,
            DatabaseMetadataTable.COLUMN_VENDOR,
            DatabaseMetadataTable.COLUMN_COMPILE_TIME,
        ]
        column_names = ", ".join(column_list)
        value_placeholders = self._get_value_placeholders(len(column_list))

        insert_statement = SqlStatement(
            f"INSERT OR IGNORE INTO {DatabaseMetadataTable.TABLE_NAME} ({column_names}) "
            f"VALUES ({value_placeholders})"
        )

        major, minor = schema_definition.get_schema_version()
        self.__database_boundary.execute_write(
            query=insert_statement,
            query_parameters=[
                major,
                minor,
                f"{APPLICATION_NAME} {APPLICATION_VERSION}",
                datetime.datetime.now(tz=datetime.UTC).isoformat(),
            ],
        )

    @override
    def collect_statistics(self) -> None:
        self.__database_boundary.run_analyze()

    @override
    def shrink(self) -> None:
        self.__database_boundary.run_vacuum()

    @override
    def add_or_enrich_summit(self, summit: Summit) -> None:
        column_list = [
            SummitsTable.COLUMN_SUMMIT_NAME,
            SummitsTable.COLUMN_LATITUDE,
            SummitsTable.COLUMN_LONGITUDE,
        ]
        column_names = ", ".join(column_list)
        value_placeholders = self._get_value_placeholders(len(column_list))
        column_updates = ", ".join(f"{col}=excluded.{col}" for col in column_list)

        sql_statement = SqlStatement(
            f"INSERT INTO {SummitsTable.TABLE_NAME} ({column_names}) "
            f"VALUES ({value_placeholders}) ON CONFLICT DO UPDATE SET {column_updates} "
            f"WHERE {SummitsTable.COLUMN_LATITUDE}={UNDEFINED_GEOPOSITION.latitude_int} "
            f"AND {SummitsTable.COLUMN_LONGITUDE}={UNDEFINED_GEOPOSITION.longitude_int}"
        )

        self.__database_boundary.execute_write(
            query=sql_statement,
            query_parameters=[
                summit.name,
                summit.position.latitude_int,
                summit.position.longitude_int,
            ],
        )

    @override
    def add_or_enrich_route(self, summit_name: str, route: Route) -> None:
        select_summit = (
            f"SELECT {SummitsTable.COLUMN_ID} FROM {SummitsTable.TABLE_NAME} "
            f"WHERE {SummitsTable.COLUMN_SUMMIT_NAME}=? LIMIT 1"
        )

        column_list = [
            RoutesTable.COLUMN_SUMMIT_ID,
            RoutesTable.COLUMN_ROUTE_NAME,
            RoutesTable.COLUMN_ROUTE_GRADE,
            RoutesTable.COLUMN_GRADE_AF,
            RoutesTable.COLUMN_GRADE_RP,
            RoutesTable.COLUMN_GRADE_OU,
            RoutesTable.COLUMN_GRADE_JUMP,
            RoutesTable.COLUMN_STARS,
            RoutesTable.COLUMN_DANGER,
        ]
        column_names = ", ".join(column_list)
        value_placeholders = self._get_value_placeholders(len(column_list) - 1)
        insert_statement = SqlStatement(
            f"INSERT OR IGNORE INTO {RoutesTable.TABLE_NAME} ({column_names}) "
            f"VALUES (({select_summit}), {value_placeholders})"
        )
        self.__database_boundary.execute_write(
            query=insert_statement,
            query_parameters=[
                summit_name,
                route.route_name,
                route.grade,
                route.grade_af,
                route.grade_rp,
                route.grade_ou,
                route.grade_jump,
                route.star_count,
                route.dangerous,
            ],
        )

    @override
    def add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        select_summit = (
            f"SELECT {SummitsTable.COLUMN_ID} FROM {SummitsTable.TABLE_NAME} "
            f"WHERE {SummitsTable.COLUMN_SUMMIT_NAME}=? LIMIT 1"
        )
        select_route = (
            f"SELECT {RoutesTable.COLUMN_ID} FROM {RoutesTable.TABLE_NAME} "
            f"WHERE {RoutesTable.COLUMN_SUMMIT_ID}=({select_summit}) "
            f"AND {RoutesTable.COLUMN_ROUTE_NAME}=? "
            f"LIMIT 1"
        )

        column_list = [
            PostsTable.COLUMN_ROUTE_ID,
            PostsTable.COLUMN_USER_NAME,
            PostsTable.COLUMN_COMMENT,
            PostsTable.COLUMN_POST_DATE,
            PostsTable.COLUMN_RATING,
        ]
        column_names = ", ".join(column_list)
        value_placeholders = self._get_value_placeholders(len(column_list) - 1)

        insert_statement = SqlStatement(
            f"INSERT OR IGNORE INTO {PostsTable.TABLE_NAME} ({column_names}) "
            f"VALUES (({select_route}), {value_placeholders})"
        )

        self.__database_boundary.execute_write(
            query=insert_statement,
            query_parameters=[
                summit_name,
                route_name,
                post.user_name,
                post.comment,
                post.post_date.isoformat(),
                post.rating,
            ],
        )

    def _get_value_placeholders(self, value_count: int) -> str:
        return ", ".join(["?"] * value_count)
