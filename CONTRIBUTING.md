# Code style

In general, we follow the [Dart style guidelines](https://dart.dev/effective-dart/style). However,
contradictory to the guidelines we use a line length of 100 characters, so make sure to add the
`--line-length` argument when using the `dart format` tool.

## Language

All public communication (code comments, documentation, log messages) as well as code entity names
shall be in English.

## Branches

When using feature branches, never *fast forward* merge them into `main`. The `main` branch shall
always be sane, i.e. it must be possible to compile and run it.
