# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input .csv data file")
# parser.add_argument('-entities', dest="ENTITIES_FILE", default="data/compiled/monumentlab_national_monuments_audit_entities_for_indexing.csv", help="Input entities .csv data file")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter string")
parser.add_argument('-config', dest="CONFIG_FILE", default="config/data-model.json", help="Input config .json file")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_DIR", default="search-index/documents-latest/", help="Output directory")
parser.add_argument('-backup', dest="BACKUP_DIR", default="search-index/backup-%Y-%m-%d-%H-%M/", help="Output backup directory")
parser.add_argument('-prev', dest="PREV_DIR", default="", help="Optional previous directory of .json documents for determining deletions")
parser.add_argument('-batchsize', dest="DOCS_PER_BATCH", default=1800, type=int, help="Documents per batch")
parser.add_argument('-maxsize', dest="MAX_FILE_SIZE_MB", default=5, type=float, help="Max file size in megabytes")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fields, rows = readCsv(a.INPUT_FILE)
dataModel = readJSON(a.CONFIG_FILE)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

# entFields, entRows = readCsv(a.ENTITIES_FILE)
# entLookup = {}
# if len(entRows) > 0:
#     for i, entRow in enumerate(entRows):
#         entRows[i]["idString"] = str(entRow["Id"])
#     entById = groupList(entRows, "idString")
#     entLookup = createLookup(entById, "idString")
# else:
#     print("Warning: no entities file found; run `visualize_entities.py` to generate this")

# write a sample record for index config purposes
sampleDoc = {
    "id": "unique-id-123",
    "fields": {},
    "type": "add"
}
for field in dataModel["fields"]:
    key = field["key"]
    search_key = stringToId(key)
    type = field["type"]

    if search_key == "url":
        value = "http://example.com/"
    elif "year" in search_key and type == "int":
        value = 2000
    elif search_key == "latitude":
        search_key = "latlon"
        value = "40.730610, -73.935242"
    elif search_key == "longitude":
        continue
    elif type == "string":
        value = "Short text"
    elif type == "text":
        value = "Long text"
    elif type == "int":
        value = 10
    elif type == "float":
        value = 3.1459
    elif type == "string_list":
        value = ["Short text 1", "Short text 2", "Short text 3"]

    sampleDoc["fields"][search_key] = value

writeJSON("tmp/sampleSearchDocument.json", [sampleDoc], pretty=True)

if not a.PROBE:
    makeDirectories(a.OUTPUT_DIR)
    removeFiles(a.OUTPUT_DIR + "*.json")

