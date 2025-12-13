# Contribution Guide

## Feedback

Feel free to [open an issue](https://github.com/Headbucket/trad/issues) for bug reports, feature requests or simple questions. Please assign the corresponding label your new issue.

## Setup a development environment

This section is a short how-to for setting up a development environment for the mobile app and/or
the scraper application. It assumes that you already got a local working copy of the source code
repository (e.g. `git clone https://github.com/Headbucket/trad.git`).

### Mobile App

In your local working copy, the mobile application code is stored within the `mobileapp` directory,
so all following commands must be executed from there.

#### 1. Make sure you have appropriate versions of the Flutter and Dart frameworks installed in your system.

At the time of writing, we were using Dart 3.4.0 and Flutter 3.22.0, please check the `environment` section of [this pubspec file](mobileapp/infrastructure_flutter/pubspec.yaml) for the current version constraints.

If everything is set up correctly, the `dart` and `flutter` commands shall be available in your PATH. `flutter doctor -v` shouldn't report any critical issues.

#### 2. Install [Melos](https://melos.invertase.dev):

```
dart pub global activate melos
```

#### 3. Install all application dependencies:
```
melos bootstrap
```

#### 4. Use melos scripts to build and test the application:

```
# Run all unit tests
$ melos run test
# Build an android APK
$ melos run build.android
```

For further information about available `Melos` scripts, please see [Development tools and CI](doc/devtools.md).

#### 5. Setup an IDE

IDEs with Dart/Flutter support (e.g. Android Studio) usually rely on the Dart tools and should therefore automatically apply the central configuration. However, please check/set the following two settings:
 - The editor/formatter line length must be set to 100 characters
 - All linter issues (including `note`s) should be displayed

 
### Route Data Scraper

In your local working copy, the scraper code is stored within the `scraper` directory, so all
following commands must be executed from there.

We recommend to create a separate `virtualenv` for `trad`. If you do so, all commands given in this
section must be run with this `virtualenv` being activated, of course.

#### 1. Make sure you have an appropriate Python version installed in your system.

At the time of writing, we were using Python 3.14.0, please check the `project.requires-python`
setting of [this pyproject.toml file](scraper/pyproject.toml) for the current version constraint.

It is usually a good idea to use the latest `pip` version for package installation. Update it with
`pip install -U pip`.

If everything is set up correctly, the `python` and `pip` commands must be available in your PATH.

#### 2. Install [Invoke](https://www.pyinvoke.org):

```
pip install -U invoke
```

#### 3. Install all application dependencies:
```
invoke bootstrap
```

#### 4. Use Invoke scripts to test and run the application:

```
# Run all unit tests
$ invoke test
# Run the scraper application
$ invoke run
```

For further information about available `Invoke` scripts, please see [Development tools and CI](doc/devtools.md).

#### 5. Record and replay network traffic

To avoid accessing external network resources while testing and debugging, the Scraper can record
all network traffic to disk:

```
python src/scraper.py --record-traffic /path/to/store/recordings /path/to/store/routedb
```

The recorded traffic can be replayed, to re-create the same route database without doing any real
network requests:

```
python src/scraper.py --replay-traffic /path/to/store/recordings /path/to/store/routedb
```

Note that the recordings directory can easily exceed 100 MB and contain several tens of thousands
of files.


## Important branches

- Changes to the mobile app must be merged into the `mobileapp-staging` branch
- Changes to the scraper must be merged into the `scraper-staging` branch
- `scraper-staging` must not contain changes to the `mobileapp` directory, and vice-versa
- If the required `staging` branch doesn't exist, just create it from `main`


## Coding Rules

- In general, we follow the [Dart style guidelines](https://dart.dev/effective-dart/style) for Dart and the [Black style](https://black.readthedocs.io/en/stable/the_black_code_style/) for Python code.
- Contradictory to the default guidelines, we use a line length of 100 characters.
- All public communication (code comments, documentation, log messages) as well as code entity names shall be in English.
- Before committing a change, always run the auto formatter and the linter (i.e. `melos run format`/`invoke format` and `melos run analyze`/`invoke analyze`).
- See [Commit Guidelines](doc/commit_guidelines.md) for rules about commits and commit messages.

## Architecture

For studying and modifying the *trad* sources, some understanding of its basic structure and design decisions may be useful. So it is probably a good idea to read the [Software Architecture Documentation](doc/architecture.md) before contributing a change.
