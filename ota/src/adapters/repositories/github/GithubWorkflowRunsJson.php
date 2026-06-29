<?php

namespace trad\adapters\repositories\github;

use trad\adapters\repositories\github\GithubWorkflowRunJson;
use \stdClass;
use \ValueError;

/**
 * The JSON response of a certain endpoint of the Github Workflow API. To be used by the
 * GithubBuildService only.
 */
final class GithubWorkflowRunsJson
{
    /**
     * List of all workflow runs.
     *
     * @var array<GithubWorkflowRunJson> $workflow_runs
     */
    public array $workflow_runs;

    /**
     * Construct a new instance from the raw data object returned by curl.
     */
    public function __construct(stdClass $jsonArray)
    {
        $this->workflow_runs = [];
        /** @var stdClass $jsonData */
        foreach ($this->getArray($jsonArray->workflow_runs, 'workflow_runs') as $jsonData) {
            $this->workflow_runs[] = new GithubWorkflowRunJson($jsonData);
        }
    }

    /**
     * Return the given [$value] as an array if it is one, or raise if it is not. The [$fieldname]
     * is only used for creating a helpful error message.
     *
     * @return array<mixed, mixed>
     */
    private function getArray(mixed $value, string $fieldName): array
    {
        if (is_array($value)) {
            return $value;
        } else {
            throw new ValueError("JSON field '{$fieldName}' doesn't contain an array");
        }
    }
}

?>
