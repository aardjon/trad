import os
import sys

import requests

from parser_module import parse_page
from sqlite_module import Database

BASE_URL = "https://www.teufelsturm.de/wege/bewertungen/anzeige.php?wegnr={}"


def perform_scan(database_file_path, schema_file_path, start_id, end_id):
    database = Database(database_file_path, schema_file_path)
    count = end_id - start_id + 1
    for id in range(start_id, end_id + 1):
        page_text = get_page_text(id)
        post_data = parse_page(page_text)
        if post_data.peak:
            database.save_to_sqlite(post_data)
        progress = 100 * (id - start_id + 1) / count
        sys.stdout.write("Progress: %d%%   \r" % (progress))
        sys.stdout.flush()


def get_page_text(route_id):
    url = BASE_URL.format(route_id)
    page = requests.get(
        url=url, headers={"User-Agent": "Thunder Client (https://www.thunderclient.com)"}
    )
    return page.text


if __name__ == "__main__":
    dir_name = os.path.dirname(__file__)
    database_file_path = os.path.join(dir_name, "data.sqlite")
    schema_file_path = os.path.join(dir_name, "schema.sql")
    perform_scan(database_file_path, schema_file_path, 11000, 13500)