batchCount = ceilInt(1.0 * len(rows) / a.DOCS_PER_BATCH)
invalidCount = 0
currentBatchIndex = 0
currentBatch = []
newIds = []
for i, row in enumerate(rows):
    docFields = {}
    isValid = True

    docId = str(row["Id"])
    if len(docId) < 1:
        invalidCount += 1
        print(f'Warning: no valid ID for row {(i+1)}')
        continue

    # Moved this logic to ingest.py
    ## Add entities
    # if docId in entLookup:
    #     rowEnts = entLookup[docId]["items"]
    #     eventEnts = []
    #     peopleEnts = []
    #     for ent in rowEnts:
    #         value = str(ent["Value"]).strip()
    #         if len(value) < 1:
    #             continue
    #         if ent["Type"] == "EVENT" and value not in eventEnts:
    #             eventEnts.append(value)
    #         elif ent["Type"] == "PERSON" and value not in peopleEnts:
    #             peopleEnts.append(value)
    #
    #     if len(eventEnts) > 0:
    #         row["Entities Events"] = a.LIST_DELIMETER.join(eventEnts)
    #
    #     if len(peopleEnts) > 0:
    #         row["Entities People"] = a.LIST_DELIMETER.join(peopleEnts)

    for field in dataModel["fields"]:
        key = field["key"]
        search_key = stringToId(key)
        type = field["type"]
        required = ("required" in field and field["required"])
        isFacetAndSearch = ("facetAndSearch" in field and field["facetAndSearch"])
        if key not in row:
            if i < 1:
                print(f'Warning: no key {key}')
            continue
        value = row[key]

        if type == "string" or type == "text":
            value = str(value).strip()
            if len(value) < 1 and not required:
                continue

            if type == "text":
                value = cleanText(value)

        elif type == "int":
            value = parseInt(value)
            if not isNumber(value) and not required:
                continue

        elif type == "float":
            value = parseFloat(value)
            if not isNumber(value) and not required:
                continue

        elif type == "string_list":
            value = str(value)
            value = [v.strip() for v in value.split(a.LIST_DELIMETER)]
            value = [v for v in value if len(v) > 0]
            if len(value) < 1 and not required:
                continue

        if value == "":
            print(f'Warning: {key} is required, but no value found for row {(i+1)}')
            isValid = False
            continue

        docFields[search_key] = value
        # replicate field for separate free text search indexing
        # (in CloudSearch, a single field cannot be both free text search and faceted)
        if isFacetAndSearch:
            docFields[search_key+"_search"] = value

    if not isValid:
        invalidCount += 1
        continue

    # reformat lat lon
    if "latitude" in docFields and "longitude" in docFields:
        if isNumber(docFields["latitude"]) and docFields["latitude"] > 0:
            docFields["latlon"] = f'{docFields["latitude"]}, {docFields["longitude"]}'
        docFields.pop("latitude", None)
        docFields.pop("longitude", None)

    elif "latitude" in docFields:
        docFields.pop("latitude", None)

    elif "longitude" in docFields:
        docFields.pop("longitude", None)

    doc = {
        "type": "add",
        "id": docId,
        "fields": docFields
    }
    newIds.append(docId)
    currentBatch.append(doc)
    if len(currentBatch) >= a.DOCS_PER_BATCH and not a.PROBE:
        batchname = f'{a.OUTPUT_DIR}batch_{padNum(currentBatchIndex, batchCount)}.json'
        writeJSON(batchname, currentBatch)
        currentBatch = []
        currentBatchIndex += 1

if len(currentBatch) >= 0 and not a.PROBE:
    batchname = f'{a.OUTPUT_DIR}batch_{padNum(currentBatchIndex, batchCount)}.json'
    writeJSON(batchname, currentBatch)

print(f'{invalidCount} invalid records')

if len(a.PREV_DIR) > 0:
    print("Checking for deletions...")
    prevFilenames = getFilenames(a.PREV_DIR + "*.json", verbose=True)
    prevIds = []
    for fn in prevFilenames:
        batch = readJSON(fn)
        for row in batch:
            if "type" in row and row["type"] == "add" and "id" in row:
                prevIds.append(row["id"])

    deleteIds = list(set(prevIds).difference(newIds))

    if len(deleteIds) > 0:
        print(f'Deleting {len(deleteIds)} records')
        docsPerBatch = a.DOCS_PER_BATCH * 10
        currentBatch = []
        currentBatchIndex = 0
        batchCount = ceilInt(1.0 * len(deleteIds) / docsPerBatch)
        for id in deleteIds:
            currentBatch.append({
                "type": "delete",
                "id": id
            })
            if len(currentBatch) >= docsPerBatch and not a.PROBE:
                batchname = f'{a.OUTPUT_DIR}_batch_deletions_{padNum(currentBatchIndex, batchCount)}.json'
                writeJSON(batchname, currentBatch)
                currentBatch = []
                currentBatchIndex += 1
        if len(currentBatch) >= 0 and not a.PROBE:
            batchname = f'{a.OUTPUT_DIR}_batch_deletions_{padNum(currentBatchIndex, batchCount)}.json'
            writeJSON(batchname, currentBatch)

# validate batch sizes
if a.MAX_FILE_SIZE_MB > 0:
    filenames = getFilenames(a.OUTPUT_DIR + "*.json")
    for fn in filenames:
        filesize = os.path.getsize(fn) / 1000.0 / 1000.0
        if filesize >= a.MAX_FILE_SIZE_MB:
            print(f'ERROR: {fn} is too large ({filesize}MB > {a.MAX_FILE_SIZE_MB}MB). Re-run with a lower -batchsize parameter (currently {a.DOCS_PER_BATCH})')
            sys.exit()

# create a backup based on this date and time
now = datetime.now()
backupDir = now.strftime(a.BACKUP_DIR)
removeDir(backupDir)
copyDir(a.OUTPUT_DIR, backupDir)
