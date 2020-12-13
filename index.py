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
parser.add_argument('-config', dest="CONFIG_FILE", default="config/data-model.json", help="Input config .json file")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_DIR", default="search-index/documents/", help="Output directory")
parser.add_argument('-batchsize', dest="DOCS_PER_BATCH", default=4000, type=int, help="Documents per batch")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fields, rows = readCsv(a.INPUT_FILE)
dataModel = readJSON(a.CONFIG_FILE)

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
for i, row in enumerate(rows):
    docFields = {}
    docId = ""
    isValid = True
    for field in dataModel["fields"]:
        key = field["key"]
        search_key = stringToId(key)
        type = field["type"]
        required = ("required" in field and field["required"])
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

        if key == "Vendor Entry ID":
            docId = stringToId(row["Source"]) + "_" + value

        docFields[search_key] = value

    if len(docId) < 1:
        invalidCount += 1
        print(f'Warning: no valid ID for row {(i+1)}')
        continue

    if not isValid:
        invalidCount += 1
        continue

    # reformat lat lon
    if "latitude" in docFields and "longitude" in docFields:
        docFields["latlon"] = f'{docFields["latitude"]}, {docFields["latitude"]}'
        docFields.pop("latitude", None)
        docFields.pop("longitude", None)

    doc = {
        "type": "add",
        "id": docId,
        "fields": docFields
    }
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
