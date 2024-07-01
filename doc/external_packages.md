External Package Evaluations
============================

This document records the reasons why certain libraries we depend on have been chosen. This
doesn't necessarily include all of our (direct) dependencies, but only the ones we explicitly
decided among some alternatives for.

# 1 Crosscutting Concepts

External libraries used by crosscutting concept implementations (`trad.crosscuttings`).

## 1.1. Logging Framework

There is no fully-featured logging system built-in to Dart, so logs from external libraries can
only be recorded if they are accidentially using the same logging tool as *trad*. This will
never apply to all of them, so the logging tool is more or less limited to *trad* itself.

The following external libraries have been considered:
 1. [Built-in `log` function](https://api.flutter.dev/flutter/dart-developer/log.html)
 2. [logging](https://pub.dev/packages/logging)
 3. [logger](https://pub.dev/packages/logger)
 4. [Log4Dart](https://pub.dev/packages/log4dart)

Based on the following abstracts of the several options, we chose to use the `logging` package
(number #2).

### Built-in `log` function

Advantages:
  - Available to (though not necessarily used by) all Dart components, including external libs
  - No external dependencies needed

Disadvantages:
  - Procedural interface (simple global function)
  - Channel name must be provided on every single log call
  - Without an external library, log levels are just magic integer values
  - No predefined destinations, writes to stdout only

### `logging` package

Advantages:
  - De-facto standard for logging, provided by the Dart team and even mentioned by the `log()` function documentation (=high probability of external libs using it)
  - Used by some external packages
  - Supports lazy evaluation/formatting
  - Fine grained log level and handler (destination) configuration

Disadvantages:
  - No predefined destinations, must be written manually
  - New releases (even for bugfixes) are quite rare, but at least there is activity

### `logger` package

Advantages:
  - Fine grained log level and handler (destination) configuration
  - Predefined log handlers
  - Actively developed

Disadvantages:
  - No lazy evaluation support
  - Predefined file printer writes asynchronously, meaning that in case of a problem/crash the last log messages may be missing (=we must provide our own implementation)


### `Log4Dart` package

This project seems to be abandoned because there was no activity since 2020 and the current Dart
version is not supported at all. That's why it was not evaluated any further.


## 1.2. Depedency Injection

There are a couple of big DI frameworks providing file-based configuration or the possibility to
replace implementations on runtime. As this is not needed, only the following lightweight
libraries providing just the mapping have been considered:

 - [Injector](https://pub.dev/packages/injector)
 - [GetIt](https://pub.dev/packages/get_it/)

We are using `GetIt` because it seems to be more actively developed (as in: more versions,
more frequent updates, more fixed bugs).


# 2 Infrastructure

External libraries used by the `infrastructure` implementations.

## 2.1. SQLite binding

There are two SQLite bindings available for Dart:
  1. [sqlite3](https://pub.dev/packages/sqlite3)
  2. [sqflite](https://pub.dev/packages/sqflite)

`sqlite3` is a pure Dart binding and requires some build system configuration to always ship a compatible sqlite3 binary (which can be done automatically in our cases by using the package `sqlite3_flutter_libs`).

`sqflite` depends on Flutter and always uses its sqlite3 binary. However, `sqflite` is based on the `sqlite3` package internally, and from the overview page it is not clear what further advantages it has.

Because we want to keep things as simple and lightweight as possible, we are using `sqlite3` directly for now (even though we already depend on Flutter anyway).


# 3 Unit Testing

External libraries used by unit tests. They are just *dev* dependencies.

## 3.1. Mocking Framework

For generating mock for unit tests, the following libraries have been considered:
 1. [mockito](https://pub.dev/packages/mockito)
 2. [mocktail](https://pub.dev/packages/mocktail)

We finally decided to use `mocktail`(#2). Note that due to the similar APIs, it should be relatively
easy to switch to `mockito`in the future if it becomes necessary.

### mockito

Advantages:
  - Recommended by the [Dart documentation](https://dart.dev/guides/testing#generally-useful-libraries), probably kind of de-facto standard
  - Mature and feature-rich (has been there for several years)
 
Disadvanatages:
 - Quite complex, needs explicit code generation (which requires additional build steps and a separate package)
 - Documentation seems to lack some information (e.g. introduction how-to doesn't work as-is; no information about how to generate the mocks)

### mocktail

Advantages:
 - Lightweight, easier to learn
 - Doesn't require code generation
 - Same (or at least very similar) API as `mockito`

Disadvantages:
 - Quite new, i.e. its API may change in the future
 - Seems to lack some popular features that are provided with the [`mocktailx`](https://pub.dev/documentation/mocktailx) extension package
 - Unclear limitations (i.e. what `mockito`s code generation is actually needed for)
