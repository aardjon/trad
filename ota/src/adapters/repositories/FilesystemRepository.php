<?php

/**
 * Adapter implementation for the DbDirectoryRepository.
 */

namespace trad\adapters\repositories;

use trad\core\boundaries\DbDirectoryRepository;
use \DirectoryIterator;

/**
 * Adapter implementation that finds route databases within a single file system directory.
 */
final class FilesystemRepository implements DbDirectoryRepository
{
    private string $dbFilesDirectory;

    public function __construct(string $dbFilesDir)
    {
        $this->dbFilesDirectory = $dbFilesDir;
    }

    #[\Override]
    public function getRouteDbFiles(): array
    {
        $dbFiles = [];
        foreach (new DirectoryIterator($this->dbFilesDirectory) as $fileInfo) {
            if ($fileInfo->isFile()) {
                $dbFiles[] = "{$this->dbFilesDirectory}/{$fileInfo->getFilename()}";
            }
        }

        return $dbFiles;
    }
}

?>
