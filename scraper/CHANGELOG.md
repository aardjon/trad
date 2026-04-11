# Scraper & Route Database Changelog


## Version 0.3.1 - 2026-04-11

### Fixed Bugs:
 - Normalize umlauts when merging route names (#41)


## Version 0.3.0 - 2026-03-29

### New/Improved Features:
 - Import the names of the sectors that summits are assigned to (#20)
 - Update to DB schema version 1.2

### Fixed Bugs:
 - Increase the radius within which two summit coordinates are considered 'equal' to 250m
 - Do not import forbidden summits from OSM


## Version 0.2.0 - 2026-03-14

### New/Improved Features:
 - Write information about all external sources (#20, #22)
 - Import data from sandsteinklettern.de
 - Update to DB schema version 1.1


## Version 0.1.2 - 2026-01-24

### Fixed Bugs:
 - Some summits are not merged properly (#16)


## Version 0.1.1 - 2025-12-13

### New/Improved Features:
 - Route data from different sources is now merged

### Fixed Bugs:
 - Teufelsturm posts are ignored for routes with additional information (#18)


## Version 0.1.0 - 2025-11-29

- First release
- Importing data from Teufelsturm and OSM
- Starting with DB schema version 1.0
