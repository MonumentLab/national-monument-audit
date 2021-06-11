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
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/si/sos_data.csv", help="Input file")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-county', dest="COUNTIES_GEO_FILE", default="app/data/counties.json", help="County geojson file (generated from make_boundaries.py)")
parser.add_argument('-countycache', dest="COUNTIES_CACHE_FILE", default="data/preprocessed/counties_matched.csv", help="Cached csv file for storing lat/lon matched against county data")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/si/sos_data_location_fixed.csv", help="Output file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
parser.add_argument('-verbose', dest="VERBOSE", action="store_true", help="Output all details?")
a = parser.parse_args()

OUTPUT_FILE = a.OUTPUT_FILE if len(a.OUTPUT_FILE) > 0 else a.INPUT_FILE

makeDirectories(OUTPUT_FILE)

fieldNames, rows = readCsv(a.INPUT_FILE)
# rows = addIndices(rows, keyName="_index")
rowCount = len(rows)

stateMap = getStates()
states = [{"text": stateString, "abbrev": stateKey} for stateString, stateKey in stateMap.items()]
states = sorted(states, key=lambda state: -len(state["text"]))

for i, row in enumerate(rows):
    locations = str(row["Owner/Location"])
    locations = [v.strip().strip(a.LIST_DELIMETER).strip() for v in locations.split(a.LIST_DELIMETER)]
    places = str(row["Place"]).strip()
    if len(places) > 0:
        places = [v.strip().strip(a.LIST_DELIMETER).strip() for v in places.split(a.LIST_DELIMETER)]
        locations += places
    locations = [v for v in locations if len(v) > 0]
    originalState = row["State"]

    if len(locations) < 1:
        print(f'  No location set for: {row["Url"]}')
        continue

    locations = sorted(locations, key=lambda loc: 1 if loc.startswith("Located") else 2) # prefer strings starting with "Located"

    foundState = False
    for location in locations:

        loc = location.lower()
        if "accession number" in loc:
            loc = loc.split("accession number")[0]
        # remove non-alpha
        loc = re.sub('[^a-z ]+', '', loc)
        loc = loc.strip()
        for state in states:
            stateString, stateKey = (state["text"], state["abbrev"])
            if loc.endswith(stateString.lower()):
                if originalState != stateKey:
                    if a.VERBOSE:
                        print(f'"{location}" originally marked as {originalState} but should be {stateKey}: {row["Url"]}')
                    rows[i]["State"] = stateKey
                foundState = True
                break
        if foundState:
            break

    # if not in location, look in notes and topics
    if not foundState:
        notes = [n.strip().lower() for n in row["Notes"].split(",")]
        if row["Topic"] != "":
            notes += [v.strip().strip(a.LIST_DELIMETER).strip().lower() for v in row["Topic"].split(a.LIST_DELIMETER)]
        # e.g. Look in note: "Save Outdoor Sculpture, California survey, 1995."
        for note in notes:
            for state in states:
                stateString, stateKey = (state["text"], state["abbrev"])
                stateString = stateString.lower()
                if note == stateString or "survey" in note and note.startswith(stateString) or "--" in note and note.endswith(stateString) or note.startswith("state of ") and note.endswith(stateString):
                    if originalState != stateKey:
                        if a.VERBOSE:
                            print(f'"{location}" originally marked as {originalState} but should be {stateKey}: {row["Url"]}')
                        rows[i]["State"] = stateKey
                    foundState = True
                    break
            if foundState:
                break

    if not foundState:
        print(f'  Could not find state for {locations[0]} / {row["Url"]}')

    printProgress(i+1, rowCount)

print("Matching lat/lon data against county data...")
_, latlonCountyMatches = readCsv(a.COUNTIES_CACHE_FILE, doParseNumbers=False)
latlonCountyLookup = createLookup(latlonCountyMatches, "latlon")
countyGeoJSON = readJSON(a.COUNTIES_GEO_FILE)
# create a state lookup for county data
countyStateLookup = {}
for feature in countyGeoJSON["features"]:
    geoId = str(feature["properties"]["GEOID"])
    state = fipsToState(str(feature["properties"]["STATEFP"]), defaultValue="")
    countyStateLookup[geoId] = state
for i, row in enumerate(rows):
    countyGeoId = "Unknown"

    if not isNumber(row["Latitude"]) or not isNumber(row["Longitude"]) or row["Latitude"] <= 0:
        continue

    latlon = f'{row["Latitude"]},{row["Longitude"]}'
    if latlon in latlonCountyLookup:
        countyGeoId = latlonCountyLookup[latlon]["countyGeoId"]
    else:
        matchedFeature = searchPointInGeoJSON(row["Latitude"], row["Longitude"], countyGeoJSON)
        if matchedFeature is not None:
            countyGeoId = str(matchedFeature["properties"]["GEOID"])
            countyLookupChanged = True
        latlonCountyLookup[latlon] = {"countyGeoId": countyGeoId}
        # saveCountyDataCache(a.COUNTIES_CACHE_FILE, latlonCountyLookup)
    if countyGeoId == "Unknown":
        continue
    # validate state
    geoState = countyStateLookup[countyGeoId] if countyGeoId in countyStateLookup else ""
    originalState = row["State"] if "State" in row else ""
    if geoState == "":
        continue

    # set state if not already set
    if originalState != geoState:
        print(f' Changing state for {row["Id"]} / {row["Url"]}: {geoState} (was {originalState})')
        rows[i]["State"] = geoState

if a.PROBE:
    sys.exit()

writeCsv(OUTPUT_FILE, rows, headings=fieldNames)
print("Done.")
