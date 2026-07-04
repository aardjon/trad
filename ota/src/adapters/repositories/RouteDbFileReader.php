<?php

/**
 * Adapter implementation for the DbMetadataRepository.
 */

namespace trad\adapters\repositories;

use trad\core\boundaries\DbMetadataRepository;
use trad\core\entities\RouteDbMetadata;
use \DateTimeImmutable;
use \PDO;
use \RuntimeException;

/**
 * Implementation reading data from a trad routedb of schema version 1.
 */
final class RouteDbFileReader implements DbMetadataRepository
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
