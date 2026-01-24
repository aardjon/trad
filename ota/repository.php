<?php

require_once('core.php');


class DbDirectoryReader implements DbDirectoryRepository {
    
    private string $dbFilesDirectory;
    
    public function __construct($dbFilesDir) {
        $this->dbFilesDirectory = $dbFilesDir;
    }
    
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


 
class TradRouteDbFileReader implements DbMetadataRepository {

    public function getRouteDbMetadata(string $routeDbFile) : RouteDbMetadata {
        $db = new PDO('sqlite:'.$routeDbFile);
        $cursor = $db->query('SELECT schema_version_major, schema_version_minor, compile_time FROM database_metadata LIMIT 1');
        $resultSet = $cursor->fetchAll();

        $metadataRow = $resultSet[0];
        
        $cursor = null;
        $db = null;

        return new RouteDbMetadata("$routeDbFile", $metadataRow[0], $metadataRow[1], $metadataRow[2]);
    }
}

?>
