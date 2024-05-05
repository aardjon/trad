Requirements & Goals
====================

# 1. Personal Journal
 - Manual logging of the following data for all climbed routes:
   - Date
   - Area
   - Summit
   - Route
   - Grade
   - Team
   - (Personal) Safety Rating
   - Notes
 - Show all logs
 - Show last personal safety rating
 - On logging:
    - Possibility to search summit and route from the route database
    - All fiedls (esp. route) must be changeable (sometimes one doesn't climb an exact route)
    - For personal safety rating, use the last rating as default
 - Add/reference photos
    - Shall photos be connected to routes or the other way around? Maybe connect to log entries instead?
 - Import and Export from/to CSV file
 - Automatic backup of the journal database
    - Online/Cloud destinations
    - Local storage
    - Backward compatible import of old backups!
    - Maybe CSV export already satisfies this, needs to be checked!

# 2. Route Database
## 2.1 List of climbing routes in the Saxon Switzerland area
 - List of all summits:
    - Summit name
    - Area
    - Stop sign, if currently banned from climbing
 - For each summit, show the following information:
    - Name
    - All routes:
        - Name
        - Grade
        - Rating
        - Stop sign, if currently banned from climbing
    - Geographical position (coordinates)
    - Date of climbing bans, if any (list at https://bergsteigerbund.de/bergsport/aktuelle-informationen-zum-klettern-und-wandern/)
 - Filter/sort by name
 - Filter/sort by grade
 - Filter/sort by distance to current position (if available)
 - Provide "Share" or "Open with" action for summit coordinates to easily open it in external apps (e.g. maps or navigation)
 - For each route, show the following data:
   - Name
   - Grade
   - Remarks
   - Rating
 - Import route data from different online sources:
    - Teufelsturm
    - DB-Sandsteinklettern
    - ...?
 - Do not allow editing route data

## 2.2 Updating
 - A process for getting new/updated route data into the app has still to be defined
 - For the beginning, go with an example snapshot included directly into the app
 - May it'd be enough to simply import a manually downloaded SQLite file?

# 3. Knowledgebase
## 3.1 Information about Knots
 - Important knots and their usage for climbing in the Saxon Switzerland
 - Including a sketch

## 3.2 Saxon Switzerland Climbing Regulations
 - Source: SBB
 - Changes very rarely only (some like "once in ten years")

# 4 General/Misc
 - User interface language: German
 - Keep the doors open for adding multi-language (Czech?) support later
