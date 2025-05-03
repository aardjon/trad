# trad - The ultimate app for climbing in Saxony

A utility for climbing in the Saxon Switzerland area providing the following main features:
 - Personal climbing journal
 - Climbing guide
 - Small knowledge base with useful information
 - Ability to work completely offline

## Setup & Running

When running the `mobile app` for the first time (locally or on any mobile device), it will ask you
to import a route database file (which is currently not publicly available for legal reasons). If
you don't have this file, you can create it by yourself using the `scraper`:

1. [Setup the Route Data Scraper](CONTRIBUTING.md#route-data-scraper)
2. Run the following commands from the source root directory:

```bash
cd scraper/src
mkdir output_directory
python scraper.py output_directory
```

The new route database file is written into `output_directory`. Depending on your network speed,
running the scraper may take up to an hour or even longer. Provide `-v` to enable some more verbose
debug log, which will give you some kind of progress feedback.
