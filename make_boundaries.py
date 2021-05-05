# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import sys

from lib.geo_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-out', dest="OUTPUT_FILE", default="app/data/counties.json", help="Output geojson file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

countyData = readJSON("data/boundaries/census/cb_2018_us_county_20m.geo.json")
congressionalData = readJSON("data/boundaries/census/cb_2018_us_county_within_cd116_500k_simplified.geo.json") # because county data does not include most territories

featuresOut = []
ids = set([])
stateIds = set([])

for feature in countyData["features"]:
    props = feature["properties"]
    # validate ID
    if props["GEOID"] in ids:
        print(f' **Warning: duplicate ID {props["GEOID"]}')
    else:
        ids.add(props["GEOID"])

    # convert and track states
    stateId = fipsToState(props["STATEFP"], defaultValue=None)
    if stateId is None:
        print(f' **Warning: invalid state FIPS {props["STATEFP"]}')
        continue

    if stateId not in stateIds:
        stateIds.add(stateId)

    featuresOut.append(feature)

print("Finished processing counties.")

# now look for territories not represented in the county set
for feature in congressionalData["features"]:
    props = feature["properties"]

    # convert and check states
    stateId = fipsToState(props["STATEFP"], defaultValue=None)
    if stateId is None:
        print(f' **Warning: invalid state FIPS {props["STATEFP"]}')
        continue

    # if state already represented, continue
    if stateId in stateIds:
        continue

    # validate ID
    if props["GEOID"] in ids:
        print(f' **Warning: duplicate ID {props["GEOID"]}')
    else:
        ids.add(props["GEOID"])

    stateName = codeToState(stateId)
    feature["properties"]["NAME"] = stateName
    print(f' Found territory: {feature["properties"]["NAME"]}')
    feature["properties"].pop("CD116FP", None)
    featuresOut.append(feature)

print("Finished processing territories.")

if a.PROBE:
    sys.exit()

makeDirectories(a.OUTPUT_FILE)

jsonOut = {
    "type": "FeatureCollection",
    "name": "census_2018_county_boundaries_with_territories",
    "crs": countyData["crs"],
    "features": featuresOut
}
writeJSON(a.OUTPUT_FILE, jsonOut)
print("Done.")
