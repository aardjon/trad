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
