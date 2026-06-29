<?php

require_once (__DIR__.'/../../../vendor/autoload.php');

use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use trad\adapters\repositories\FilesystemRepository;
use trad\infrastructure\monolog\handlers\BlackHoleLoggingHandler;
use trad\infrastructure\monolog\loggers\MonologLoggerFactory;

/**
 * Unit tests for the FilesystemRepository class.
 */
final class FilesystemRepositoryTest extends TestCase
{
    /**
     * Path to the temporary route DB repository data directory.
     * This corresponds to the $CONFIG_DATABASE_FILES_DIRECTORY settings variable.
     */
    private string $testTempDir;

    /**
     * Path to a temporary directory that is not used as route DB repository.
     */
    private string $testTempDirOther;

    private LoggerInterface $loggerMock;

    private FilesystemRepository $repository;

    protected function setUp(): void
    {
        parent::setUp();
        MonologLoggerFactory::setupLogging(new BlackHoleLoggingHandler());
        $this->loggerMock = $this->createMock(LoggerInterface::class);

        $tempDir = $this->getTempDir();
        $this->testTempDir = $tempDir.'repository_files'.DIRECTORY_SEPARATOR;
        $this->testTempDirOther = $tempDir.'other_files'.DIRECTORY_SEPARATOR;
        if (! mkdir($this->testTempDir, 0777, true)) {
            $this->fail("Unable to create temporary directory: {$this->testTempDir}");
        }
        if (! mkdir($this->testTempDirOther, 0777, true)) {
            $this->fail("Unable to create temporary directory: {$this->testTempDirOther}");
        }
        $this->repository = new FilesystemRepository($this->testTempDir);
    }

    private function getTempDir(): string
    {
        $uniqueName = uniqid('db_reader_test_', true);

        return sys_get_temp_dir().DIRECTORY_SEPARATOR.$uniqueName.DIRECTORY_SEPARATOR;
        // return '/home/thomas/tmp/trad.ota'.DIRECTORY_SEPARATOR.$uniqueName.DIRECTORY_SEPARATOR;
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        $tempBaseDir = dirname($this->testTempDir);
        if (is_dir($tempBaseDir)) {
            $this->deleteRecursively($tempBaseDir);
        }
        MonologLoggerFactory::shutdownLogging();
    }

