<?php

namespace trad\adapters\repositories\github;

use \stdClass;
use \ValueError;

/**
 * The JSON response of a certain endpoint of the Github Workflow API. To be used by the
 * GithubBuildService only.
 *
 * An instance describes a single workflow run.
 */
final class GithubWorkflowRunJson
{
    /**
     * Name of the workflow.
     */
    public string $name;

    /**
     * Timestamp this run was last updated.
     */
    public string $updated_at;

    /**
     * URL for retrieving the assigend run artifacts.
     */
    public string $artifacts_url;

    /**
     * Construct a new instance from the raw data object returned by curl.
     */
    public function __construct(stdClass $jsonArray)
    {
        $this->name = $this->getString($jsonArray->name, 'name');
        $this->updated_at = $this->getString($jsonArray->updated_at, 'updated_at');
        $this->artifacts_url = $this->getString($jsonArray->artifacts_url, 'artifacts_url');
    }

    /**
     * Return the given [$value] as a string if it is one, or raise if it is not. The [$fieldname]
     * is only used for creating a helpful error message.
     */
    private function getString(mixed $value, string $fieldName): string
    {
        if (is_string($value)) {
            return $value;
        } else {
            throw new ValueError("JSON field '{$fieldName}' doesn't contain a string value");
        }
    }
}

?>
