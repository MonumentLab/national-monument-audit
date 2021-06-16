# -*- coding: utf-8 -*-

import argparse
from collections import Counter
import en_core_web_sm
import inspect
import os
from pprint import pprint
import spacy
from spacy import displacy
import sys

# add parent directory to sys path to import relative modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
sys.path.insert(0,parentdir)

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *

rows = [
    {"Text": "Andrew Dickson White, 1832-1918, friend and counselor of Ezra Cornell, and with him associated in the founding of the Cornell University, its First President 1865-1885 and for fifty years a member of its government board."},
    {"Name": "Justice John McKinley Federal Building"},
    {"Name": "Horace King"},
    {"Text": "First White House of the Confederacy. .  .  . Designated Executive Residence by the Provisional Confederate Congress February 21, 1861. President Jefferson Davis  and his family lived here until the Confederate Capital moved to Richmond summer 1861. Built by William Sayre 1832-35 at Bibb and  Lee Streets. Moved to present location by the First White House Association and dedicated June 3, 1921."},
    {"Name": "Martin Luther King Civil Rights Memorial, (sculpture)", "Text": "A portrait of Dr. Martin Luther King, Jr. striding forward. He is dressed in suit covered by a clerical robe. Captured in the tucks and folds of the robe are scenes of significant events of the Civil Rights Movement, including Rosa Parks seated on a bus, Martin Luther King, Jr. in a jail cell contemplating Gandhi, Civil Rights marches, a fireman spraying water, the Martin Luther King family, and a hanging by the Ku Klux Klan. The base is inscribed with quotes from Martin Luther King, Jr.'s speeches."},
    {"Name": "Doctor Martin Luther King Junior Memorial"},
    {"Name": "William Seward and Harriet Tubman Statue", "Honorees": "Tubman, Harriet, 1822-1913 | Seward, William Henry, 1801-1872"}
]
for i, row in enumerate(rows):
    rows[i]["Id"] = ""
    rows[i]["Source"] = ""
    rows[i]["Vendor Entry ID"] = ""

rowCount = len(rows)
PROPERTIES = [{"prop": p.strip(), "type": "name"} for p in "Name,Alternate Name,Honorees".strip().split(",")]
TEXT_PROPERTIES = [{"prop": p.strip(), "type": "text"} for p in "Text,Description".strip().split(",")]
props = PROPERTIES + TEXT_PROPERTIES
TYPES = [p.strip() for p in "PERSON,NORP,ORG,EVENT".strip().split(",")]
nlp = en_core_web_sm.load()

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
        if " | " in value and type == "name":
            values = [normalizeName(v.strip().strip("|").strip()).title() for v in value.split("|")]
            value = ", ".join(values)
            value = f'The {p.lower()} are ' + value + '.'
        elif type == "name":
            value = 'The name is ' + normalizeName(value).title() + '.'

        print("-----------------")
        print(f'Value: "{value}"')

        doc = nlp(value)

        if not doc or len(doc.ents) < 1:
            print("Result: None")
            continue

        print(f'{len(doc.ents)} results: ')
        for ent in doc.ents:
            if ent.label_ in TYPES:
                validEnt = {
                    "Id": row["Id"],
                    "Extracted Text": ent.text,
                    "Type": ent.label_,
                    "Property": p
                }
                extractedEntities.append(validEnt)
                print(f' - {ent.text} ({ent.label_})')
