# Commit Guideline

## Commit Messages

These guidelines help to ensure consistent and understandable commit messages, making the project easier to maintain.

### General Rules

- Use the imperative form in the present tense.
- Add an empty line between the summary and the description.

### Structure of a Commit Message

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

### Recommended Prefixes for Commit Messages

- **feat:** Commits, that adds or remove a new feature
- **fix:** Commits, that fixes a bug
- **cha:** Commits, that introduces a breaking change
- **docs:** Commits, that affect documentation only
- **style:** Commits, that do not affect the meaning (white-space, formatting, missing semi-colons, etc)
- **refactor:** Commits, that rewrite/restructure your code, however does not change any API behaviour
- **test:** Commits, that add missing tests or correcting existing tests
- **chore:** Miscellaneous commits e.g. modifying .gitignore
- **ci:** Commits, that affect CI configuration
- **clean:** Commits, that removes unnecessary code or files
- **merge:** Commits that explicitly merge a branch into another

### Examples

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
- `merge: Merge branch 'new_fancy_feature' into 'main'`


## Best Practices

- Commits should be small and focused.
- Avoid unclear commit messages like `fix bug` or `update`.
- The `main` branch shall always be sane, i.e. the CI pipeline shall succeed for all commits.
- Use branches for developing new features or bug fixes.
- Do not *fast forward* merge branches with more than a single commit (create a dedicated merge commit instead).

## Source Reports

The CI generates and publishes some reports on the source code, which may be interesting to look at
during development:

- Detailed code coverage of the last successful test run on the `main` branch:
  - Mobile App: https://www.fomori.de/trad/reports/main/mobileapp
  - Scraper: https://www.fomori.de/trad/reports/main/scraper

Please note that reports are published for the `main` branch only, but the ones for your feature
branch are still kept as artifacts for a while so you can download them from the corresponding
[Github Workflow Run](https://github.com/Headbucket/trad/actions). Alternatively, it's also possible
to create them locally using some melos script, please refer to [Development tools and CI](devtools.md)
for further information.
