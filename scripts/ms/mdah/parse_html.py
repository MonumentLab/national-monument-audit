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
from lib.math_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/mdah_html/*.html", help="HTML file pattern")
parser.add_argument('-geo', dest="INPUT_GEO_FILE", default="tmp/mdah_geojson/%s.json", help="geojson file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/ms/mdah_mississippi_landmarks.csv", help="Where to store .csv metadata")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
filecount = len(filenames)

makeDirectories(a.OUTPUT_FILE)

def parseHTMLFile(fn):
    contents = readTextFile(fn)

    if len(contents) < 1:
        print(f'{fn} is empty; skipping')
        return None

    bs = BeautifulSoup(contents, "html.parser")
    id = getBasename(fn)
    item = {
        "Vendor Entry ID": id,
        "URL": f'https://www.apps.mdah.ms.gov/Public/prop.aspx?id={id}&view=facts&y=1040'
    }

    # look for image
    m = re.search("'\.\.(\/photos\/.*\.jpg)'\;", contents, flags=re.IGNORECASE)
    if m:
        item["Image"] = f'https://www.apps.mdah.ms.gov{m.group(1)}'

    # Look for lat/lon
    geofn = a.INPUT_GEO_FILE % id
    geo = readJSON(geofn)
    # note that these are WGS_1984_Web_Mercator_Auxiliary_Sphere (WKID 3857) projection
    if "features" in geo and len(geo["features"]) > 0:
        geometry = geo["features"][0]["geometry"]
        item["x"] = geometry["x"]
        item["y"] = geometry["y"]

    mainTable = bs.find("table", {"id": "Table1"})
    if not mainTable:
        print(f"Could not find main table in {fn}")
        return None

    leftColumn = mainTable.find("td", {"align": "left"})
    if not leftColumn:
        print(f"Could not find left column in {fn}")
        return None

    sections = leftColumn.find_all("td", {"width": "325"})
    for section in sections:
        # header = section.find("td", {"class": "header5"})
        # if not header:
        #     continue
        # headerText = header.get_text().strip()

        labels = section.find_all("td", {"class": "tdLabel2"})
        for label in labels:
            labelText = label.get_text().strip(' :')

            value = label.findNext('td')
            valueText = value.get_text().strip()

            if labelText == "City/County":
                citycounty = [v.strip() for v in valueText.split(",", 2)]
                if len(citycounty) == 2:
                    city, county = tuple(citycounty)
                    if county.endswith(" County"):
                        county = county[:-7].strip()
                    item["City"] = city
                    item["County"] = county
            else:

                item[labelText] = valueText

    textC = leftColumn.find("td", {"class": "textC"})
    if textC:
        item["Description"] = textC.get_text().strip()

    return item

rows = []
fieldnames = []
for i, fn in enumerate(filenames):
    row = parseHTMLFile(fn)
    if row is not None:
        rows.append(row)
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    printProgress(i+1, filecount)

writeCsv(a.OUTPUT_FILE, rows, headings=fieldnames)
