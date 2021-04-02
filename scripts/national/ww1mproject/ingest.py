# -*- coding: utf-8 -*-

import argparse
from bs4 import BeautifulSoup
import inspect
import os
from pprint import pprint
import re
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
parser.add_argument('-pages', dest="PAGES_FILES", default="tmp/ww1mproject/%s.json", help="Output Page JSON file pattern")
parser.add_argument('-items', dest="ITEMS_FILES", default="tmp/ww1mproject/items/%s.html", help="Output Item HTML file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/ww1mproject.csv", help="Output csv")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
a = parser.parse_args()

makeDirectories([a.PAGES_FILES, a.ITEMS_FILES, a.OUTPUT_FILE])

pagePattern = "https://ww1mproject.org/items/browse?page=%s&output=json"
itemPattern = "https://ww1mproject.org/items/show/%s"

def parseContents(html):
    if not html or len(html) < 1:
        return None

    row = {}
    bs = BeautifulSoup(html, "html.parser")

    metaContainer = bs.find("div", {"id": "primary"})
    if not metaContainer:
        return None

    # look for image
    imgTag = bs.find("img", {"class": "zoomImg"})
    if imgTag:
        row["Image"] = imgTag.get("src").strip()

    # look for lat/lon, e.g.
        # "latitude":42.32641542181900007335570990107953548431396484375
        # "longitude":-83.043991327285993975237943232059478759765625
    lats = re.findall(r'"latitude":([0-9\.]+)', html)
    lons = re.findall(r'"longitude":([0-9\.\-]+)', html)
    if len(lats) > 0 and len(lons) > 0:
        row["Latitude"] = lats[0]
        row["Longitude"] = lons[0]

    metaItems = metaContainer.find_all("div", {"class": "element"})
    for item in metaItems:
        label = item.find("h3")
        if not label:
            continue

        key = label.get_text(strip=True).strip()
        values = item.find_all("div", {"class": "element-text"})
        if len(values) < 1:
            continue

        # By default collapse everythng into a string
        svalues = [v.get_text(strip=True).strip() for v in values]
        value = " ".join(svalues)

        if key in ("Creator") and ";" in value:
            value = [v.strip() for v in value.split(";")]

        if key == "Location":
            addressParts = [text for text in values[0].stripped_strings]
            if len(addressParts) < 1:
                continue

            location = ""
            street = ""
            citystate = addressParts[-1]
            if len(addressParts) > 1:
                street = addressParts[-2]
                if len(addressParts) > 2:
                    location = ", ".join(addressParts[:-2])

            if "," not in citystate:
                continue
                # print(f'*** City, State not in right format: {citystate}')

            citystateParts = [p.strip() for p in citystate.split(",")]
            city = county = state = ""
            if len(citystateParts) == 2:
                city, state = tuple(citystateParts)
            elif len(citystateParts) >= 3:
                city, county, state = tuple(citystateParts[-3:])

            state = validateStateString(state)

            if "County" in state:
                county = state
                state = ""

            row["Location Description"] = location
            row["Street Address"] = street
            row["City"] = city
            row["County"] = county
            row["State"] = state

            continue


        row[key] = value

    # validate lat/lon
    easternMostLon = -64.565
    southernMostLat = 0
    if "Longitude" in row and "Latitude" in row and (float(row["Longitude"]) > easternMostLon or float(row["Latitude"]) < southernMostLat):
        print(f'Invalid coordinates for: {row["Title"]}')
        return None

    return row

page = 1
totalPages = 102
rows = []
fieldsOut = []
for i in range(totalPages):
    page = i+1
    filename = a.PAGES_FILES % page
    url = pagePattern % page
    r = downloadJSONFromURL(url, filename, overwrite=a.OVERWRITE)

    if "items" not in r:
        continue

    for item in r["items"]:
        if "id" not in item:
            print("No id for item:")
            print(item)
            continue

        itemUrl = itemPattern % item["id"]
        itemFilename = a.ITEMS_FILES % item["id"]
        contents = downloadFileFromUrl(itemUrl, itemFilename, overwrite=a.OVERWRITE, verbose=False)
        row = parseContents(contents)

        if row is None:
            print(f'Invalid file contents: {itemFilename}')
            continue

        row["Vendor Entry ID"] = item["id"]
        row["URL"] = itemUrl
        rows.append(row)
        for key in row:
            if key not in fieldsOut:
                fieldsOut.append(key)

    printProgress(page, totalPages)
    # break

writeCsv(a.OUTPUT_FILE, rows, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

print("Done.")
