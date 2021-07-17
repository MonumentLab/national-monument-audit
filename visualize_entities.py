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
parser.add_argument('-in', dest="INPUT_FILE", default="data/preprocessed/monumentlab_national_monuments_audit_entities_resolved.csv", help="Input .csv data file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="app/data/entities.json", help="Output file")
parser.add_argument('-index', dest="INDEX_FILE", default="data/preprocessed/monumentlab_national_monuments_audit_entities_for_indexing.csv", help="Output file .csv for indexing")
parser.add_argument('-summary', dest="SUMMARY_FILE", default="app/data/entities-summary.json", help="Output summary file")
parser.add_argument('-count', dest="MAX_COUNT",  default=5000, type=int, help="How many entities per group?")
parser.add_argument('-probe', dest="PROBE",  default=0, type=int, help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fieldnames, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

validRows = []
for i, row in enumerate(rows):
    type = row["Type"]
    if type == "PERSON" and row["Wikidata Type"] != "human" and row["Is Custom"] != 1:
        continue
    elif row["Wikidata Type"] == "human":
        type = "PERSON"
    row["normType"] = type
    text = row["Normalized Text"]
    ftext = row["Formatted Text"]
    if row["Resolved Text"] != "":
        text = row["Resolved Text"]
        ftext = row["Resolved Text"]
    row["NameGroup"] = text
    row["Name"] = ftext
    validRows.append(row)

groupsByType = groupList(validRows, "normType")
for i, typeGroup in enumerate(groupsByType):
    groupsByEnt = groupList(typeGroup["items"], "NameGroup", sort=True)
    if len(groupsByEnt) > a.MAX_COUNT:
        groupsByEnt = groupsByEnt[:a.MAX_COUNT]
        updatedGroupItems = []
        for entGroup in groupsByEnt:
            updatedGroupItems += entGroup["items"]
        groupsByType[i]["items"] = updatedGroupItems
    groupsByType[i]["groupsByEnt"] = groupsByEnt


# Cols: Wikidata, Wikidata Type, Image, Image Filename, Description, Gender, Birth Date, Occupation, Ethnic Group
entities = {}
for typeGroup in groupsByType:
    typeName = typeGroup["normType"]
    jcols = ["Count", "Name", "Wikidata Type", "Description"]
    jfacets = []
    if typeGroup["normType"] == "PERSON":
        jcols = ["Count", "Name", "Wikidata Type", "Image Filename", "Description", "Gender", "Occupation", "Ethnic Group"]
        jfacets = ["Gender", "Occupation", "Ethnic Group"]
    elif typeGroup["normType"] == "EVENT":
        jfacets = ["Wikidata Type"]

    facetGroups = {}
    facetCounts = {}
    for facet in jfacets:
        facetItems = groupList(typeGroup["items"], facet, sort=True)
        facetGroups[facet] = [item[facet] for item in facetItems]
        facetCounts[facet] = [0 for item in facetItems]

    jrows = []
    for entGroup in typeGroup["groupsByEnt"]:
        if len(entGroup["items"]) < 1:
            continue
        entity = entGroup["items"][0]
        jrow = [entGroup["count"]]
        for col in jcols:
            if col == "Count":
                continue
            if col in facetGroups:
                valueIndex = facetGroups[col].index(entity[col])
                jrow.append(valueIndex)
                facetCounts[col][valueIndex] += 1
            else:
                jrow.append(entity[col])
        jrows.append(jrow)
    minCount = min([entGroup["count"] for entGroup in typeGroup["groupsByEnt"]])
    maxCount = max([entGroup["count"] for entGroup in typeGroup["groupsByEnt"]])

    entities[typeName] = {
        "cols": jcols,
        "rows": jrows,
        "min": minCount,
        "max": maxCount,
        "groups": facetGroups,
        "groupCounts": facetCounts
    }

jsonOut = {"entities": entities}

if a.PROBE:
    sys.exit()

makeDirectories([a.OUTPUT_FILE, a.SUMMARY_FILE, a.INDEX_FILE])
writeJSON(a.OUTPUT_FILE, jsonOut)

################################################################
# Generate pie chart data
################################################################

pieChartData = {}
people = [row for row in validRows if row["normType"] == "PERSON" and row["Wikidata Type"] == "human"]
for property in ["Gender", "Ethnic Group", "Occupation"]:
    pdata = getCountPercentages(people, property, otherTreshhold=5)
    pkey = f'entity-{stringToId(property)}'
    pieChartData[pkey] = {
        "title": property,
        "values": [d["percent"] for d in pdata],
        "labels": [d["value"] for d in pdata]
    }

################################################################
# Generate record value top frequencies
################################################################

entLabels = {
    "PERSON": "People",
    "EVENT": "Events",
    "ORG": "Organizations",
    "NORP": "Nationalities or religious or political groups"
}
showTop = 10
freqData = []
for typeGroup in groupsByType:
    typeName = typeGroup["normType"]
    rowFreqData = []
    for entGroup in typeGroup["groupsByEnt"]:
        if len(entGroup["items"]) < 1:
            continue
        entity = entGroup["items"][0]
        rowFreqData.append([entity["Name"], formatNumber(entGroup["count"])])
        if len(rowFreqData) >= showTop:
            break
    freqData.append({
        "title": f'Top {showTop} values for "{entLabels[typeName]}"',
        "rows": rowFreqData,
        "cols": ["Value", "Count"],
        "resourceLink": f'entities_type_{typeName}.csv'
    })

jsonOut = {}
jsonOut["pieCharts"] = pieChartData
jsonOut["frequencies"] = freqData
writeJSON(a.SUMMARY_FILE, jsonOut)

################################################################
# Generate file for use in indexing
################################################################
indexRows = []
for typeGroup in groupsByType:
    typeName = typeGroup["normType"]
    if typeName not in ("PERSON", "EVENT"):
        continue

    for entGroup in typeGroup["groupsByEnt"]:
        ids = set([])
        for item in entGroup["items"]:
            id = item["Id"]
            if id in ids:
                continue
            ids.add(id)
            indexRows.append({
                "Id": id,
                "Type": typeName,
                "Value": item["Name"],
                "Property": item["Property"],
                "Gender": item["Gender"],
                "Ethnic Group": item["Ethnic Group"]
            })

writeCsv(a.INDEX_FILE, indexRows, headings=["Id", "Type", "Value", "Property", "Gender", "Ethnic Group"])
