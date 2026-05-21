<?php

/** Adapter implementation for the DbMetadataRepository. */
require_once (__DIR__.'/../../core/boundaries.php');
require_once (__DIR__.'/../../core/entities.php');

/**
 * Implementation reading data from a trad routedb of schema version 1.
 */
final class TradRouteDbFileReader implements DbMetadataRepository
{
    #[\Override]
    public function getRouteDbMetadata(string $routeDbFile): RouteDbMetadata
    {
        $db = new PDO('sqlite:'.$routeDbFile);
        $cursor = $db->query('SELECT schema_version_major, schema_version_minor, compile_time FROM database_metadata LIMIT 1');
        if ($cursor == false) {
            throw new RuntimeException('SQL query failed; maybe this is not a valid trad route database?');
        }
        /** @var array<int, mixed> $resultSet */
        $resultSet = $cursor->fetchAll();

        /** @var array<int, int | string> $metadataRow */
        $metadataRow = $resultSet[0];

        $cursor->closeCursor();
        unset($cursor);
        unset($db);

        return new RouteDbMetadata(
            "$routeDbFile",
            (int) $metadataRow[0],
            (int) $metadataRow[1],
            new DateTimeImmutable((string) $metadataRow[2]),
        );
    }
}

?>
