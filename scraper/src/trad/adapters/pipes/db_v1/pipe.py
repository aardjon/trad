"""
Concrete pipe implementation writing a route database with schema version 1.
"""

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Final, override

from trad.adapters.boundaries.database import RelationalDatabaseBoundary
from trad.adapters.boundaries.database.query import DataRow, InsertQuery, SelectQuery
from trad.adapters.boundaries.database.structure import CreateIndexQuery, CreateTableQuery
from trad.adapters.pipes.db_v1.dbschema import (
    DbMetadataTable,
    PostsTable,
    RoutesTable,
    SummitsTable,
    TableSchema,
)
from trad.core.boundaries.pipes import Pipe
from trad.core.entities import Post, Route, Summit

if TYPE_CHECKING:
    from collections.abc import Sequence

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

        table_schemes: Sequence[type[TableSchema]] = (
            DbMetadataTable,
            SummitsTable,
            RoutesTable,
            PostsTable,
        )
        for table_class in table_schemes:
            table_definition = table_class()
            # Create the table
            self.__database_boundary.execute_create_table(
                CreateTableQuery(
                    table_name=table_definition.table_name(),
                    column_definition=table_definition.column_specification(),
                    primary_key=table_definition.primary_key(),
                    unique_constraints=table_definition.unique_constraints(),
                )
            )
            # Create all indices for this table
            for index in table_definition.indices():
                self.__database_boundary.execute_create_index(
                    CreateIndexQuery(
                        table_name=table_definition.table_name(),
                        index_definition=index,
                    )
                )

    @override
    def collect_statistics(self) -> None:
        self.__database_boundary.run_analyze()

    @override
    def shrink(self) -> None:
        self.__database_boundary.run_vacuum()

    @override
    def add_summit_data(self, summit: Summit) -> None:
        self.__database_boundary.execute_insert(
            InsertQuery(
                table_name=SummitsTable.TABLE_NAME,
                data_row=DataRow(
                    {
                        SummitsTable.COLUMN_NAME: summit.name,
                        SummitsTable.COLUMN_LATITUDE: 0,
                        SummitsTable.COLUMN_LONGITUDE: 0,
                    }
                ),
            )
        )

    @override
    def add_route_data(self, summit_name: str, route: Route) -> None:
        summit_query = SelectQuery(SummitsTable.TABLE_NAME, [SummitsTable.COLUMN_ID])
        summit_query.set_where_condition(f"{SummitsTable.COLUMN_NAME} = ?", [summit_name])
        summit_query.limit = 1
        self.__database_boundary.execute_insert(
            InsertQuery(
                table_name=RoutesTable.TABLE_NAME,
                data_row=DataRow(
                    {
                        RoutesTable.COLUMN_SUMMIT_ID: summit_query,
                        RoutesTable.COLUMN_NAME: route.route_name,
                        RoutesTable.COLUMN_GRADE: route.grade,
                        RoutesTable.COLUMN_GRADE_AF: route.grade_af,
                        RoutesTable.COLUMN_GRADE_RP: route.grade_rp,
                        RoutesTable.COLUMN_GRADE_OU: route.grade_ou,
                        RoutesTable.COLUMN_GRADE_JUMP: route.grade_jump,
                        RoutesTable.COLUMN_STARS: route.star_count,
                        RoutesTable.COLUMN_DANGER: route.dangerous,
                    }
                ),
            )
        )

    @override
    def add_post_data(self, summit_name: str, route_name: str, post: Post) -> None:
        summit_query = SelectQuery(SummitsTable.TABLE_NAME, [SummitsTable.COLUMN_ID])
        summit_query.set_where_condition(f"{SummitsTable.COLUMN_NAME} = ?", [summit_name])
        summit_query.limit = 1

        route_query = SelectQuery(RoutesTable.TABLE_NAME, [RoutesTable.COLUMN_ROUTE_ID])
        route_query.set_where_condition(
            f"{RoutesTable.COLUMN_SUMMIT_ID} = ? AND {RoutesTable.COLUMN_NAME} = ?",
            [summit_query, route_name],
        )
        route_query.limit = 1

        self.__database_boundary.execute_insert(
            InsertQuery(
                table_name=PostsTable.TABLE_NAME,
                data_row=DataRow(
                    {
                        PostsTable.COLUMN_ROUTE_ID: route_query,
                        PostsTable.COLUMN_USERNAME: post.user_name,
                        PostsTable.COLUMN_COMMENT: post.comment,
                        PostsTable.COLUMN_TIMESTAMP: post.post_date.isoformat(),
                        PostsTable.COLUMN_RATING: post.rating,
                    }
                ),
            )
        )
