Mobile App Architecture Documentation
=====================================

This is the documention of the architectural views and decisions of the `mobile app` part of the
[trad application](../architecture.md). See there for a system overview and overall documentation.


# 1. Introduction and Goals

The mobile app is the application actually running on mobile devices, and the main part of the
`trad` system.


# 3. Building Block View

## 3.1 Level 1

![Refinement of the first mobile app level](mobileapp/bbview_level2.png)

### 3.1.1 Motivation

In addition to the three common parts described in
[architecture section 5.2.3](../architecture.md#523-common-system-parts), the `infrastructure` ring
is split into a *flutter* and a *vanilla* part, containing all flutter and all non-flutter
dependent `infrastructure` components, respectively - see also
[ADR-1](../architecture.md#91-adr-1-how-to-integrate-flutter-into-the-architecture).

### 3.1.2 Source Locations

 - `adapters`: [mobileapp/adapters](../../mobileapp/adapters)
 - `core`: [mobileapp/core](../../mobileapp/core)
 - `crosscuttings`: [mobileapp/crosscuttings](../../mobileapp/crosscuttings)
 - `infrastructure`, *flutter* part: [mobileapp/infrastructure_flutter](../../mobileapp/infrastructure_flutter)
 - `infrastructure`, *vanilla* part: [mobileapp/infrastructure_vanilla](../../mobileapp/infrastructure_vanilla)

In additiona, please also refer to see [Accessing the file system](#54-accessing-the-file-system)
for how to access file system objects.
 
### 3.1.3 Interface Documentation

Interface name | Source location
------------|--------------------------------------------------------
core.boundaries.presentation | [core.boundaries.presentation](../../mobileapp/core/lib/boundaries/presentation.dart)
core.boundaries.data_exchange | TODO
core.boundaries.storage | [core.boundaries.storage](../../mobileapp/core/lib/boundaries/storage)
core.boundaries.positioning | TODO
adapters.boundaries.ui | [adapters.boundaries.ui](../../mobileapp/adapters/lib/boundaries/ui.dart)
adapters.boundaries.repositories | [adapters.boundaries.repositories](../../mobileapp/adapters/lib/boundaries/repositories)
adapters.boundaries.positioning | TODO


## 3.2 Level 2

### 3.2.1 `core`

![Refinement of the `core`](mobileapp/bbview_level3_core.png)

#### `core.entities`

Contains the basic data model (types and data structures) of the application. Must not depend on
anything else, but every other component is allowed to depend on it.

Source location: [mobileapp/core/lib/entities](../../mobileapp/core/lib/entities)

#### `core.boundaries`

Defines the interfaces (no implementations!) to the `adapters` ring. Separated into specific sub
systems like storage or presentation. Interfaces may only depend on `entities`, not on each other.

Source location: [mobileapp/core/lib/boundaries](../../mobileapp/core/lib/boundaries)

#### `core.usecases`

Implementation of all use cases. Further separated into the different application domains. Each use
case may depend on other use cases and on all core boundaries.

Source location: [mobileapp/core/lib/usecases](../../mobileapp/core/lib/usecases)


### 3.2.2 `adapters`

![Refinement of the `adapters`](mobileapp/bbview_level3_adapters.png)

#### `adapters.boundaries`

Defines the interfaces (no implementations!) to the `infrastructure` ring. Separated into specific
sub systems like `repositories` or `presentation`. These interfaces shall neither depend on any
core` structures (not even `core.entities`) nor on each other.

Source location: [mobileapp/adapters/lib/boundaries](../../mobileapp/adapters/lib/boundaries)


### 3.2.3 `infrastructure`

![Refinement of the `infrastructure`](mobileapp/bbview_level3_infrastructure.png)

The `infrastructure` ring is split into the `flutter` and the `vanilla` variant, which do not
depend on each other. However, if it is useful for some reason, the `infrastructure.flutter` part
may depend on the `infrastructure.vanilla` part (but not vice-versa).


# 5. Concepts

## 5.1 Logging

Provides a unified mechanism to record log messages to configured destinations (e.g. a log
file).

The public interface is located at [crosscuttings/lib/logging](../../mobileapp/crosscuttings/lib/logging),
the internal implementation at [crosscuttings/lib/src/logging](../../mobileapp/crosscuttings/lib/src/logging).

### 5.1.1 Use Cases

 - Write a log message to a specified channel and level
 - Configure the log destination and the logging level
 - Support for at least stdout and file logging
 - Support for (or at least easy extension of) lazy parameter evaluation/message string formatting
 - Possibility for more advanced file logging, like size limitation or rotation
 - Synchronized file logging to make sure the last messages have already been written when a problem occurs

### 5.1.2 Component Interface

The following diagram shows the public interface of the `logging` component:

![Public interface of the Logging component](mobileapp/crosscuttings_logging.png)

When using the `Logger` class, it is important to use a useful channel name. The name must start
with `trad` (to not mix up with external libraries accidentially), reflect the architectural
(and thus, also directory) position of the current source module/library and use dots as
delimeters, e.g. `trad.core.usecases.journal`. This schema allows to easily filter log files for
messages from certain system parts later on.

## 5.2 Knowledge Base

The knowledge base domain is implemented in a simple, generic way (similar to a wiki): It basically
consists of a storage providing *documents*, and a UI widget for displaying a single *document*.
Each such *document* represents a single knowledge base article. Index/ToC pages are also *documents*
(containing lists of links). The *documents* are Markdown text files stored and deployed as
application assets.

This approach clearly separates data from code and allows to add, remove or modify documents very
easily (i.e. without any source code knowledge).

Please see [Knowledge Base Documentation](../knowledgebase.md) for further documentation of this
application domain.

## 5.3 UI

The UI implementation is split into the presentation layer (`adapters` ring) and the concrete
Flutter implementation (`infrastructure` ring). Besides being the biggest and most complex of the
"outer ring" components, the constraints, guidelines and rules described in the sections
[4](../architecture.md#4-solution-strategy) and [5](../architecture.md#5-building-block-view) of
the architectur documentation apply normally: The `adapters.presentation` component finally decides
*what exactly to display*, while the `infrastructure.flutter.ui` component is responsible for
deciding *where* and (technically) *how*. The Flutter UI itself must be "as dumb as possible" and
must not maintain any state that is visible externally.

The communication works as follows:
 - `adapters.presentation.presenters` notifies `infrastructure.flutter.ui` about modified data via the `adapters.boundaries.ui` interface
 - `infrastructure.flutter.ui` directly notifies `adapters.presentation.controllers` about user actions

![Interactions between presenters, controllers and the UI](mobileapp/crosscuttings_ui_interaction.png)

Please see [Flutter UI Documentation](../ui-flutter.md) for further documentation of the Flutter UI
implementation.

## 5.4 Accessing the file system

File system operations in general are allowed from within the `infrastructure` and the `adapters` rings.
Since `dart:io` is part of the Dart standard library, there is no need to replace it by a different library
in the future, so it's not necessary to completely decouple the `dart:io` library. However, to improve
testability, we have to be able to replace the real file system operations. Furthermore, we have to support
different path styles (e.g. `\` VS. `/` separater) on different platforms. For these reasons, a special
`filesystem` boundary is responsible for creating entity objects like `dart.io.File` and for manipulating
directory paths. That means, every `infrastructure` and `adapters` part except the single component
implementing this boundary:
- shall preferably use `File` or `Directory` to identify certain file system locations/entities
- must use the `filesystem` component to manipulate path strings
- must never create e.g. `File` or `Directory` instances directly but get them from the `filesystem` component
- must never use any static methods of the `dart:io` library or its provided classes (such as `Directory.current`)

It's okay to do everything offered by the `FileSystemEntity` derived objects provided by the `filesystem`
component, though. Runtime information about the concrete platform or the running application instance (e.g.
the current working directory) can be retrieved via the `sysenv` boundary.

Within the `core` ring, no direct file system operations are allowed at all. File system entities are
identified by simple (platform dependent) strings (containing paths) there.

For unit testing, file system operations can be mocked with the in-memory implementation provided by the
[file](https://pub.dev/packages/file) package (only available for tests, not in a release build).
