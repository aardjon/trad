<?php

namespace trad\adapters\repositories\github;

use trad\adapters\boundaries\NetworkAdapter;
use trad\adapters\repositories\github\GithubArtifactJson;
use trad\adapters\repositories\github\GithubArtifactsJson;
use trad\adapters\repositories\github\GithubWorkflowRunJson;
use trad\adapters\repositories\github\GithubWorkflowRunsJson;
use trad\core\boundaries\DbBuildService;
use trad\core\entities\ArtifactMetadata;
use trad\core\entities\DbArtifact;
use trad\core\logging\Logger;
use \DateTimeImmutable;
use \Exception;
use \RuntimeException;
use \ZipArchive;

/**
 * Build service implementation that retrieves routdb artifacts from Github.
 */
final class GithubBuildService implements DbBuildService
{
    private Logger $logger;
    private NetworkAdapter $networkAdapter;
    private string $githubRepoOwner;
    private string $githubRepoName;
    /** @var array<int, string> $authHeader */
    private array $authHeader;
    private string $githubApiBaseUrl = 'https://api.github.com';
    private string $dbCreationWorkflowName = 'routedb-creation';
    private string $routeDbArtifactName = 'routedb';

    public function __construct(
        NetworkAdapter $networkAdapter,
        string $githubRepoOwner,
        string $githubRepoName,
        string $githubApiToken,
    ) {
        $this->logger = Logger::get('trad.adapters.repositories.github');
        $this->networkAdapter = $networkAdapter;
        $this->githubRepoOwner = $githubRepoOwner;
        $this->githubRepoName = $githubRepoName;
        $this->authHeader = ["Authorization: Bearer {$githubApiToken}"];
    }

    #[\Override]
    public function getNewerArtifactsMetadata(DateTimeImmutable $startDate): array
    {
        // Retrieve all workflow runs
        $latestRuns = $this->getNewWorkflowRuns($this->dbCreationWorkflowName, $startDate);
        if (count($latestRuns) == 0) {
            return [];
        }

        $artifactsMetadata = [];
        foreach ($latestRuns as $run) {
            $routeDbArtifact = $this->getArtifactMetadata(
                $run,
                $this->routeDbArtifactName,
                $startDate,
            );
            if ($routeDbArtifact === null) {
                continue;
            }

            $artifactsMetadata[] = new ArtifactMetadata(
                $routeDbArtifact->archive_download_url,
                new DateTimeImmutable($routeDbArtifact->created_at),
            );
        }

        return $artifactsMetadata;
    }

    /**
     * Return the latest workflow run that created a route database.
     *
     * @return Array<GithubWorkflowRunJson>
     */
    private function getNewWorkflowRuns(string $workflowName, DateTimeImmutable $startDate): array
    {
        $url = "{$this->githubApiBaseUrl}/repos/{$this->githubRepoOwner}/{$this->githubRepoName}/actions/runs";
        $urlParams = array(
            'status' => 'success',
            'branch' => 'main',
        );
        $jsonRuns = new GithubWorkflowRunsJson(
            $this->networkAdapter->getJsonPayload($url, $urlParams, $this->authHeader)
        );

        // Find all matching workflow runs
        $newRuns = [];
        foreach ($jsonRuns->workflow_runs as $workflow) {
            if (
                $workflow->name == $workflowName &&
                $startDate < new DateTimeImmutable($workflow->updated_at)
            ) {
                $newRuns[] = $workflow;
            }
        }

        return $newRuns;
    }

