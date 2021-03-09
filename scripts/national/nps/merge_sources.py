# -*- coding: utf-8 -*-

import argparse
import inspect
import os
from pprint import pprint
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
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/nps/nps_nrhp_combined.csv", help="Where to store merged data")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()

files = [
    {
        "filename": "data/vendor/national/nps/NPS_-_National_Register_of_Historic_Places_Locations-shp.csv",
        "id": "NRIS_Refnu",
        "columns": {
            "X": "X",
            "Y": "Y",
            "NRIS_Refnu": "NRIS_Refnu",
            "RESNAME": "RESNAME",
            "ResType": "ResType",
            "Address": "Address",
            "City": "City",
            "County": "County",
            "State": "State",
            "Listed_Dat": "Listed_Dat",
            "NARA_URL": "NARA_URL"
        }
    },{
        "filename": "data/vendor/national/nps/national_register_listed_20210214.csv",
        "id": "Ref#",
        "columns": {
            "Ref#": "NRIS_Refnu",
            "Property Name": "RESNAME",
            "Category of Property": "ResType",
            "Street & Number": "Address",
            "City": "City",
            "County": "County",
            "State": "State",
            "Listed Date": "Listed_Dat",
            "External Link": "NARA_URL"
        }
    },{
        "filename": "data/vendor/wv/nationalRegisterOfHistoricPlacesPoints_natoinalPakrService_200404.csv",
        "id": "REFNUM",
        "columns": {
            "REFNUM": "NRIS_Refnu",
            "RESNAME": "RESNAME",
            "ADDRESS": "Address",
            "CITY": "City",
            "COUNTY": "County",
            "STATE": "State",
            "LISTED_DAT": "Listed_Dat"
        }
    },{
        "filename": "data/vendor/mt/Montana National Register of Historic Places.csv",
        "id": "NR_Referen",
        "State": "MT",
        "columns": {
            "NR_Referen": "NRIS_Refnu",
            "Name": "RESNAME",
            "Street_Add": "Address",
            "City": "City",
            "County": "County",
            "X": "X",
            "Y": "Y",
            "Type": "ResType",
            "Nomination": "NARA_URL"
        }
    }
]

ids = set([])
mergedRows = []
fieldsOut = ["Sourcefile"]
for f in files:
    fields, rows = readCsv(f["filename"])
    newEntries = 0
    for row in rows:
        id = str(row[f["id"]]).strip()
        if len(id) < 1:
            continue

        if id in ids:
            continue

        ids.add(id)
        newEntries += 1
        newRow = {
            "Sourcefile": getBasename(f["filename"])
        }
        for colFrom, colTo in f["columns"].items():
            newRow[colTo] = row[colFrom]
            if colTo not in fieldsOut:
                fieldsOut.append(colTo)
        mergedRows.append(newRow)
    print(f' {newEntries} new entries found.')

if a.PROBE:
    sys.exit()

makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, mergedRows, headings=fieldsOut)
