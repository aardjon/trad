# Contribution Guide

## Feedback

Feel free to [open an issue](https://github.com/Headbucket/trad/issues) for bug reports, feature requests or simple questions. Please apply the corresponding label your new issue.

## Setup a development environment for the mobile app

This section is a short how-to for setting up a development environment for the mobile app. It assumes that you already got a local working copy of the source code repository (e.g. `git clone https://github.com/Headbucket/trad.git`). The mobile application code is stored within the `mobileapp` directory, so all following commands should be executed from there.

### 1. Make sure you have appropriate versions of the Flutter and Dart frameworks installed in your system.

At the time of writing, we were using Dart 3.4.0 and Flutter 3.22.0, please check the `environment` section of [this pubspec file](mobileapp/infrastructure_flutter/pubspec.yaml) for the current version constraints.

If everything is set up correctly, the `dart` and `flutter` commands shall be available in your PATH. `flutter doctor -v` shouldn't report any critical issues.

### 2. Install [Melos](https://melos.invertase.dev):

```
dart pub global activate melos
```

### 3. Install all application dependencies:
```
melos bootstrap
```

### 4. Use melos scripts to build and test the application:

```
# Run all unit tests
$ melos run test
# Build an android APK
$ melos run build.android
```

For further information about available `Melos` scripts, please see [Development tools and CI](doc/devtools.md).

### 5. Setup an IDE

IDEs with Dart/Flutter support (e.g. Android Studio) usually rely on the Dart tools and should therefore automatically apply the central configuration. However, please check/set the following two settings:
 - The editor/formatter line length must be set to 100 characters
 - All linter issues (including `note`s) should be displayed


## Coding Rules

- In general, we follow the [Dart style guidelines](https://dart.dev/effective-dart/style).
- Contradictory to the default guidelines, we use a line length of 100 characters.
- All public communication (code comments, documentation, log messages) as well as code entity names shall be in English.
- Before committing a change, always run the auto formatter and the linter (i.e. `melos run format` and `melos run analyze`).
- See [Commit Guidelines](doc/commit_guidelines.md) for rules about commits and commit messages.
