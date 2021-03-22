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
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/nj_lucy_json/*.json", help="Input JSON file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/nj/lucy_historic_properties.csv", help="Output csv")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
filecount = len(filenames)
makeDirectories(a.OUTPUT_FILE)

def parseJSONFile(fn):
    resp = readJSON(fn)
    frows = []

    if "features" not in resp:
        print(f'Warning: no features found in {fn}')
        return frows

    for i, feature in enumerate(resp["features"]):
        row = {}
        attr = feature["attributes"]
        for key in ["OBJECTID", "NJEMS_STID", "NJEMS_PIID", "NAME", "ALT_NAME", "ADDRESS", "DEMOLISHED", "STATUS", "NHL", "LOC_RESTR", "NOTES"]:
            if key in attr and attr[key]:
                row[key] = attr[key]

        geo = feature["geometry"]

        if "rings" in geo:
            row["x"] = geo["rings"][0][0][0]
            row["y"] = geo["rings"][0][0][1]

        else:
            print(f' *** Unknown geometry type: {fn}: {i}')

        frows.append(row)

    return frows

rows = []
for i, fn in enumerate(filenames):
    frows = parseJSONFile(fn)
    rows += frows
    printProgress(i+1, filecount)

fieldnames = []
for row in rows:
    for key in row:
        if key not in fieldnames:
            fieldnames.append(key)

writeCsv(a.OUTPUT_FILE, rows, headings=fieldnames)
