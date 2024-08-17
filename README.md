# trad - The ultimate app for climbing in Saxony

A utility for climbing in the Saxon Switzerland area providing the following main features:
 - Personal climbing journal
 - Climbing guide
 - Small knowledge base with useful information
 - Ability to work completely offline

## Setup & Running

To run the app (locally or on any mobile device), you need the route database file named `peaks.sqlite` (currently not publicly available for legal reasons). Put it into the data directory your operating system assigned to the `trad` application. Some examples for the data directory on different platforms are:
 - Linux: `$HOME/.local/share/trad/`
 - Windows: `%APPDATA%\trad`
 - Android: `/data/user/0/de.wesenigk.trad/files/`

On startup, the expected file path is logged on the info level as follows:

```
[2024-08-17 19:35:43.791645][INFO][trad.adapters.storage.routedb] Connecting to route database at: /home/aardjon/.local/share/trad/peaks.sqlite
```

If the file is not found, the app start fails with the following error message:

```
SqliteException(14): while opening the database, unable to open database file, unable to open database file (code 14)
```