    /**
     * Return metadata of the artifact named [$artifactName] from the given workflow run, if it is
     * newer than [$startDate]. Return null if the run doesn't contain a matching artifact.
     */
    private function getArtifactMetadata(
        GithubWorkflowRunJson $workflowRun,
        string $artifactName,
        DateTimeImmutable $startDate,
    ): ?GithubArtifactJson {
        $jsonArtifacts = new GithubArtifactsJson($this->networkAdapter->getJsonPayload(
            $workflowRun->artifacts_url,
            array(),
            $this->authHeader,
        ));

        // Find the routedb artifact
        $routeDbArtifact = null;
        foreach ($jsonArtifacts->artifacts as $artifact) {
            if (
                $artifact->name == $artifactName &&
                $artifact->expired == false &&
                new DateTimeImmutable($artifact->created_at) > $startDate
            ) {
                $routeDbArtifact = $artifact;
                break;
            }
        }
        if ($routeDbArtifact === null) {
            // Not a real problem, the artifact may just have expired
            $this->logger->debug(
                'A matching workflow does not contain a routedb artifact (anymore?).'
            );
        }

        return $routeDbArtifact;
    }

    #[\Override]
    public function getArtifactContent(string $artifactIdentifer): DbArtifact
    {
        $destinationDir = sys_get_temp_dir();
        $archiveFile = $this->downloadArtifactZip($artifactIdentifer, $destinationDir);
        $routeDbFile = $this->extractRouteDbFile($archiveFile, $destinationDir);
        unlink($archiveFile);

        return new DbArtifact($routeDbFile);
    }

    /**
     * Download the artifact ZIP file identified by [$artifactIdentifer], and write it into a new
     * file within the [$destinationDir] directory. In case of any error an exception is raised and
     * the file is deleted (or not created at all, depending on the error).
     *
     * Returns the path to the newly created ZIP file.
     */
    private function downloadArtifactZip(string $artifactIdentifer, string $destinationDir): string
    {
        $tempFilePath = tempnam($destinationDir, 'trad.ota-');
        if ($tempFilePath === false) {
            throw new RuntimeException('Unable to create temporary file');
        }

        try {
            $artifactFileContent = $this->networkAdapter->getBinaryPayload(
                $artifactIdentifer,
                array_merge($this->authHeader, array('Accept: application/vnd.github+json')),
            );

            $bytesWritten = file_put_contents($tempFilePath, $artifactFileContent);
            if ($bytesWritten === false) {
                $this->logger->fatal("Unable to write artifact file {$tempFilePath}");
                throw new RuntimeException("Unable to write artifact file {$tempFilePath}");
            }
        } catch (Exception $e) {
            unlink($tempFilePath);
            throw $e;
        }

        $this->logger->info("Successfully wrote artifact into file {$tempFilePath}");

        return $tempFilePath;
    }

    /**
     * Extract the routedb file from the given [$zipArchiveFile] into the [$destinationDir]
     * directory. Throws in case of any errors.
     */
    private function extractRouteDbFile(string $zipArchiveFile, string $destinationDir): string
    {
        $zip = new ZipArchive;
        if ($zip->open($zipArchiveFile, ZipArchive::RDONLY | ZipArchive::CHECKCONS) !== true) {
            throw new RuntimeException("Unable to open archive file {$zipArchiveFile}");
        }
        $entryCount = $zip->count();
        $this->logger->debug("Artifact ZIP {$zipArchiveFile} contains {$entryCount} files");

        $routeDbFileName = '';
        for ($idx = 0; $idx < $entryCount; $idx++) {
            $zipEntry = $zip->statIndex($idx);
            if ($zipEntry === false) {
                throw new RuntimeException("Unable to extract metadata of ZIP entry {$idx}");
            }
            $routeDbFileName = (string) $zipEntry['name'];
            if (
                str_starts_with($routeDbFileName, 'routedb_') &&
                array_last(explode('.', $routeDbFileName)) == 'sqlite'
            ) {
                break;
            }
        }

        $this->logger->debug("Extracting routedb file: {$routeDbFileName}");
        $content = $zip->getFromName($routeDbFileName);
        $zip->close();

        $destinationFile = "{$destinationDir}/{$routeDbFileName}";
        file_put_contents($destinationFile, $content);

        $this->logger->info("Successfully extracted routedb into {$destinationFile}");

        return $destinationFile;
    }
}

?>
