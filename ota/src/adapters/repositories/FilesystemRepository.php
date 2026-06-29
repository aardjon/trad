<?php

/**
 * Adapter implementation for the DbDirectoryRepository.
 */

namespace trad\adapters\repositories;

use trad\core\boundaries\DbDirectoryRepository;
use trad\core\logging\Logger;
use \DirectoryIterator;
use \RuntimeException;

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

    #[\Override]
    public function replaceRouteDb(string $toReplaceUrl, string $replaceWithFilePath): void
    {
        $newFileBasename = basename($replaceWithFilePath);
        $newFilePath = "{$this->dbFilesDirectory}{$newFileBasename}";

        // New file must exist
        if (! file_exists($replaceWithFilePath)) {
            throw new RuntimeException("New file to replace with doesn't exist: {$replaceWithFilePath}");
        }

        // File to replace must exist
        if (! file_exists($toReplaceUrl)) {
            throw new RuntimeException("File to replace doesn't exist: {$toReplaceUrl}");
        }

        // File to add already exists
        if (file_exists($newFilePath)) {
            throw new RuntimeException("New file already exists in the repository: {$newFilePath}");
        }

        // Move the new file into the repository directory
        rename($replaceWithFilePath, $newFilePath);

        // Delete the old file that shall be replaced
        unlink($toReplaceUrl);
    }
}

?>
