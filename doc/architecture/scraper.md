Scraper Architecture Documentation
==================================

This is the documention of the architectural views and decisions of the `scraper` part of the
[trad application](../architecture.md). See there for a system overview and overall documentation.

# 1. Introduction and Goals

## 1.1 Requirements Overview

The scraper application is a command line tool that downloads all the summit related data from
external sources and generates the route database, as shortly described in
[ADR-3](../architecture.md#93-adr-3-decouple-the-mobile-app-from-external-route-data-services).
It is intended to run automated and unattended.

Please refer to [Requirements & Goals](../requirements.md) for further information about functional
requirements.

## 1.2 Different/Additional quality goals

Because the scraper of course depends on a working network connection and does not run on a mobile
device, some quality goals are not relevant for this part of the software. Goals that are
applicable (e.g. Maintenance) still apply, though.

Because the scraper runs unattended anyway, a short runtime (performance) is not a big thing. We
still want to avoid unnecessary waiting times and keep the traffic on external sites at the
absolute minimum, though.

# 3. Building Block View

![Overview of the Scraper architecture](scraper/sysarc_overview.png)

## 3.1 Level 1

![Refinement of the first scraper level](scraper/bbview_level2.png)

### 3.1.1 Motivation

The scraper part is split into the four "rings" as described in
[architecture section 5.2.3](../architecture.md#523-common-system-parts). Additionally, the scraper
utilizes the [Pipes and Filters](https://www.geeksforgeeks.org/pipe-and-filter-architecture-system-design/)
architectural pattern for keeping the different data flows separated while staying flexible:
*Filters* read data from a *Pipe*, process, restructure or enrich it and write it back to the same
Pipe. Pipes must not depend on Filters, but Filters depend on the generic Pipe boundary (but not on
a certain Pipe implementation) as they must read and write data from/to it.

Because all Filters and Pipes are actually converters between external or infrastructure data and
core entities, they are considered part of the `adapters` ring by means of the higher-level Clean
Architecture pattern. That's why the `adapters` ring is split into the three components `adapters`,
`filters` and `pipes`:

- The `pipes` component provides all Pipe (abstraction of the database being created) implementations
- The `filters` component provides all Filter (processing steps, e.g. retrieve and add data) implementations
- The `adapters` component provides regular adapter implementations by means of the Clean Architecture pattern

### 3.1.2 Source Locations

 - `adapters`: [scraper/src/trad/adapters](../../scraper/src/trad/adapters)
 - `core`: [scraper/src/trad/core](../../scraper/src/trad/core)
 - `crosscuttings`: [scraper/src/trad/crosscuttings](../../scraper/src/trad/crosscuttings)
 - `filters`: [scraper/src/trad/filters](../../scraper/src/trad/filters)
 - `pipes`: [scraper/src/trad/pipes](../../scraper/src/trad/pipes)
 - `infrastructure`: [scraper/src/trad/infrastructure](../../scraper/src/trad/infrastructure)

### 3.1.3 Interface Documentation

Interface name | Source location
------------|--------------------------------------------------------
core.boundaries.filters | [core.boundaries.filters](../../scraper/src/trad/core/boundaries/filters.py)
core.boundaries.pipes | [core.boundaries.pipes](../../scraper/src/trad/core/boundaries/pipes.py)
core.boundaries.settings | [core.boundaries.settings](../../scraper/src/trad/core/boundaries/settings.py)
adapters.boundaries.database | [adapters.boundaries.database](../../scraper/src/trad/adapters/boundaries/database.py)
adapters.boundaries.http | [adapters.boundaries.http](../../scraper/src/trad/adapters/boundaries/http.py)


## 3.2 Level 2

### 3.2.1 `core`

Contains all business entities and business logic on an abstract level.

![Refinement of the `core`](scraper/bbview_level3_core.png)

Source location: [scraper/src/trad/core](../../scraper/src/trad/core)

### 3.2.2 `adapters`

Encapsulates all regular `adapters` components of the Clean Architecture, and also provides the
boundary interface to the `infrastructure` ring that `filters` and `pipes` may depend on.

![Refinement of the `adapters`](scraper/bbview_level3_adapters.png)

The `adapters` component depend neither on `pipes` nor on `filters`. All the regular rules
described in [architecture section 5.2.3](../architecture.md#523-common-system-parts) apply, too.

Source location: [scraper/src/trad/adapters](../../scraper/src/trad/adapters)

### 3.2.3 `filters`

Encapsulates all knowledge about the concrete data sources (e.g. data structure and how to obtain
it). Must not contain any knowledge about the destination data format.

![Refinement of the `filters` component](scraper/bbview_level3_filters.png)

There is one *Filter* implementation for each external data source (which imports route data from
that site), allowing us to easily add, remove or maintain data sources independent from each other.
Furthermore, special *Filter*s are there e.g. for optimizing the written database.

Filters depend on the *core.boundaries.pipes* but not on a certain *Pipe* implementation. They may
directly depend on `adapters` (and thus, also on the `infrastructure` boundaries).

In addition to the general `adapter` rules, third party libs are allowed for filters if:
 - they are only needed by a single filter
 - they are not doing (e.g. network) IO with external systems
 - there is no need to mock them in unit tests

Source location: [scraper/src/trad/filters](../../scraper/src/trad/filters)

### 3.2.4 `pipes`

Encapsulates all knowledge about the routedb structure(s) (e.g. the database schema) to create. Must
not contain any knowledge about the external data sources.

![Refinement of the `pipes` component](scraper/bbview_level3_pipes.png)

There can be different pipe implementations for different database variants (e.g.schema versions),
allowing us to easily maintain old, backward-compatible versions while implementing new features.

Source location: [scraper/src/trad/pipes](../../scraper/src/trad/pipes)


### 3.2.5 `infrastructure`

Contains all concrete implementations of library bindings and all technical details.

![Refinement of the `infrastructure`](scraper/bbview_level3_infrastructure.png)

Source location: [scraper/src/trad/infrastructure](../../scraper/src/trad/infrastructure)

# 5. Concepts

## 5.1 Logging

Provides a unified mechanism to record log messages to configured destinations (e.g. a log
file). The scraper simply uses the [built-in logging system](https://docs.python.org/3/library/logging.html)
which comes with Python because it meets all our requirements and just needs to be configured.
