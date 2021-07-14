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
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input .csv data file")
parser.add_argument('-add', dest="ADD_ENTITIES", default="data/entities_add.csv", help="Input .csv data file that contains entities to add")
parser.add_argument('-props', dest="PROPERTIES", default="Name,Alternate Name,Honorees", help="Comma separated list of properties to look at")
parser.add_argument('-tprops', dest="TEXT_PROPERTIES", default="Text,Description", help="Comma separated list of free-text properties to look at")
parser.add_argument('-types', dest="TYPES", default="PERSON,NORP,ORG,EVENT", help="Comma separated list of entity types to extract: https://spacy.io/api/annotation#named-entities")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/preprocessed/monumentlab_national_monuments_audit_entities.csv", help="Output file")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="If output file exists, overwrite it? (otherwise, it will just be updated with new records)")
parser.add_argument('-update', dest="UPDATE_PROPERTIES", default="", help="If you just want to update specific fields, comma separated list of properties to update")
parser.add_argument('-debug', dest="DEBUG", action="store_true", help="Just output debug details and don't write data?")
a = parser.parse_args()
# Parse arguments

# https://spacy.io/api/annotation#named-entities
# PERSON: People, including fictional.
# NORP:   Nationalities or religious or political groups.
# ORG:    Companies, agencies, institutions, etc.
# EVENT:  Named hurricanes, battles, wars, sports events, etc.

rows = []
if a.DEBUG:
    rows = [
        {"Text": "Andrew Dickson White, 1832-1918, friend and counselor of Ezra Cornell, and with him associated in the founding of the Cornell University, its First President 1865-1885 and for fifty years a member of its government board."},
        {"Name": "Justice John McKinley Federal Building"},
        {"Name": "Horace King"},
        {"Text": "First White House of the Confederacy. .  .  . Designated Executive Residence by the Provisional Confederate Congress February 21, 1861. President Jefferson Davis  and his family lived here until the Confederate Capital moved to Richmond summer 1861. Built by William Sayre 1832-35 at Bibb and  Lee Streets. Moved to present location by the First White House Association and dedicated June 3, 1921."}
    ]
    for i, row in enumerate(rows):
        rows[i]["Id"] = ""
        rows[i]["Source"] = ""
        rows[i]["Vendor Entry ID"] = ""
else:
    fields, rows = readCsv(a.INPUT_FILE)

# exclude merged records
rows = [row for row in rows if "Source" in row and row["Source"] != "Multiple"]

rowCount = len(rows)
PROPERTIES = [{"prop": p.strip(), "type": "name"} for p in a.PROPERTIES.strip().split(",")]
TEXT_PROPERTIES = [{"prop": p.strip(), "type": "text"} for p in a.TEXT_PROPERTIES.strip().split(",")]
props = PROPERTIES + TEXT_PROPERTIES
TYPES = [p.strip() for p in a.TYPES.strip().split(",")]
nlp = en_core_web_sm.load()

updateProperties = set([])
if len(a.UPDATE_PROPERTIES) > 0:
    updateProperties = set([p.strip() for p in a.UPDATE_PROPERTIES.strip().split(",")])

existingEnts = []
if os.path.isfile(a.OUTPUT_FILE) and not a.OVERWRITE:
    _, existingEnts = readCsv(a.OUTPUT_FILE)
    # remove custom entities
    existingEnts = [ent for ent in existingEnts if ent["Is Custom"] < 1]
    if len(updateProperties) > 0:
        existingEnts = [ent for ent in existingEnts if ent["Property"] not in updateProperties] # remove entities with properties that we want to re-process
processedIds = set([ent["Id"] for ent in existingEnts])

addEntities = []
addEntityLookup = {}
if len(a.ADD_ENTITIES) > 0 and os.path.isfile(a.ADD_ENTITIES):
    _, addEntities = readCsv(a.ADD_ENTITIES)
    for i, row in enumerate(addEntities):
        nvalue = normalizeName(row["match"])
        addEntities[i]["nvalue"] = nvalue
        addEntityLookup[nvalue] = row

makeDirectories(a.OUTPUT_FILE)

extractedEntities = []
for i, row in enumerate(rows):
    alreadyProcessed = (row["Id"] in processedIds)
    if alreadyProcessed and len(updateProperties) <= 0:
        printProgress(i+1, rowCount)
        continue

    for prop in props:
        p = prop["prop"]
        if alreadyProcessed and p not in updateProperties:
            continue

        type = prop["type"]
        if p not in row:
            continue
        value = str(row[p]).strip()
        if len(value) < 1:
            continue

        # put names into a sentence format
        if a.LIST_DELIMETER in value and type == "name":
            values = [normalizeName(v.strip()).title() for v in value.split(a.LIST_DELIMETER)]
            value = ", ".join(values)
            value = f'The {p.lower()} are ' + value + '.'
        elif type == "name":
            value = 'The name is ' + normalizeName(value).title() + '.'

        doc = nlp(value)

        if not doc or len(doc.ents) < 1:
            continue

        for ent in doc.ents:
            if ent.label_ in TYPES:
                nvalue = normalizeName(ent.text)
                entType = ent.label_
                entText = ent.text
                # check for custom types
                if nvalue in addEntityLookup:
                    entType = addEntityLookup[nvalue]["type"]
                    entText = addEntityLookup[nvalue]["target"]
                validEnt = {
                    "Id": row["Id"],
                    "Extracted Text": entText,
                    "Type": entType,
                    "Property": p,
                    "Is Custom": 0
                }
                extractedEntities.append(validEnt)

    printProgress(i+1, rowCount)

print("Checking for custom entities...")
# add custom entities
for i, row in enumerate(rows):

    for prop in props:

        if p not in row:
            continue

        value = str(row[p]).strip()
        if len(value) < 1:
            continue

        value = normalizeName(value)

        for ent in addEntities:
            if ent["nvalue"] in value:
                validEnt = {
                    "Id": row["Id"],
                    "Extracted Text": ent["target"],
                    "Type": ent["type"],
                    "Property": p,
                    "Is Custom": 1
                }
                extractedEntities.append(validEnt)

    printProgress(i+1, rowCount)

extractedEntities = existingEnts + extractedEntities

if a.DEBUG:
    showTop = 10
    if len(extractedEntities) > showTop:
        extractedEntities = extractedEntities[:showTop]
    pprint(extractedEntities)
    sys.exit()

writeCsv(a.OUTPUT_FILE, extractedEntities, headings=["Id", "Extracted Text", "Type", "Property", "Is Custom"])
