# -*- coding: utf-8 -*-

import argparse
from collections import Counter
import en_core_web_sm
import os
from pprint import pprint
import spacy
from spacy import displacy
import sys

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_entities_normalized.csv", help="Input .csv data file")
parser.add_argument('-filter', dest="FILTER", default="Type=PERSON OR Type=EVENT", help="Filter query")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_entities_resolved.csv", help="Output file")
parser.add_argument('-stats', dest="STATS_OUTPUT_FILE", default="tmp/resolved_entities.csv", help="Output stats file pattern")
parser.add_argument('-wdir', dest="WIKI_DATA_DIR", default="data/wikidata/", help="Output directory for storing wikidata responses")
parser.add_argument('-count', dest="MINIMUM_COUNT",  default=10, type=int, help="Resolve if count above this number?")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite data files if they exist")
parser.add_argument('-debug', dest="DEBUG", action="store_true", help="Use test data")
parser.add_argument('-probe', dest="PROBE",  default=0, type=int, help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

rows = []
fieldnames = []

if a.DEBUG:
    rows = [
        {"Normalized Text": "Martin Luther King", "Type": "PERSON"},
        {"Normalized Text": "Booker T. Washington", "Type": "PERSON"}
    ]
else:
    fieldnames, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

# add indices
for i, row in enumerate(rows):
    rows[i]["index"] = i
filteredRows = rows[:]

if len(a.FILTER) > 0:
    print("  Filtering data...")
    filteredRows = filterByQueryString(rows, a.FILTER)
    rowCount = len(filteredRows)
    print(f'  {rowCount} rows after filtering')

groups = groupList(filteredRows, "Normalized Text", sort=True)
if a.MINIMUM_COUNT > 0 and not a.DEBUG:
    groups = [g for g in groups if g["count"] >= a.MINIMUM_COUNT]

wikiSearchDir = a.WIKI_DATA_DIR + "search/"
wikiEntDir = a.WIKI_DATA_DIR + "entities/"
makeDirectories([a.OUTPUT_FILE, a.STATS_OUTPUT_FILE, wikiSearchDir, wikiEntDir])

wikidataCache = {}

def getEntityFromId(wikidataId):
    global wikidataCache
    global wikiEntDir
    global a
    if wikidataId in wikidataCache:
        return wikidataCache[wikidataId]
    entityUrl = f'https://www.wikidata.org/wiki/Special:EntityData/{wikidataId}.json'
    entityFilename = wikiEntDir + f'{wikidataId}.json'
    ent = downloadJSONFromURL(entityUrl, entityFilename, overwrite=a.OVERWRITE)
    wikidataCache[wikidataId] = ent
    return ent

def getEntityLabel(resp, wikidataId):
    if not resp or "entities" not in resp or wikidataId not in resp["entities"]:
        return ""
    entity = resp["entities"][wikidataId]
    if "labels" not in entity or "en" not in entity["labels"] or "value" not in entity["labels"]["en"]:
        return ""
    return entity["labels"]["en"]["value"]

def getClaimValue(claims, claimId):
    value = ""
    if claimId not in claims:
        return value
    claim = claims[claimId]
    if len(claim) < 1:
        return value
    claim = claim[0]
    if "mainsnak" not in claim:
        return value
    claim = claim["mainsnak"]
    if "datavalue" not in claim:
        return value
    claim = claim["datavalue"]
    if "value" in claim:
        value = claim["value"]
    if not isinstance(value, str) and "id" in value:
        entId = value["id"]
        if len(entId) > 0:
            ent = getEntityFromId(entId)
            value = getEntityLabel(ent, entId)
    elif not isinstance(value, str) and "time" in value:
        value = value["time"]
    return value

groupedRows = []
groupCount = len(groups)
for i, group in enumerate(groups):
    ntext = str(group["Normalized Text"]).strip()
    if len(ntext) < 1:
        continue

    rowOut = {}
    rowOut["Count"] = group["count"]
    rowOut["Normalized Text"] = ntext
    rowOut["Resolved Text"] = ""
    rowOut["Wikidata"] = ""
    rowOut["Wikidata Type"] = ""
    rowOut["Image"] = ""
    rowOut["Image Filename"] = ""
    rowOut["Description"] = ""
    rowOut["Gender"] = "NA"
    rowOut["Birth Date"] = "NA"
    rowOut["Occupation"] = "NA"
    rowOut["Ethnic Group"] = "NA"
    rowOut["Date"] = "NA"

    groupType = group["items"][0]["Type"]
    qString = urlEncodeString(ntext)
    searchUrl = f'https://www.wikidata.org/w/api.php?action=wbsearchentities&search={qString}&language=en&format=json'
    searchFilename = wikiSearchDir + stringToId(ntext) + ".json"
    response = downloadJSONFromURL(searchUrl, searchFilename, overwrite=a.OVERWRITE)
    foundValid = False

    if response and "search" in response and len(response["search"]) > 0:

        for j, respRow in enumerate(response["search"]):

            if foundValid or j > 1:
                break

            if j == 1:
                print(f"   Looking for the next entry for {ntext}...")

            if respRow and "match" in respRow and "id" in respRow and "text" in respRow["match"] and not foundValid:
                rtext = respRow["match"]["text"]
                wikidataId = respRow["id"]
                description = ""
                entResp = getEntityFromId(wikidataId)
                if entResp and "entities" in entResp and wikidataId in entResp["entities"] and entResp["entities"][wikidataId]:
                    entity = entResp["entities"][wikidataId]

                    # retrieve description
                    if "descriptions" in entity and "en" in entity["descriptions"] and "value" in entity["descriptions"]["en"]:
                        description = normalizeWhitespace(entity["descriptions"]["en"]["value"])

                    if "claims" in entity:
                        claims = entity["claims"]

                        # check for type
                        rowOut["Wikidata Type"] = getClaimValue(claims, "P31")
                        isValidType = (groupType == "PERSON" and rowOut["Wikidata Type"] in ("human") or groupType != "PERSON")

                        if isValidType or j < 1:
                            rowOut["Resolved Text"] = rtext
                            rowOut["Wikidata"] = wikidataId
                            rowOut["Description"] = description
                        else:
                            continue

                        # check for image
                        image = getClaimValue(claims, "P18")
                        if len(image) > 0:
                            imageFn = urlEncodeString(image.replace(' ', '_'))
                            rowOut["Image"] = f'https://commons.wikimedia.org/w/thumb.php?width=256&f={imageFn}'
                            rowOut["Image Filename"] = imageFn
                            # https://stackoverflow.com/questions/34393884/how-to-get-image-url-property-from-wikidata-item-by-api
                            # hash = md5string(imageFn)
                            # a = hash[:1]
                            # ab = hash[:2]
                            # wikidataImage = f'https://upload.wikimedia.org/wikipedia/commons/{a}/{ab}/{imageFn}'

                        # get human-specific data
                        if rowOut["Wikidata Type"] == "human":
                            rowOut["Gender"] = getClaimValue(claims, "P21")
                            rowOut["Birth Date"] = getClaimValue(claims, "P569")
                            rowOut["Occupation"]  = getClaimValue(claims, "P106")
                            rowOut["Ethnic Group"] = getClaimValue(claims, "P172")

                        else:
                            rowOut["Date"] = getClaimValue(claims, "P585")

                        if isValidType:
                            foundValid = True

    groups[i]["data"] = rowOut
    groupedRows.append(rowOut)
    printProgress(i+1, groupCount, "  ")

if a.DEBUG:
    pprint(groupedRows)
    sys.exit()

if a.PROBE > 0:
    lim = a.PROBE
    if len(groupedRows) > lim:
        groupedRows = groupedRows[:lim]
    pprint(groupedRows)
    sys.exit()

# pprint(groupedRows)
def sorter(row):
    if row["Wikidata Type"] == "human":
        return "aaa"
    elif len(row["Wikidata Type"]) < 1:
        return "zzz"
    else:
        return row["Wikidata Type"]
groupedRows = sorted(groupedRows, key=sorter)
writeCsv(a.STATS_OUTPUT_FILE, groupedRows)

# Update original rows
for i, group in enumerate(groups):
    for row in group["items"]:
        index = row["index"]
        for key, value in group["data"].items():
            if key not in ("Count", "Normalized Text"):
                if key not in fieldnames:
                    fieldnames.append(key)
                rows[index][key] = value
writeCsv(a.OUTPUT_FILE, rows, headings=fieldnames)
