<?php

require_once (__DIR__.'/../../../vendor/autoload.php');

use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use trad\adapters\repositories\FilesystemRepository;

/**
 * Unit tests for the FilesystemRepository class.
 */
final class FilesystemRepositoryTest extends TestCase
{
    private string $testTempDir;
    private LoggerInterface $loggerMock;
    private FilesystemRepository $repository;

    protected function setUp(): void
    {
        parent::setUp();

        // Mock für den Logger erstellen
        // $this->loggerMock = $this->createMock(LoggerInterface::class);

        $this->testTempDir = $this->getTempDir();
        if (! mkdir($this->testTempDir, 0777, true)) {
            $this->fail("Unable to create temporary directory: {$this->testTempDir}");
        }
        $this->repository = new FilesystemRepository($this->testTempDir);
    }

    private function getTempDir(): string
    {
        $uniqueName = uniqid('db_reader_test_', true);

        return sys_get_temp_dir().DIRECTORY_SEPARATOR.$uniqueName.DIRECTORY_SEPARATOR;
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        if (is_dir($this->testTempDir)) {
            $this->deleteRecursively($this->testTempDir);
        }
    }

    /**
     * Recursively deletes the given directory an all of its contents.
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
     * Make sure that only files are returned from getRouteDbFiles. Directories must be ignored.
     */
    public function testGetRouteDbFilesReturnsOnlyFiles(): void
    {
        // Create test data (files and directory)
        touch($this->testTempDir.'test1.sqlite');
        touch($this->testTempDir.'test2.sqlite');
        touch($this->testTempDir.'test3.txt');
        touch($this->testTempDir.'test4.md');
        mkdir($this->testTempDir.'subdir');

        $result = $this->repository->getRouteDbFiles();

        $this->assertCount(4, $result);
        $this->assertContains($this->testTempDir.'test1.sqlite', $result);
        $this->assertContains($this->testTempDir.'test2.sqlite', $result);
        $this->assertContains($this->testTempDir.'test3.txt', $result);
        $this->assertContains($this->testTempDir.'test4.md', $result);
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
        // Nur Unterverzeichnisse erstellen
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
        touch($this->testTempDir.'test.sqlite.backup');
        touch($this->testTempDir.'test.sqlite');

        $result = $this->repository->getRouteDbFiles();

        $this->assertCount(3, $result);
        $this->assertContains($this->testTempDir.'test.file.sqlite', $result);
        $this->assertContains($this->testTempDir.'test.sqlite', $result);
        $this->assertContains($this->testTempDir.'test.sqlite.backup', $result);
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
}

?>
