Development tools and CI
========================

Because the `trad` system is split into two applications witten in different languages, we also have
to use different sets of development tools for them. We try to keep their usages as similar as
possible, e.g. by using the same names for scripts/tasks that are essentially doing the same but in
different environments.

- For developing the mobile application (Dart), we use [Melos](https://melos.invertase.dev/).
- For developing the scraper application (Python), we use [Invoke](https://www.pyinvoke.org/).

We use those tools to provides several scripts for common tasks that can be used in local
development as well as from CI workflows. This helps to use the same configuration in both
environments.


# Melos (Mobile App Development)

Because the mobile application (`mobileapp` directory) is split into multiple sub projects, using
the `Dart`/`Flutter` framework tools directly or in a CI task can be tedious. That's why we use
[Melos](https://melos.invertase.dev/) (a CLI tool for managing multiple `Dart` projects within a
mono-repo) to simplify and unify things.

## Using Melos

All Melos commands have to be executed from the `mobileapp` directory (which is the mobile
application project root). The following sections shortly describe the most important commands,
please refer to the [Melos documentation](https://melos.invertase.dev/getting-started) for more
detailed information. There is one important thing to know, though: **Please do not use the default
`melos format` command** because it doesn't respect our formatter configuration. **Use the `melos
run format` script instead.**

You may also want to have a look at [IDE Support](https://melos.invertase.dev/ide-support) for how
to integrate Melos into your favourite IDE.

All available scripts are defined in the [Melos configuration file](../mobileapp/melos.yaml).

## Setup a working copy

```
melos bootstrap
```

Installs all necessary (`Dart`) packages for the mobile app into the local `Flutter` environment
(respecting the version constraints from all sub projects and their dependencies), resulting in the
environment being used for building and running the app. Needs to be done once after initial
checkout and again every time any of the `pubspec.yaml` or `pubspec.lock` files changes.

## Run a single command in all (or some) sub projects

```
melos exec [filter options] [shell command]
```

Executes the given `shell command` in all sub projects ("rings") matching the given `filter
options`. Example: `melos exec rm README.md` to remove all README.md files.

Some useful filter options (can be combined):
- `--flutter`: Executes the command in Flutter rings only
- `--no-flutter`: Executes the command in non-Flutter rings only
- `--dir-exists=dirname`: Only executes the command in rings providing the `dirname` directory
- `--file-exists=filename`: Only executes the command in rings providing the `filename` file

See https://melos.invertase.dev/filters for all available filter options.

## Run a Melos script

```
melos run [script]
```

Runs the requested script as provided by the Melos configuration. `melos run` shows all available
scripts and lets the user select one. See section [Provided Scripts](#provided-scripts) for a list
of available Melos scripts.


# Invoke (Scraper Development)

We use [Invoke](https://www.pyinvoke.org/) (a CLI tool for executing tasks, similar to `make`) for
providing several scripts to simplify and unify common tasks.

## Using Invoke

All Invoke commands have to be executed from the `scraper` directory (which is the scraper
application project root). The following sections shortly describe how to work with Invoke. For very
detailled usage information, please refer to the
[Invoke documentation](https://docs.pyinvoke.org/en/stable/invoke.html).

If you are using an IntelliJ-based IDE (e.g. PyCharm), you may want to have a look at
[this](https://plugins.jetbrains.com/plugin/24793-pyinvoke) plugin for IDE integration.

The configuration (e.g. available scripts) is stored in the [tasks.py](../scraper/tasks.py) file.

## Setup a working copy

```
invoke bootstrap
```

Installs all necessary (`Python`) packages for the scraper application into the current Python
environment, resulting in the environment being used for building and running the app. Needs to be
done once after initial checkout and again each time the `pyproject.toml` file changes.

## Run an Invoke script

```
invoke [script]
```

Runs the requested script as provided by the Invoke configuration. `invoke -l` shows all available
scripts. See section [Provided Scripts](#provided-scripts) for a list of available Invoke scripts.


# Provided Scripts

This section describes the most importand development scripts. If not mentioned otherwise, these
scripts are available for both Melos (mobile app) and Invoke (scraper). Run them with `melos run
[script]` and `invoke [script]`, respectively.


## analyze: Run the linter

The `analyze` script runs the configured linter(s), e.g. [`dart analyze`](https://dart.dev/tools/dart-analyze)
(Dart) or [ruff](https://docs.astral.sh/ruff/) (Python).

## build.*: Build for various platforms

The `build.*` scripts build the mobile application for different platforms. The generated artifacts
are stored in the `artifacts` directory.

- `build.android`: Builds the Android application, creating an APK file.
- `build.linux`: Builds the Linux application, creating an Ubuntu ELF binary. Only works on Linux.
- `build.windows`: Builds the Windows application, creating an EXE file. Only works on Windows.

These scripts are only available in the mobile app environment!

## coverage: Generate code coverage reports

The `coverage` script generates code coverage reports in HTML and Cobertura (XML) formats and stores
them in the `coverage` directory. All unit tests  (i.e. the `test` script) must have run
successfully before!

## format: Auto format all sources

The `format` script auto-formats the sources according to our coding style guidelines (by running
`dart format` or `ruff format`).

## test: Run all unit tests

The `test` script runs all unit tests and gathers code coverage information (i.e. creates lcov.info
files).

## upgrade: Upgrade all dependencies

The `upgrade` script upgrades all dependencies to the most current versions that are allowed by the
constraints in the corresponding project configuration.


# CI workflows

Several [Github actions](https://github.com/Headbucket/trad/actions) ("CI") are defined to
automatically check the following quality properties after each push:
- Is it possible to build the application for all platforms?
- Do all unit tests pass?
- Is the code formatted properly?
- Are there no linter issues?

If all of these checks pass (i.e. all above questions are answered with "yes"), the pipeline
succeeds and the built application binaries are provided as artifacts. If any of them fails, the
whole pipeline does.
