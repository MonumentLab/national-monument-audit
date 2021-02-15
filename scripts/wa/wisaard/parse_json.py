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
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/wisaard_json/*.json", help="Input JSON file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/wa/washington_wisaard_register_public.csv", help="Output csv")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
filecount = len(filenames)
makeDirectories(a.OUTPUT_FILE)

def parseJSONFile(fn):
    resp = readJSON(fn)
    frows = []

    if "results" in resp:
        for i, result in enumerate(resp["results"]):
            row = {}
            for key in ["AddressLine1", "ConstructionYear", "ResourceID", "SmithsonianNumber", "RegisterName", "RegisterTypeName"]:
                if key in result and result[key]:
                    row[key] = result[key]

            if "features" in result and len(result["features"]) > 0:
                feature = result["features"][0]

                if feature["geometryType"] == "esriGeometryPoint":
                    row["x"] = feature["geometry"]["x"]
                    row["y"] = feature["geometry"]["y"]

                elif feature["geometryType"] == "esriGeometryPolygon":
                    row["x"] = feature["geometry"]["rings"][0][0][0]
                    row["y"] = feature["geometry"]["rings"][0][0][1]

                elif feature["geometryType"] == "esriGeometryPolyline":
                    row["x"] = feature["geometry"]["paths"][0][0][0]
                    row["y"] = feature["geometry"]["paths"][0][0][1]

                else:
                    print(f' *** Unknown geometry type: {feature["geometryType"]} in {fn} index:{i}')

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
