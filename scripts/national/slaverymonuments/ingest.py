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
parser.add_argument('-pages', dest="PAGES_FILES", default="tmp/slaverymonuments/%s.json", help="Output Page JSON file pattern")
parser.add_argument('-items', dest="ITEMS_FILES", default="tmp/slaverymonuments/items/%s.html", help="Output Item HTML file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/slaverymonuments.csv", help="Output csv")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
a = parser.parse_args()

makeDirectories([a.PAGES_FILES, a.ITEMS_FILES, a.OUTPUT_FILE])

pagePattern = "https://www.slaverymonuments.org/items/browse?page=%s&output=json"
itemPattern = "https://www.slaverymonuments.org/items/show/%s"

def parseContents(html):
    if not html or len(html) < 1:
        return None

    row = {}
    bs = BeautifulSoup(html, "html.parser")

    metaContainer = bs.find("div", {"id": "item-metadata"})
    if not metaContainer:
        return None

    # look for image
    imgLink = bs.find("a", {"class": "download-file"})
    if imgLink:
        row["Image"] = imgLink.get("href").strip()

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

        # Special case: subjects
        if key == "Subject":
            for value in values:
                valueHtml = str(value.encode_contents())
                parts = valueHtml.split('<br/>')
                subjectType = parts[0]
                parts = parts[1:]
                subjectValues = []
                for part in parts:
                    subjectValue = stripTags(part.strip()).replace('\\n', '').replace('\\', '').replace('"', '').replace('–', '').replace(" xe2x80x93", "").strip("'")
                    subjectValues.append(subjectValue)

                if len(subjectValues) < 1:
                    continue

                if "Type" in subjectType:
                    row["Object Types"] = subjectValues
                elif "Topic" in subjectType:
                    row["Subjects"] = subjectValues
                elif "Name" in subjectType:
                    row["Honorees"] = subjectValues
                else:
                    print(f'****Other category found: {subjectType}')
            continue

        # By default collapse everythng into a string
        values = [v.get_text(strip=True).strip() for v in values]
        value = " ".join(values)

        # Special case: title
        if key == "Title":
            # Examples:
            # Slavernijmonument (National Slavery Monument)(Amsterdam, The Netherlands)
            # Haitian Monument(Savannah, GA)
            # Unsung Founders Memorial(University of North Carolina at Chapel Hill)
            if "(" in value:
                parts = value.split("(")

                if len(parts) == 2:
                    value = parts[0].strip()
                elif len(parts) > 2:
                    value = "(".join(parts[:-1])

                remainder = parts[-1].strip().strip(")")
                parts = [p.strip() for p in remainder.split(",")]
                if len(parts) == 1:
                    row["Location Description"] = parts[0]
                elif len(parts) >= 2:
                    if len(parts[-1]) == 2:
                        row["City"] = parts[-2]
                        row["State"] = parts[-1]
                        if len(parts) > 2:
                            row["Location Description"] = ", ".join(parts[:-2])
                    else:
                        row["Location Description"] = remainder

        if key in ("Tags"):
            value = [v.strip() for v in value.split(",")]

        elif key in ("Contributor") or ";" in value:
            value = [v.strip() for v in value.split(";")]

        elif key in ("Type", "Creator", "Medium"):
            value = values

        row[key] = value

    # validate lat/lon
    easternMostLon = -64.565
    southernMostLat = 0
    if "Longitude" in row and "Latitude" in row and (float(row["Longitude"]) > easternMostLon or float(row["Latitude"]) < southernMostLat):
        print(f'Invalid coordinates for:')
        print(f' {row["Title"]}')
        if "Location Description" in row:
            print(f' {row["Location Description"]}')
        return None

    return row

page = 1
totalPages = 11
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
        contents = downloadFileFromUrl(itemUrl, itemFilename, overwrite=a.OVERWRITE)
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
