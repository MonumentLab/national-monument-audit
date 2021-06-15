# -*- coding: utf-8 -*-

import argparse
import inspect
import os
from pprint import pprint
import re
import sys

# add parent directory to sys path to import relative modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
parentdir = os.path.dirname(parentdir)
sys.path.insert(0,parentdir)

from lib.collection_utils import *
from lib.geo_utils import *
from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/si/sos_data_location_fixed.csv", help="Input file")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_FILE", default="", help="Output file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
parser.add_argument('-verbose', dest="VERBOSE", action="store_true", help="Output all details?")
a = parser.parse_args()

OUTPUT_FILE = a.OUTPUT_FILE if len(a.OUTPUT_FILE) > 0 else a.INPUT_FILE

makeDirectories(OUTPUT_FILE)

fieldNames, rows = readCsv(a.INPUT_FILE)
# rows = addIndices(rows, keyName="_index")
rowCount = len(rows)

sponsorStrings = ["Administered by ", "Coadministered by ", "On loan to ", "Owned by ", "Restricted Owner "]

for i, row in enumerate(rows):
    locations = str(row["Owner/Location"])
    locations = [v.strip().strip(a.LIST_DELIMETER).strip() for v in locations.split(a.LIST_DELIMETER)]
    locations = [v for v in locations if len(v) > 0]

    notes = []
    locationDescriptions = []

    for loc in locations:

        sponsorFound = False
        for ss in sponsorStrings:
            if loc.startswith(ss):
                notes.append(loc)
                sponsorFound = True
                break

        if not sponsorFound:
            locationDescriptions.append(loc)

    if len(notes) > 0:
        existingNotes = [v.strip().strip(a.LIST_DELIMETER).strip() for v in row["Notes"].split(a.LIST_DELIMETER)]
        newNotes = unique(existingNotes + notes)
        rows[i]["Notes"] = newNotes

    if len(locationDescriptions) > 0:
        rows[i]["Location Description"] = locationDescriptions

    printProgress(i+1, rowCount)

if a.PROBE:
    sys.exit()

for f in ["Notes", "Location Description"]:
    if f not in fieldNames:
        fieldNames.append(f)

writeCsv(OUTPUT_FILE, rows, headings=fieldNames)
print("Done.")
