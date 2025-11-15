"""
Concrete pipe implementation writing a route database with schema version 1.
"""

import datetime
from logging import getLogger
from pathlib import Path
from typing import Final, override

from trad.application.boundaries.database import RelationalDatabaseBoundary, SqlStatement
from trad.application.filters._base import SinkFilter
from trad.application.filters.sink.db_v1.dbschema import (
    DatabaseMetadataTable,
    DatabaseSchema,
    NameUsage,
    PostsTable,
    RoutesTable,
    SummitNamesTable,
    SummitsTable,
)
from trad.kernel.appmeta import APPLICATION_NAME, APPLICATION_VERSION
from trad.kernel.boundaries.filters import FilterStage
from trad.kernel.boundaries.pipes import Pipe
from trad.kernel.entities import UNDEFINED_GEOPOSITION, Post, Route, Summit

_logger = getLogger(__name__)


class DbSchemaV1Filter(SinkFilter):
    """
    Filter implementation for creating a route database file (schema version 1) that can be used
    with the trad mobile app.

    This class encapsulates all knowledge about the structure of the route database in this
    particular schema version.
    """

    _DB_FILE_NAME: Final = "routedb_v1.sqlite"
    """ File name to use for the destination database file. """

    def __init__(self, output_directory: Path, database_boundary: RelationalDatabaseBoundary):
        """
        Create a new filter that writes all data from the input pipe into a new route DB file within
        the given [output_directory], using the provided [database_boundary].
        """
        super().__init__()
        self.__destination_file = output_directory.joinpath(self._DB_FILE_NAME)
        self.__database_boundary = database_boundary

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.FINALIZATION

    @override
    def get_name(self) -> str:
        return "WriteDbSchemaV1"

    @override
    def _execute_sink_filter(
        self,
        input_pipe: Pipe,
    ) -> None:
        _logger.debug("Executing filter for writing into %s", self.__destination_file)
        self.__database_boundary.connect(self.__destination_file, overwrite=True)
        self._initialize_database()

        for summit_id, summit in input_pipe.iter_summits():
            self._add_summit(summit)
            for route_id, route in input_pipe.iter_routes_of_summit(summit_id):
                self._add_route(summit.name, route)
                for post in input_pipe.iter_posts_of_route(route_id):
                    self._add_post(summit.name, route.route_name, post)

        self._finalize_database()
        self.__database_boundary.disconnect()

    def _initialize_database(self) -> None:
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

    def _finalize_database(self) -> None:
        _logger.debug("Finalizing routedb pipe")
        self.__database_boundary.execute_write(SqlStatement("ANALYZE"))
        self.__database_boundary.execute_write(SqlStatement("VACUUM"))

    def _add_summit(self, summit: Summit) -> None:
        summit_id = self._write_to_summits_table(summit)
        self._write_to_summit_names_table(summit_id, summit)

    def _write_to_summits_table(self, summit: Summit) -> int:
        """Add the given Summit to the `summits` table and return the ID of the new record."""
        column_list = [
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
                summit.high_grade_position.latitude_int,
                summit.high_grade_position.longitude_int,
            ],
        )
        row_ids = self.__database_boundary.execute_read(
            SqlStatement("SELECT last_insert_rowid() as rowid")
        )
        return row_ids[0].get_int_value("rowid")

    def _write_to_summit_names_table(self, summit_id: int, summit: Summit) -> None:
        column_list = [
            SummitNamesTable.COLUMN_SUMMIT_ID,
            SummitNamesTable.COLUMN_NAME,
            SummitNamesTable.COLUMN_USAGE,
        ]
        column_names = ", ".join(column_list)
        value_placeholders = self._get_value_placeholders(len(column_list))

        sql_statement = SqlStatement(
            f"INSERT INTO {SummitNamesTable.TABLE_NAME} ({column_names}) "
            f"VALUES ({value_placeholders})"
        )

        if summit.official_name:
            self.__database_boundary.execute_write(
                query=sql_statement,
                query_parameters=[
                    summit_id,
                    summit.official_name,
                    NameUsage.official,
                ],
            )
            for alternate_name in summit.alternate_names:
                self.__database_boundary.execute_write(
                    query=sql_statement,
                    query_parameters=[
                        summit_id,
                        alternate_name,
                        NameUsage.alternate,
                    ],
                )
        else:
            # Some summits don't have an official name. Possible reasons (besides bugs):
            #    - "Massive" are not (yet) retrieved from OSM (https://github.com/Headbucket/trad/issues/12)
            #    - New entries on some external sites
            # As a workaround, we just handle this here. Should better be done by a separate
            # VALIDATION filter, though, to make sure writte data is always complete.
            # TODO(aardjon): Provide a proper implementation for this case
            _logger.warning("Found Summit without official name: %s", summit.name)
            self.__database_boundary.execute_write(
                query=sql_statement,
                query_parameters=[
                    summit_id,
                    summit.name,
                    NameUsage.official,
                ],
            )

    def _add_route(self, summit_name: str, route: Route) -> None:
        select_summit = (
            f"SELECT {SummitNamesTable.COLUMN_SUMMIT_ID} FROM {SummitNamesTable.TABLE_NAME} "
            f"WHERE {SummitNamesTable.COLUMN_NAME}=? AND {SummitNamesTable.COLUMN_USAGE}=0 LIMIT 1"
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

    def _add_post(self, summit_name: str, route_name: str, post: Post) -> None:
        select_summit = (
            f"SELECT {SummitNamesTable.COLUMN_SUMMIT_ID} FROM {SummitNamesTable.TABLE_NAME} "
            f"WHERE {SummitNamesTable.COLUMN_NAME}=? AND {SummitNamesTable.COLUMN_USAGE}=0 LIMIT 1"
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
