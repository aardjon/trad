# Commit Message Guidelines

These guidelines help ensure consistent and understandable commit messages, making the project easier to maintain.

## General Rules

- Use the imperative form in the present tense.
- Add an empty line between the summary and the description.

## Structure of a Commit Message

1. **Summary**
    - Briefly and concisely describe what the change does.
    - Example: `fix typo in the user guide`
2. **Description** (optional)
    - Explain why this change was made and how it was implemented.
    - Example:
      ```
      The typo in the user guide section 4.2 could cause confusion among users.
      This commit fixes that typo to improve clarity.
      ```

## Recommended Prefixes for Commit Messages

- **feat:** Commits, that adds or remove a new feature
- **fix:** Commits, that fixes a bug
- **cha:** Commits, that introduces a breaking change
- **docs:** Commits, that affect documentation only
- **style:** Commits, that do not affect the meaning (white-space, formatting, missing semi-colons, etc)
- **refactor:** Commits, that rewrite/restructure your code, however does not change any API behaviour
- **test:** Commits, that add missing tests or correcting existing tests
- **chore:** Miscellaneous commits e.g. modifying .gitignore
- **ci:** Commits, that affect CI configuration
- **clean**: Commits, that removes unnecessary code or files

## Examples

- `feat: add user login functionality`
- `fix: resolve issue with user profile update`
- `cha: change logging from stdout to console`
- `docs: update README with installation instructions`
- `style: format code according to style guide`
- `refactor: reorganize project structure for better modularity`
- `test: add unit tests for authentication service`
- `chore: update dependencies`
- `ci: update CI configuration for new environment`
- `clean: remove unused imports and variables`

## Best Practices

- Commits should be small and focused.
- Use branches for developing new features or bug fixes.
- Avoid unclear commit messages like `fix bug` or `update`.