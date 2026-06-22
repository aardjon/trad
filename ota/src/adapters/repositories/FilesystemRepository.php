<?php

/**
 * Adapter implementation for the DbDirectoryRepository.
 */

namespace trad\adapters\repositories;

use trad\core\boundaries\DbDirectoryRepository;
use trad\core\logging\Logger;
use \DirectoryIterator;

/**
 * Adapter implementation that finds route databases within a single file system directory.
 */
final class FilesystemRepository implements DbDirectoryRepository
{
    private Logger $logger;
    private string $dbFilesDirectory;

    public function __construct(string $dbFilesDir)
    {
        $this->logger = Logger::get('trad.adapters.repositories.filesystem');
        $this->dbFilesDirectory = $dbFilesDir;
        if (! str_ends_with($this->dbFilesDirectory, DIRECTORY_SEPARATOR)) {
            $this->dbFilesDirectory = $this->dbFilesDirectory.DIRECTORY_SEPARATOR;
        }
    }

    #[\Override]
    public function getRouteDbFiles(): array
    {
        $this->logger->info('getRouteDbFiles() called');
        $dbFiles = [];
        foreach (new DirectoryIterator($this->dbFilesDirectory) as $fileInfo) {
            if ($fileInfo->isFile() && str_ends_with($fileInfo->getFilename(), '.sqlite')) {
                $dbFiles[] = "{$this->dbFilesDirectory}{$fileInfo->getFilename()}";
            }
        }

        return $dbFiles;
    }
}

?>
