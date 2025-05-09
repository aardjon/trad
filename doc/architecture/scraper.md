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

## 3.1 Level 1

![Refinement of the first scraper level](scraper/bbview_level2.png)

### 3.1.1 Motivation

The scraper part is split into the four "rings" as described in
[architecture section 5.2.3](../architecture.md#523-common-system-parts).

### 3.1.2 Source Locations

 - `adapters`: [scraper/src/trad/adapters](../../scraper/src/trad/adapters)
 - `core`: [scraper/src/trad/core](../../scraper/src/trad/core)
 - `crosscuttings`: [scraper/src/trad/crosscuttings](../../scraper/src/trad/crosscuttings)
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

![Refinement of the `core`](scraper/bbview_level3_core.png)


### 3.2.2 `adapters`

![Refinement of the `adapters`](scraper/bbview_level3_adapters.png)

Besides smaller components like the application settings, the `adapters` ring is split into two
main parts that are a bit special: `filters` and `pipes`, utilizing the *Pipes and Filters*
architectural pattern.

*Filters* read data from a *Pipe*, process, restructure or enrich it and write it back to the
same pipe. We implement a filter for each external data source (which imports route data from
that site) and also additional ones for e.g. optimizing the written database. There is one pipe
for each result file format (e.g. different routedb schema versions). Filters and Pipes must not
depend on each other: Filters must not have any knowledge about the concrete route database
structure, and pipes must not have any knowledge about concrete data sources.

By means of the higher-level Clean Architecture, filters and pipes are still regular adapters
connecting the `core` to the `infrastructure`, so basically the same rules apply to them. The
`adapters` ring defines the interfaces (no implementations!) to the `infrastructure` ring, which
shall neither depend on any `core` structures (not even `core.entities`) nor on each other.


#### `filters`

Encapsulates all knowledge about the concrete data sources (e.g. data structure and how to obtain
it). Must not contain any knowledge about the destination data format.

![Refinement of the `filters` component](scraper/bbview_level4_filters.png)

There is one filter implementation for each external data source, allowing us to easily add, remove
or maintain data sources independent from each other.

In addition to the general `adapter` rules, third party libs are allowed for filters if:
 - they are only needed by a single filter
 - they are not doing (e.g. network) IO with external systems
 - there is no need to mock them in unit tests

Source location: [scraper/src/trad/adapters/filters](../../scraper/src/trad/adapters/filters)

#### `pipes`

Encapsulates all knowledge about the routedb structure(s) (e.g. the database schema) to create. Must
not contain any knowledge about the external data sources.

![Refinement of the `pipes` component](scraper/bbview_level4_pipes.png)

There can be different pipe implementations for different database variants (e.g.schema versions),
allowing us to easily maintain old, backward-compatible versions while implementing new features.

Source location: [scraper/src/trad/adapters/pipes](../../scraper/src/trad/adapters/pipes)


### 3.2.3 `infrastructure`

![Refinement of the `infrastructure`](scraper/bbview_level3_infrastructure.png)


# 5. Concepts

## 5.1 Logging

Provides a unified mechanism to record log messages to configured destinations (e.g. a log
file). The scraper simply uses the [built-in logging system](https://docs.python.org/3/library/logging.html)
which comes with Python because it meets all our requirements and just needs to be configured.
