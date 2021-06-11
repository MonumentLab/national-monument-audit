# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import sys

from lib.collection_utils import *
from lib.geo_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *
from lib.data_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="data/vendor/national/osm/quickOSM/*.csv", help="Input .csv files")
parser.add_argument('-id', dest="ID_KEY", default="osm_id", help="ID key")
parser.add_argument('-lat', dest="LAT_KEY", default="Y", help="Input .json data model file")
parser.add_argument('-lon', dest="LON_KEY", default="X", help="App directory")
parser.add_argument('-precision', dest="PRECISION", default=6, type=int, help="This amount of decimal places")
a = parser.parse_args()
# Parse arguments

datafiles = getFilenames(a.INPUT_FILES)
rows = []
for fn in datafiles:
    _, frows = readCsv(fn)
    rows += frows

multiplier = 10 ** a.PRECISION
for i, row in enumerate(rows):
    lat = row[a.LAT_KEY] if isNumber(row[a.LAT_KEY]) else 0
    lon = row[a.LON_KEY] if isNumber(row[a.LON_KEY]) else 0
    lat = roundInt(lat * multiplier)
    lon = roundInt(lon * multiplier)
    latlonKey = str(lat)+"_"+str(lon)
    rows[i]["_groupBy"] = latlonKey

rowsByLatLon = groupList(rows, "_groupBy")
rowsWithDupes = [group for group in rowsByLatLon if len(group["items"]) > 1]

print(f'{len(rowsWithDupes)} groups with dupes')

for group in rowsWithDupes:
    print(", ".join([str(row[a.ID_KEY]) for row in group["items"]]))
