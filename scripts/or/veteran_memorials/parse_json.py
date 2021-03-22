# -*- coding: utf-8 -*-

import argparse
import inspect
import json
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
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/or/Veteran Memorials in Oregon - Map.json", help="Input JSON file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/or/Veteran Memorials in Oregon - Map.csv", help="Output csv")
a = parser.parse_args()

data = readJSON(a.INPUT_FILE)
makeDirectories(a.OUTPUT_FILE)

cols = [c["name"] for c in data["meta"]["view"]["columns"]]

rowsOut = []
for row in data["data"]:
    rowOut = {}
    for j, col in enumerate(cols):
        if not col:
            continue
        value = row[j]
        if col == "Address":
            vlen = len(value)
            if vlen > 0 and value[0]:
                locdata = json.loads(value[0])
                for field in ["address", "city", "state", "zip"]:
                    if field in locdata and locdata[field]:
                        rowOut[field] = locdata[field]
            if vlen > 1:
                rowOut["Latitude"] = value[1] if value[1] else ""
            if vlen > 2:
                rowOut["Longitude"] = value[2] if value[2] else ""
        elif value:
            if isinstance(value, list):
                value = value[0]

            if col == "Photo":
                value = f'https://data.oregon.gov/views/2ku2-p2h8/files/{value}'
                
            rowOut[col] = value

    rowsOut.append(rowOut)

fieldnames = []
for row in rowsOut:
    for key in row:
        if key not in fieldnames:
            fieldnames.append(key)

writeCsv(a.OUTPUT_FILE, rowsOut, headings=fieldnames)
