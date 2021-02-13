# -*- coding: utf-8 -*-

import argparse
import inspect
import os
from pprint import pprint
import shutil
import subprocess
import sys
import time

# add parent directory to sys path to import relative modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
parentdir = os.path.dirname(parentdir)
sys.path.insert(0,parentdir)

from lib.collection_utils import *
from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-json', dest="JSON_FILES", default="tmp/dlg_json/pages/%s.json", help="Output JSON file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/ga/GeorgiaHistoricalMarkers.csv", help="Output csv")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
a = parser.parse_args()

makeDirectories([a.JSON_FILES, a.OUTPUT_FILE])

endpoint = 'https://dlg.usg.edu/collection/dlg_ghm.json'

rows = []
fieldsOut = []
page = 1
totalPages = 1
while True:
    filename = a.JSON_FILES % page
    url = endpoint + f'?per_page=100&page={page}'
    r = downloadJSONFromURL(url, filename, overwrite=a.OVERWRITE)

    if "response" not in r:
        break

    r = r["response"]
    if "pages" not in r or "docs" not in r or len(r["docs"]) < 1:
        break

    if page==1:
        totalPages = r["pages"]["total_pages"]
        print(f'{totalPages} total pages')

    for doc in r["docs"]:
        row = {}

        if "id" not in doc or "title" not in doc or not doc["id"] or not doc["title"]:
            continue

        row["Vendor Entry ID"] = doc["id"]
        row["Name"] = doc["title"]

        if "dcterms_spatial" in doc and doc["dcterms_spatial"]:
            parts = [v.strip() for v in doc["dcterms_spatial"][0].split(",")]
            if len(parts) >=2:
                lat, lon = tuple(parts[-2:])
                row["Latitude"] = lat
                row["Longitude"] = lon

        if "dc_date" in doc and doc["dc_date"]:
            date = doc["dc_date"][0]
            if "/" in date:
                date = date.split("/")[0]
            row["Year Constructed"] = date

        if "dcterms_creator" in doc and doc["dcterms_creator"]:
            row["Creators"] = doc["dcterms_creator"]

        if "dcterms_description" in doc and doc["dcterms_description"]:
            otherText = ""
            for descr in doc["dcterms_description"]:

                if descr.lower().startswith("text of marker:"):
                    row["Text"] = descr[16:]
                elif descr.lower().startswith("text of markers:"):
                    row["Text"] = descr[17:]
                elif descr.lower().startswith("location:"):
                    row["Location Description"] = descr[10:]
                elif descr.lower().startswith("location"):
                    row["Location Description"] = descr[9:]
                else:
                    otherText += descr + " "
            if len(otherText) > 0:
                row["Notes"] = otherText

        for key in row:
            if key not in fieldsOut:
                fieldsOut.append(key)

        rows.append(row)

    if r["pages"]["last_page?"]:
        break

    printProgress(page, totalPages)
    page += 1

writeCsv(a.OUTPUT_FILE, rows, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)
