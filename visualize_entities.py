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
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_entities_resolved.csv", help="Input .csv data file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="app/data/entities.json", help="Output file")
parser.add_argument('-count', dest="MAX_COUNT",  default=1000, type=int, help="How many entities per group?")
parser.add_argument('-probe', dest="PROBE",  default=0, type=int, help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fieldnames, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

validRows = []
for i, row in enumerate(rows):
    type = row["Type"]
    if type == "PERSON" and row["Wikidata Type"] != "human":
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
    groupsByType[i]["groupsByEnt"] = groupsByEnt


# Cols: Wikidata, Wikidata Type, Image, Image Filename, Description, Gender, Birth Date, Occupation, Ethnic Group
makeDirectories([a.OUTPUT_FILE])
entities = {}
for typeGroup in groupsByType:
    typeName = typeGroup["normType"]
    jcols = ["Count", "Name", "Wikidata Type", "Description"]
    jfacets = []
    if typeGroup["normType"] == "PERSON":
        jcols = ["Count", "Name", "Wikidata Type", "Image Filename", "Description", "Gender", "Occupation", "Ethnic Group"]
        jfacets = ["Gender", "Occupation", "Ethnic Group"]
    elif typeGroup == "EVENT":
        jfacets = ["Wikidata Type"]
    jrows = []
    for entGroup in typeGroup["groupsByEnt"]:
        if len(entGroup["items"]) < 1:
            continue
        entity = entGroup["items"][0]
        jrow = [entGroup["count"]]
        for col in jcols:
            if col != "Count":
                jrow.append(entity[col])
        jrows.append(jrow)
    minCount = min([entGroup["count"] for entGroup in typeGroup["groupsByEnt"]])
    maxCount = max([entGroup["count"] for entGroup in typeGroup["groupsByEnt"]])
    entities[typeName] = {
        "cols": jcols,
        "rows": jrows,
        "min": minCount,
        "max": maxCount
    }

jsonOut = {"entities": entities}

if a.PROBE:
    sys.exit()
writeJSON(a.OUTPUT_FILE, jsonOut)
