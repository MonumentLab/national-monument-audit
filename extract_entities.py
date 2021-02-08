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
parser.add_argument('-props', dest="PROPERTIES", default="Name,Alternate Name,Honorees", help="Comma separated list of properties to look at")
parser.add_argument('-tprops', dest="TEXT_PROPERTIES", default="Text,Description", help="Comma separated list of free-text properties to look at")
parser.add_argument('-types', dest="TYPES", default="PERSON,NORP,ORG,EVENT", help="Comma separated list of entity types to extract: https://spacy.io/api/annotation#named-entities")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_entities.csv", help="Output file")
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
        rows[i]["Source"] = ""
        rows[i]["Vendor Entry ID"] = ""
else:
    fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)
PROPERTIES = [{"prop": p.strip(), "type": "name"} for p in a.PROPERTIES.strip().split(",")]
TEXT_PROPERTIES = [{"prop": p.strip(), "type": "text"} for p in a.TEXT_PROPERTIES.strip().split(",")]
props = PROPERTIES + TEXT_PROPERTIES
TYPES = [p.strip() for p in a.TYPES.strip().split(",")]
nlp = en_core_web_sm.load()

makeDirectories(a.OUTPUT_FILE)

extractedEntities = []
for i, row in enumerate(rows):
    for prop in props:
        p = prop["prop"]
        type = prop["type"]
        if p not in row:
            continue
        value = str(row[p]).strip()
        if len(value) < 1:
            continue

        # put names into a sentence format
        if a.LIST_DELIMETER in value and type == "name":
            value = value.replace(a.LIST_DELIMETER, ", ")
            value = f'The {p.lower()} are ' + value + '.'
        elif type == "name":
            value = 'The name is ' + value + '.'

        doc = nlp(value)

        if not doc or len(doc.ents) < 1:
            continue

        for ent in doc.ents:
            if ent.label_ in TYPES:
                validEnt = {
                    "Id": row["Id"],
                    "Extracted Text": ent.text,
                    "Type": ent.label_,
                    "Property": p
                }
                extractedEntities.append(validEnt)

    printProgress(i+1, rowCount)

if a.DEBUG:
    showTop = 10
    if len(extractedEntities) > showTop:
        extractedEntities = extractedEntities[:showTop]
    pprint(extractedEntities)
    sys.exit()

writeCsv(a.OUTPUT_FILE, extractedEntities, headings=["Id", "Extracted Text", "Type", "Property"])
