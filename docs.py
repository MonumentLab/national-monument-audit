# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input csv file")
parser.add_argument('-config', dest="CONFIG_FILES", default="config/ingest/*.json", help="Input .json config files")
parser.add_argument('-model', dest="DATA_MODEL_FILE", default="config/data-model.json", help="Input .json data model file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="app/data/docs.json", help="Output file")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
a = parser.parse_args()


fields, rows = readCsv(a.INPUT_FILE, doParseLists=True, listDelimeter=a.LIST_DELIMETER)

configFiles = getFilenames(a.CONFIG_FILES)
dataSources = []
for fn in configFiles:
    data = readJSON(fn)
    data["configFile"] = fn.replace("\\", "/")
    if "isDisabled" in data and data["isDisabled"]:
        continue
    dataSources.append(data)

dataModel = readJSON(a.DATA_MODEL_FILE)

rowsWithoutMergedRecords = [row for row in rows if "Has Duplicates" not in row or not isInt(row["Has Duplicates"]) or row["Has Duplicates"] < 1]
rowsWithoutDupes = [row for row in rows if "Is Duplicate" not in row or not isInt(row["Has Duplicates"]) or row["Is Duplicate"] < 1]
duplicateRows = [row for row in rows if "Is Duplicate" in row and isInt(row["Is Duplicate"]) and row["Is Duplicate"] == 1]
monumentRows = [row for row in rowsWithoutMergedRecords if "Object Groups" in row and "Monument" in row["Object Groups"]]

jsonVars = {}
jsonVars["dataSourceTotal"] = formatNumber(len(dataSources))
jsonVars["dataRecordTotal"] = formatNumber(len(rowsWithoutMergedRecords))
jsonVars["dataUniqueRecordTotal"] = formatNumber(len(rowsWithoutDupes))
jsonVars["dataDuplicateRecordTotal"] = formatNumber(len(rowsWithoutMergedRecords)-len(rowsWithoutDupes))
jsonVars["totalMonuments"] = formatNumber(len(monumentRows))
jsonVars["percentMonuments"] = round(1.0 * len(monumentRows) / len(rowsWithoutMergedRecords) * 100, 2)

for i, d in enumerate(dataSources):
    sourceRecords = [row for row in monumentRows if row["Vendor ID"] == d["id"]]
    sourceCount = len(sourceRecords)
    dataSources[i]["recordCount"] = sourceCount
    dataSources[i]["percentOfTotal"] = round(1.0 * sourceCount / len(monumentRows) * 100, 3)

    sourceRecords = [row for row in rowsWithoutMergedRecords if row["Vendor ID"] == d["id"]]
    sourceCount = len(sourceRecords)
    dataSources[i]["recordCountBeforeFiltering"] = sourceCount
    dataSources[i]["percentOfTotalBeforeFiltering"] = round(1.0 * sourceCount / len(rowsWithoutMergedRecords) * 100, 3)
dataSources = sorted(dataSources, key=lambda s: s["recordCount"], reverse=True)

jsonCharts = {}
# Data Sources / Share of records, pre-study set (before excluding non-monument data records)
result = getCountPercentages(rowsWithoutMergedRecords, "Source", otherTreshhold=10)
jsonCharts['data-sources-share-prestudy'] = {
    "title": "Share of all records (including non-monuments) by data source",
    "data": result
}

# Data Sources / Share of records, study set (monument data records only)
result = getCountPercentages(monumentRows, "Source", otherTreshhold=10)
jsonCharts['data-sources-share-study'] = {
    "title": "Share of records in study set (monuments only) by data source",
    "data": result
}

# Geospatial type
result = getCountPercentages(monumentRows, "Geo Type")
jsonCharts['geo-latlon-by-type'] = {
    "title": "Share of records by geospatial type",
    "data": result
}

# Dates available
result = []
for key in ["Year Dedicated Or Constructed", "Year Constructed", "Year Dedicated", "Year Listed", "Year Removed"]:
    kresult = getCountPercentages(monumentRows, key, presence=True)
    yesResult = kresult[0]
    result.append({
        "percent": yesResult["percent"],
        "count": yesResult["count"],
        "value": f'{key} Available?'
    })
jsonCharts['dates-availability'] = {
    "title": "Share of records by date availability",
    "data": result
}

# Data source object type availability
result = getCountPercentages(monumentRows, "Object Types", presence=True)
jsonCharts['object-types-availability'] = {
    "title": "Records that have object type available",
    "data": result
}

# Object types (before normalization)
result = getCountPercentages(rowsWithoutMergedRecords, "Object Types", otherTreshhold=20, excludeEmpty=True)
jsonCharts['object-types-by-type'] = {
    "title": "Object types (before normalization)",
    "data": result
}

# Object groups (after normalization)
result = getCountPercentages(rowsWithoutMergedRecords, "Object Groups")
jsonCharts['object-groups-by-type'] = {
    "title": "Object groups (after normalization)",
    "data": result
}

# Data source honorees availability
result = getCountPercentages(monumentRows, "Honorees", presence=True)
jsonCharts['honorees-availability'] = {
    "title": "Records that have honorees available",
    "data": result
}

# Top people entities
result = getCountPercentages(monumentRows, "Entities People", otherTreshhold=30, excludeEmpty=True)
jsonCharts['top-entities-people'] = {
    "title": "Top PERSON entities",
    "data": result
}

# Top events entities
result = getCountPercentages(monumentRows, "Entities Events", otherTreshhold=30, excludeEmpty=True)
jsonCharts['top-entities-events'] = {
    "title": "Top EVENT entities",
    "data": result
}

# Data source text availability
result = getCountPercentages(monumentRows, "Text", presence=True)
jsonCharts['text-availability'] = {
    "title": "Records that have plaque or marker text available",
    "data": result
}

# Data source subjects availability
result = getCountPercentages(monumentRows, "Subjects", presence=True)
jsonCharts['subjects-availability'] = {
    "title": "Records that have subjects available",
    "data": result
}

# Availabilities
result = []
for key in ["Creators", "Sponsors", "Status", "Image"]:
    kresult = getCountPercentages(monumentRows, key, presence=True)
    yesResult = kresult[0]
    result.append({
        "percent": yesResult["percent"],
        "count": yesResult["count"],
        "value": f'{key} Available?'
    })
jsonCharts['misc-availability'] = {
    "title": "Availability of various fields",
    "data": result
}

# Duplications
result = getCountPercentages(monumentRows, "Is Duplicate", presence=True)
for i, d in enumerate(result):
    result[i]["value"] = "Is Duplicate" if d["value"]=="yes" else "Is unique"
jsonCharts['duplication-breakdown'] = {
    "title": "Record duplication",
    "data": result
}

jsonOut = {
    "stats": jsonVars,
    "sources": dataSources,
    "charts": jsonCharts
}

writeJSON(a.OUTPUT_FILE, jsonOut)
