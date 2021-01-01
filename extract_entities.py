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

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input .csv data file")
parser.add_argument('-props', dest="PROPERTIES", default="Name,Alternate Name,Sponsors,Creators,Subjects,Text,Description,Honorees", help="Comma separated list of properties to look at")
parser.add_argument('-types', dest="TYPES", default="PERSON,NORP,ORG,EVENT", help="Comma separated list of entity types to extract: https://spacy.io/api/annotation#named-entities")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_entities.csv", help="Output file")
a = parser.parse_args()
# Parse arguments

# https://spacy.io/api/annotation#named-entities
# PERSON: People, including fictional.
# NORP:   Nationalities or religious or political groups.
# ORG:    Companies, agencies, institutions, etc.
# EVENT:  Named hurricanes, battles, wars, sports events, etc.

fields, rows = readCsv(a.INPUT_FILE)
# rows = [{"Text": "Andrew Dickson White, 1832-1918, friend and counselor of Ezra Cornell, and with him associated in the founding of the Cornell University, its First President 1865-1885 and for fifty years a member of its government board."}]
rowCount = len(rows)
PROPERTIES = [p.strip() for p in a.PROPERTIES.strip().split(",")]
TYPES = [p.strip() for p in a.TYPES.strip().split(",")]
nlp = en_core_web_sm.load()

makeDirectories(a.OUTPUT_FILE)

extractedEntities = []
for i, row in enumerate(rows):
    for p in PROPERTIES:
        if p not in row:
            continue
        value = str(row[p]).strip()
        if len(value) < 1:
            continue

        value = value.replace(a.LIST_DELIMETER, ", ")
        doc = nlp(value)

        if not doc or len(doc.ents) < 1:
            continue

        for ent in doc.ents:
            if ent.label_ in TYPES:
                validEnt = {
                    "Source": row["Source"],
                    "Vendor Entry ID": row["Vendor Entry ID"],
                    "Extracted Text": ent.text,
                    "Type": ent.label_,
                    "Property": p
                }
                extractedEntities.append(validEnt)

    printProgress(i+1, rowCount)

writeCsv(a.OUTPUT_FILE, extractedEntities, headings=["Source", "Vendor Entry ID", "Extracted Text", "Type", "Property"])
