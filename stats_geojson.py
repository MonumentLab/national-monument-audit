# -*- coding: utf-8 -*-

import argparse
import collections
import inspect
import math
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="path/to/file.geojson", help="Input geojson file")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
features = []
for fn in filenames:
    data = readJSON(fn)
    features += data["features"]

allProps = {}
for f in features:
    for key, value in f["properties"].items():
        if key in allProps:
            allProps[key]["count"] += 1
        else:
            allProps[key] = {
                "count": 1,
                "example": value
            }

allPropsSorted = []
for key, p in allProps.items():
    allPropsSorted.append({
        "key": key,
        "count": p["count"],
        "example": p["example"]
    })
allPropsSorted = sorted(allPropsSorted, key=lambda p: -p["count"])

print("Unique properties:")
for p in allPropsSorted:
    print(f'- {p["key"]}: {p["count"]} (e.g. "{p["example"]}")')
