<?php

namespace trad\adapters\repositories\github;

use \stdClass;
use \ValueError;

/**
 * The JSON response of a certain endpoint of the Github Artifact API. To be used by the
 * GithubBuildService only.
 *
 * An instance describes a single run artifact. A single run artifact may contain several files.
 */
final class GithubArtifactJson
{
    /**
     * Name of the artifact.
     */
    public string $name;

    /**
     * Creation time of the artifact.
     */
    public string $created_at;

    /**
     * True if the artifact is already expired, false if not.
     */
    public bool $expired;

    /**
     * URL for downloading the zipped artifact files.
     */
    public string $archive_download_url;

    /**
     * Construct a new instance from the raw data object returned by curl.
     */
    public function __construct(stdClass $jsonArray)
    {
        $this->name = $this->getString($jsonArray->name, 'name');
        $this->created_at = $this->getString($jsonArray->created_at, 'created_at');
        $this->expired = $this->getBool($jsonArray->expired, 'expired');
        $this->archive_download_url = $this->getString(
            $jsonArray->archive_download_url,
            'archive_download_url',
        );
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

    /**
     * Return the given [$value] as a boolen if it is one, or raise if it is not. The [$fieldname]
     * is only used for creating a helpful error message.
     */
    private function getBool(mixed $value, string $fieldName): bool
    {
        if (is_bool($value)) {
            return $value;
        } else {
            throw new ValueError("JSON field '{$fieldName}' doesn't contain a boolean value");
        }
    }
}

?>
