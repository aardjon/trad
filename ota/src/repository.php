<?php

require_once('core.php');


final class DbDirectoryReader implements DbDirectoryRepository {
    
    private string $dbFilesDirectory;
    
    public function __construct(string $dbFilesDir) {
        $this->dbFilesDirectory = $dbFilesDir;
    }
    
    #[\Override]
    public function getRouteDbFiles() : array {
        $dbFiles = [];
        foreach (new DirectoryIterator($this->dbFilesDirectory) as $fileInfo) {
            if($fileInfo->isFile()) {
                $dbFiles[] ="{$this->dbFilesDirectory}/{$fileInfo->getFilename()}";
            }
        }
        return $dbFiles;
    }
}


 
final class TradRouteDbFileReader implements DbMetadataRepository {

    #[\Override]
    public function getRouteDbMetadata(string $routeDbFile) : RouteDbMetadata {
        $db = new PDO('sqlite:'.$routeDbFile);
        $cursor = $db->query('SELECT schema_version_major, schema_version_minor, compile_time FROM database_metadata LIMIT 1');
        if($cursor == false) {
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
