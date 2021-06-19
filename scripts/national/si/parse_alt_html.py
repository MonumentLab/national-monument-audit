# -*- coding: utf-8 -*-

import argparse
from bs4 import BeautifulSoup
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
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/si/sos_data_location_fixed.csv", help="Input file")
parser.add_argument('-html', dest="HTML_FILE", default="tmp/si_html/alt_items/%s.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="", help="Output file")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just print result?")
a = parser.parse_args()

OUTPUT_FILE = a.OUTPUT_FILE if len(a.OUTPUT_FILE) > 0 else a.INPUT_FILE

makeDirectories(OUTPUT_FILE)

fieldNames, rows = readCsv(a.INPUT_FILE)
# rows = addIndices(rows, keyName="_index")
rowCount = len(rows)
invalidCount = 0
stateMap = getStates()
states = [s for s in stateMap]

for i, row in enumerate(rows):
    id = row["Id"]

    if id == "":
        continue

    filename = a.HTML_FILE % id

    if not os.path.isfile(filename):
        invalidCount += 1
        print(f' Could not find {filename}')
        continue

    contents = readTextFile(filename)
    if len(contents) < 1:
        invalidCount += 1
        print(f' No contents for {filename}')
        continue

    bs = BeautifulSoup(contents, "html.parser")

    main = bs.find("form", {"name": "full"})
    if not main:
        invalidCount += 1
        continue

    colsWithLabels = main.find_all("td", {"width": "1%"})
    if len(colsWithLabels) < 1:
        invalidCount += 1
        continue

    locationDescription = ""
    foundState = ""
    image = ""
    ownerStrings = ["Administered by", "Coadministered by", "On loan to", "Owned by", "Restricted Owner", "Lent by"]
    for col in colsWithLabels:
        label = col.get_text().strip().strip(":")

        if label == "Digital Reference":
            colRow = col.parent
            images = colRow.find_all("img")
            if len(images) > 0 and image == "":
                image = images[0].get("src").strip()

        elif label == "Owner":
            colRow = col.parent
            valueLinks = colRow.find_all("a", {"class": "SirisSmallAnchor"})
            for link in valueLinks:
                value = link.get_text().strip()
                valid = True
                # check to see if this is an owner statement
                for s in ownerStrings:
                    if value.startswith(s):
                        valid = False
                        break
                if not valid:
                    continue
                # check to see if a state is included
                valid = False
                for state in states:
                    if state in value:
                        foundState = state
                        valid = True
                        break
                if not valid:
                    continue
                if value.startswith("Located at "):
                    value = value[len("Located at "):]
                elif value.startswith("Located "):
                    value = value[len("Located "):]
                locationDescription = value
                break
            break # /col

    if len(locationDescription) < 1:
        continue

    parts = locationDescription.split(foundState)
    fullAddress = parts[0]
    if len(parts) > 2: # e.g. University of Alabama....
        fullAddress = foundState.join(parts[:-1])

    streetAddress = ""
    city = ""
    county = ""
    addressParts = [p.strip() for p in fullAddress.split(",")]
    addressParts = [p for p in addressParts if p != ""]

    if len(addressParts) < 1:
        continue

    if len(addressParts) == 1:
        city = addressParts[0]
    elif len(addressParts) == 2:
        streetAddress, city = tuple(addressParts)
    else:
        city = addressParts[-1]
        addressParts = addressParts[:-1]
        for p in addressParts:
            # if starts with a number, assume it is an address
            if p[0].isdigit():
                streetAddress = p
                break
        if streetAddress == "":
            for p in addressParts:
                # if contains a number, assume it is an address
                if stringContainsNumbers(p):
                    streetAddress = p
                    break
        # otherwise, just take the first entry
        if streetAddress == "":
            streetAddress = addressParts[0]

     # Cities should not have numbers
    if city != "" and not city.isalpha():
        city = ""

    # Check for county
    if city.endswith("County"):
        county = city
        city = ""

    rows[i]["City"] = city
    rows[i]["County"] = county
    rows[i]["Street Address"] = streetAddress
    if locationDescription != "":
        rows[i]["Location Description"] = locationDescription
    if image != "":
        rows[i]["Image"] = image

    # if city != "":
    #     print(city)

    # if a.PROBE:
    #     print(f'Location: {locationDescription}')

    printProgress(i+1, rowCount)

print(f'{invalidCount} invalid records')

if a.PROBE:
    sys.exit()

for f in ["City", "County", "Street Address", "Location Description", "Image"]:
    if f not in fieldNames:
        fieldNames.append(f)

writeCsv(OUTPUT_FILE, rows, headings=fieldNames)
print("Done.")
