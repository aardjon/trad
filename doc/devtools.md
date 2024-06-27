# Development tools and CI

Because the mobile application (`mobileapp` directory) is split into multiple sub projects, using the `Dart`/`Flutter` framework tools directly or in a CI task can be tedious. That's why we use [Melos](https://melos.invertase.dev/) (a CLI tool for managing multiple `Dart` projects within a mono-repo) to simplify and unify things.

Our Melos configuration provides several scripts for common tasks, that can be used in local development as well as from CI workflows. This helps to use the same configuration in both environments.


## Using Melos

All Melos commands have to be executed from the `mobileapp` directory (which is the mobile application project root). The following sections shortly describe the most important commands, please refer to the [Melos documentation](https://melos.invertase.dev/getting-started) for more detailed information. There is one important thing to know, though: **Please do not use the default `melos format` command** because it doesn't respect our formatter configuration. **Use the `melos run format` script instead.**

You may also want to have a look at [IDE Support](https://melos.invertase.dev/ide-support) for how to integrate Melos into four favourite IDE.

### Setup a working copy

```
melos bootstrap
```

Installs all necessary (`Dart`) packages for the mobile app into the local `Flutter` environment (respecting the version constraints from all sub projects and their dependencies), resulting in the environment being used for building and running the app. Needs to be done once after initial checkout and again every time any of the `pubspec.yaml` or `pubspec.lock` files changes.

### Run a single command in all (or some) sub projects

```
melos exec [filter options] [shell command]
```

Executes the given `shell command` in all sub projects matching the given `filter options`. Example: `melos exec rm README.md` to remove all README.md files.

Some useful filter options (can be combined):
- `--flutter`: Executes the command in Flutter projects only
- `--no-flutter`: Executes the command in non-Flutter projects only
- `--dir-exists=dirname`: Only executes the command in projects providing the `dirname` directory
- `--file-exists=filename`: Only executes the command in projects providing the `filename` file

See https://melos.invertase.dev/filters for all available filter options.

### Run a Melos script

```
melos run [script]
```

Runs the requested script as provided by the Melos configuration. `melos run` shows all available scripts and lets the user select one. See section [Provided Melos Scripts](#provided-melos-scripts) for a list of all available Melos scripts.


## Provided Melos Scripts

Melos scripts can be executed by `melos run [script]`. Alle available scripts are defined in the [Melos configuration file](../mobileapp/melos.yaml).

### analyze: Run the linter

The `analyze` script runs the [Dart Linter](https://dart.dev/tools/dart-analyze) (i.e. `dart analyze`) for all sub projects.

### build.*: Build for various platforms

The `build.*` scripts build the mobile application for different platforms. The generated artifacts are stored in the `artifacts` directory.

- `build.android`: Builds the Android application, creating an APK file
- `build.linux`: Builds the Linux application, creating an Ubuntu ELF binary

### format: Auto format all sources

The `format` script auto-formats the sources according to our coding style guidelines (by running `dart format --line-length=100`).

### test: Run unit tests

The `test` script runs all unit tests (i.e. `dart test` or `flutter test`) for all sub projects and gathers code coverage information.

### upgrade: Upgrade all dependencies

The `upgrade` script upgrades all dependencies to the most current versions that are allowed by the constraints in the `pubspec.yaml` files. All affected `pubspec_overrides.yaml` and `pubspec.lock` files are regenerated.


## CI workflows

Several [Github actions](https://github.com/Headbucket/trad/actions) ("CI") are defined to automatically check the following quality properties after each push:
- Is it possible to build the application for all platform?
- Do all unit tests pass?
- Is the code formatted properly?
- Are there no linter issues?

If all of these checks pass (i.e. all above questions are answered with "yes"), the pipeline succeeds and the built application binaries are provided as artifacts. If any of them fails, the whole pipeline does.
