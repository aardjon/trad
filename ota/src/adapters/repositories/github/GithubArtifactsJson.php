<?php

namespace trad\adapters\repositories\github;

use trad\adapters\repositories\github\GithubArtifactJson;
use \stdClass;
use \ValueError;

/**
 * The JSON response of a certain endpoint of the Github Artifact API. To be used by the
 * GithubBuildService only.
 */
final class GithubArtifactsJson
{
    /**
     * List fo all artifacts (of a certain run).
     *
     * @var array<GithubArtifactJson> $artifacts
     */
    public array $artifacts;

    /**
     * Construct a new instance from the raw data object returned by curl.
     */
    public function __construct(stdClass $jsonArray)
    {
        $this->artifacts = [];
        /** @var stdClass $jsonData */
        foreach ($this->getArray($jsonArray->artifacts, 'artifacts') as $jsonData) {
            $this->artifacts[] = new GithubArtifactJson($jsonData);
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