    /**
     * Recursively deletes the given directory and all of its contents.
     */
    private function deleteRecursively(string $dir): void
    {
        $it = new RecursiveDirectoryIterator($dir, RecursiveDirectoryIterator::SKIP_DOTS);
        $files = new RecursiveIteratorIterator($it, RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($files as $file) {
            if ($file->isDir()) {
                rmdir($file->getPathname());
            } else {
                unlink($file->getPathname());
            }
        }
        rmdir($dir);
    }

    /**
     * Make sure that only sqlite database files are returned from getRouteDbFiles. Directories and
     * other files are ignored.
     */
    public function testGetRouteDbFilesReturnsOnlyRouteDbFiles(): void
    {
        // Create test data (files and directory)
        touch($this->testTempDir.'test1.sqlite');
        touch($this->testTempDir.'test2.sqlite');
        touch($this->testTempDir.'test3.txt');
        touch($this->testTempDir.'test4.md');
        mkdir($this->testTempDir.'subdir');

        $result = $this->repository->getRouteDbFiles();

        $this->assertCount(2, $result);
        $this->assertContains($this->testTempDir.'test1.sqlite', $result);
        $this->assertContains($this->testTempDir.'test2.sqlite', $result);
    }

    /**
     * Make sure that getRouteDbFiles() returns an empty array when there are no files at all.
     */
    public function testGetRouteDbFilesReturnsEmptyArrayWhenNoFilesExist(): void
    {
        $result = $this->repository->getRouteDbFiles();
        $this->assertEmpty($result);
    }

    /**
     * Ensure that getRouteDbFiles() ignores files from sub directories.
     */
    public function testGetRouteDbFilesHandlesDirectorySubDirectories(): void
    {
        mkdir($this->testTempDir.'subdir1');
        mkdir($this->testTempDir.'subdir2');
        touch($this->testTempDir.'subdir2'.DIRECTORY_SEPARATOR.'test1.sqlite');

        $result = $this->repository->getRouteDbFiles();
        $this->assertEmpty($result);
    }

    /**
     * Make sure that getRouteDbFiles() does return dot files.
     */
    public function testGetRouteDbFilesHandlesDotFiles(): void
    {
        touch($this->testTempDir.'.hidden.sqlite');
        touch($this->testTempDir.'visible.sqlite');

        $result = $this->repository->getRouteDbFiles();

        $this->assertCount(2, $result);
        $this->assertContains($this->testTempDir.'.hidden.sqlite', $result);
        $this->assertContains($this->testTempDir.'visible.sqlite', $result);
    }

    /**
     * Make sure that getRouteDbFiles() can handle files with multiple dots in their name.
     */
    public function testGetRouteDbFilesHandlesFilesWithMultipleDots(): void
    {
        touch($this->testTempDir.'test.file.sqlite');
        touch($this->testTempDir.'.test.sqlite');
        touch($this->testTempDir.'test.sqlite');

        $result = $this->repository->getRouteDbFiles();

        $this->assertCount(3, $result);
        $this->assertContains($this->testTempDir.'test.file.sqlite', $result);
        $this->assertContains($this->testTempDir.'.test.sqlite', $result);
        $this->assertContains($this->testTempDir.'test.sqlite', $result);
    }

    /**
     * Ensure error behaviour of getRouteDbFiles(): Throw an exception if the requested directory
     * does not exist.
     */
    public function testGetRouteDbFilesThrowsExceptionForInvalidDirectory(): void
    {
        $invalidDir = $this->testTempDir.'invalid';
        $this->expectException(\RuntimeException::class);

        // Delete the temporary directory to cause an error
        rmdir($this->testTempDir);
        $this->repository = new FilesystemRepository($invalidDir);
        $this->repository->getRouteDbFiles();
    }

    /**
     * Ensure that replacing an existing file with a new one works.
     */
    public function testReplaceRouteDbSuccessfullyReplacesFile(): void
    {
        $oldFilePath = "{$this->testTempDir}old_routedb.sqlite";
        $newFilePath = "{$this->testTempDirOther}new_routedb.sqlite";
        touch($oldFilePath);
        touch($newFilePath);

        $this->repository->replaceRouteDb($oldFilePath, $newFilePath);

        // Make sure the new file is in the repository, the old one isn't.
        $routeDbFiles = $this->repository->getRouteDbFiles();
        $this->assertCount(1, $routeDbFiles);
        $this->assertStringContainsString(basename($newFilePath), $routeDbFiles[0]);

        $this->assertFileDoesNotExist($oldFilePath);
        $this->assertFileDoesNotExist($newFilePath);
        $this->assertFileExists($this->testTempDir.basename($newFilePath));
    }

    /**
     * Ensure that replacing an existing file doesn't touch any other files.
     */
    public function testReplaceRouteDbDoesntChangeOtherFiles(): void
    {
        $oldFilePath1 = "{$this->testTempDir}old1.sqlite";
        $oldFilePath2 = "{$this->testTempDir}old2.sqlite";
        $newFilePath1 = "{$this->testTempDirOther}new1.sqlite";
        $newFilePath2 = "{$this->testTempDirOther}new2.sqlite";

        touch($oldFilePath1);
        touch($oldFilePath2);
        touch($newFilePath1);
        touch($newFilePath2);

        $this->repository->replaceRouteDb($oldFilePath1, $newFilePath1);

        // Make sure that all the second files are still in place.
        $routeDbFiles = $this->repository->getRouteDbFiles();
        $this->assertCount(2, $routeDbFiles);
        $this->assertContains($this->testTempDir.basename($newFilePath1), $routeDbFiles);
        $this->assertContains($this->testTempDir.basename($oldFilePath2), $routeDbFiles);

        $this->assertFileDoesNotExist($oldFilePath1);
        $this->assertFileDoesNotExist($newFilePath1);
        $this->assertFileExists($oldFilePath2);
        $this->assertFileExists($newFilePath2);
    }

    /**
     * Ensure that replaceRouteDb() throws if the file to replace doesn't exist.
     */
    public function testReplaceRouteDbThrowsIfFileToReplaceDoesNotExist(): void
    {
        $existingRepoFilePath = "{$this->testTempDir}old_routedb.sqlite";
        $newFilePath = "{$this->testTempDirOther}new_routedb.sqlite";
        $nonExistentOldFilePath = "{$this->testTempDir}non_existent.sqlite";

        touch($existingRepoFilePath);
        touch($newFilePath);

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("File to replace doesn't exist: $nonExistentOldFilePath");

        $this->repository->replaceRouteDb($nonExistentOldFilePath, $newFilePath);
    }

    /**
     * Ensure that replaceRouteDb() throws if the given new file does not exist.
     */
    public function testReplaceRouteDbThrowsIfNewFileDoesNotExist(): void
    {
        $oldFilePath = "{$this->testTempDir}old_routedb.sqlite";
        $nonExistentNewFile = "{$this->testTempDirOther}new_routedb.sqlite";
        touch($oldFilePath);

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage(
            "New file to replace with doesn't exist: {$nonExistentNewFile}"
        );

        $this->repository->replaceRouteDb($oldFilePath, $nonExistentNewFile);
    }

    /**
     * Ensure that replaceRouteDb() throws if the destination file already exists.
     */
    public function testReplaceRouteDbThrowsIfDestinationAlreadyExists(): void
    {
        $oldFilePath1 = "{$this->testTempDir}old_routedb.sqlite";
        $oldFilePath2 = "{$this->testTempDir}dest_routedb.sqlite";
        $newFilePath = "{$this->testTempDirOther}dest_routedb.sqlite";
        touch($oldFilePath1);
        touch($oldFilePath2);
        touch($newFilePath);

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage(
            "New file already exists in the repository: {$oldFilePath2}"
        );

        $this->repository->replaceRouteDb($oldFilePath1, $newFilePath);
    }
}

?>
