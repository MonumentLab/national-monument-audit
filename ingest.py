# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.geo_utils import *
from lib.io_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="config/ingest/*.json", help="Input .json config files")
parser.add_argument('-app', dest="APP_DIRECTORY", default="app/", help="App directory")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Output csv file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

filenames = getFilenames(a.INPUT_FILE)

dataSources = []
for fn in filenames:
    data = readJSON(fn)
    dataSources.append(data)

rowsOut = []
for d in dataSources:
    print(f'Processing {d["name"]}')

    # Read data
    dataPath = d["dataPath"]
    fields = []
    data = []
    if dataPath.endswith(".csv"):
        dataEncoding = d["dataEncoding"] if "dataEncoding" in d else "utf8"
        fields, data = readCsv(dataPath, encoding=dataEncoding)

    if len(data) <= 0:
        print(" No data found, skipping.")
        continue

    mappings = d["mappings"] if "mappings" in d else {}
    firstWarning = True
    for rowIn in data:
        rowOut = {
            "Source": d["name"]
        }
        for prop in d["properties"]:
            if prop not in rowIn:
                if firstWarning:
                    print(f' Warning: "{prop}" property not found')
                    firstWarning = False
                continue

            value = rowIn[prop]
            toProperty = prop
            propMap = mappings[prop] if prop in mappings else {}

            # strip whitespace
            if isinstance(value, str):
                value = value.strip()

            # map this property to another property
            if "to" in propMap:
                toProperty = propMap["to"]

            # check for empty string
            if value == "" and toProperty not in rowOut:
                rowOut[toProperty] = value
                continue

            # parse date, convert to year
            if "dateFormat" in propMap:
                dt = None
                try:
                    dt = datetime.strptime(str(value).strip(), propMap["dateFormat"])
                except ValueError:
                    dt = False
                if not dt:
                    value = ""
                else:
                    value = int(dt.strftime("%Y"))

            # check to see if this is a list
            if "delimeter" in propMap:
                value = [v.strip() for v in re.split(propMap["delimeter"], str(value))]

            # Interpret coordinates as lat lon
            if toProperty == "Coordinates":
                lat = lon = None
                try:
                    lat, lon = tuple([float(v.strip()) for v in str(value).split(",")])
                except ValueError:
                    lat = ""
                    lon = ""
                rowOut["Latitude"] = lat
                rowOut["Longitude"] = lon
                continue

            # Convert UTM to lat lon
            if toProperty == "UTM":
                easting = value
                northing = rowIn[propMap["utmNorthing"]]
                zoneNumber = rowIn[propMap["utmZone"]]
                lat = lon = None

                lat, lon = utmToLatLon(easting, northing, zoneNumber, northern=True)

                rowOut["Latitude"] = lat
                rowOut["Longitude"] = lon
                continue

            # check to see if property is already set; if so, add it as a list
            if toProperty in rowOut:
                existingValue = rowOut[toProperty]
                if not isinstance(value, list):
                    value = [value]
                if not isinstance(existingValue, list):
                    existingValue = [existingValue]
                rowOut[toProperty] = existingValue + value
            else:
                rowOut[toProperty] = value
        rowsOut.append(rowOut)


makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, rowsOut, listDelimeter=a.LIST_DELIMETER)
