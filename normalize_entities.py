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
parser.add_argument('-in', dest="INPUT_FILE", default="data/preprocessed/monumentlab_national_monuments_audit_entities.csv", help="Input .csv data file")
parser.add_argument('-add', dest="ADD_ENTITIES", default="data/entities_add.csv", help="Input .csv data file that contains entities to add")
parser.add_argument('-alias', dest="ALIAS_FILE", default="data/entities_aliases.csv", help="Input .csv data file with synonyms")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter query")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/preprocessed/monumentlab_national_monuments_audit_entities_normalized.csv", help="Output file")
parser.add_argument('-stats', dest="STATS_OUTPUT_FILE", default="tmp/entities_type_%s.csv", help="Output stats file pattern")
parser.add_argument('-probe', dest="PROBE",  default=0, type=int, help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fieldnames, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

addEntities = []
addEntitiesRows = []
if len(a.ADD_ENTITIES) > 0 and os.path.isfile(a.ADD_ENTITIES):
    _, addEntitiesRows = readCsv(a.ADD_ENTITIES)
    for i, row in enumerate(addEntitiesRows):
        addEntities.append(normalizeName(row["name"]))

_, aliases = readCsv(a.ALIAS_FILE)
aliases = aliases + addEntitiesRows
aliasLookup = {}
containsLookup = {}
endswithLookup = {}
for i, row in enumerate(aliases):
    contains = row["match"].startswith("*")
    endswith = row["match"].endswith("*")
    nmatch = normalizeName(row["match"])
    ntarget = normalizeName(row["target"])
    if contains and nmatch == "contains":
        containsLookup[ntarget] = {
            "ntext": ntarget,
            "text": row["target"]
        }
    elif contains:
        containsLookup[nmatch] = {
            "ntext": ntarget,
            "text": row["target"]
        }
    elif endswith:
        endswithLookup[nmatch] = {
            "ntext": ntarget,
            "text": row["target"]
        }
    else:
        aliasLookup[nmatch] = {
            "ntext": ntarget,
            "text": row["target"]
        }

if len(a.FILTER) > 0:
    print("  Filtering data...")
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'  {rowCount} rows after filtering')

ntextLookup = {}
rowsOut = []
print("  Normalizing data...")
for i, row in enumerate(rows):
    text = str(row["Extracted Text"])
    ntext = normalizeName(text)
    if len(ntext) < 1:
        continue

    if ntext in aliasLookup:
        text = aliasLookup[ntext]["text"]
        ntext = aliasLookup[ntext]["ntext"]

    else:
        # check to see if text is contained within a string
        foundMatch = False
        for nmatch, item in containsLookup.items():
            if containsWordBoundary(ntext, nmatch):
                text = item["text"]
                ntext = item["ntext"]
                foundMatch = True
                break

        # check to see if endswith string
        if not foundMatch:
            for nmatch, item in endswithLookup.items():
                if ntext.endswith(nmatch):
                    text = item["text"]
                    ntext = item["ntext"]
                    break


    nwords = ntext.split(" ")
    wordcount = len(nwords)
    if ntext not in addEntities and row["Property"] not in ("Honorees"): # make an exception for manually set names or explicit honorees
        # only take names with two ore more words
        if wordcount < 2:
            continue
        # skip names with only an initial as the last word, e.g. John F.
        elif wordcount == 2 and len(nwords[1]) == 1:
            continue

    # keep track of original text after normalization
    titleText = stringToTitle(text)
    nkey = ntext + row["Type"]
    if nkey not in ntextLookup:
        ntextLookup[nkey] = {
            "originalText": titleText,
            "ntext": ntext,
            "type": row["Type"],
            "alternateTexts": [],
            "count": 1
        }
    else:
        ntextLookup[nkey]["count"] += 1
        if ntextLookup[nkey]["originalText"] != text and text not in ntextLookup[nkey]["alternateTexts"]:
            ntextLookup[nkey]["alternateTexts"].append(text)
            titleText = ntextLookup[nkey]["originalText"]

    rowOut = row.copy()
    rowOut["Normalized Text"] = ntext
    rowOut["Formatted Text"] = titleText
    rowsOut.append(rowOut)
    printProgress(i+1, rowCount, "  ")

print("  Sorting data...")
frequencies = sorted([ntextLookup[nkey] for nkey in ntextLookup], key=lambda t: -t["count"])

if a.PROBE > 0:
    lim = a.PROBE
    if len(frequencies) > lim:
        frequencies = frequencies[:lim]
    for i, entry in enumerate(frequencies):
        print(f'{entry["count"]}: {entry["originalText"]} ({entry["ntext"]}) / {" / ".join(entry["alternateTexts"])}')
        print('---')
    sys.exit()

makeDirectories(a.OUTPUT_FILE)
makeDirectories(a.STATS_OUTPUT_FILE)

groups = groupList(frequencies, "type")
for group in groups:
    outputFile = a.STATS_OUTPUT_FILE % group["type"]
    writeCsv(outputFile, group["items"], headings=["originalText", "count", "alternateTexts", "ntext"])

fieldnames += ["Normalized Text", "Formatted Text"]
writeCsv(a.OUTPUT_FILE, rowsOut, headings=fieldnames)
# sumCount = sum([f["count"] for f in frequencies])
# meanCount = roundInt(1.0 * sumCount / len(frequencies))
# jsonOut = {
#     "sum": sumCount,
#     "mean": meanCount,
#     "frequencies": [[f["originalText"], f["count"]] for f in frequencies]
# }
# makeDirectories(a.OUTPUT_FILE)
# writeJSON(a.OUTPUT_FILE, jsonOut)
