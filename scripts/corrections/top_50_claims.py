# -*- coding: utf-8 -*-

import argparse
import inspect
import os
from pprint import pprint
import re
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
from lib.data_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="E:/Dropbox/monumentlab/data/monumentlab_national_monuments_audit_final_2021-07-03.csv", help="Input csv file")
parser.add_argument('-corrections', dest="CORRECTIONS_FILE", default="data/corrections/top_50_claims_2021-07-02.csv", help="Corrections file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/corrections/top_50_claims_2021-07-02_normalized.csv", help="Output csv file")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE, doParseLists=True)
rowCount = len(rows)
lookup = createLookup(rows, "Id")

def getChildIds(id):
    global rows
    return [row["Id"] for row in rows if row["Duplicate Of"] == id]

_, rawCorrections = readCsv(a.CORRECTIONS_FILE, skipLines=8)

# parse corrections
corrections = []
activePerson = None
activeDuplicateId = None
for i, row in enumerate(rawCorrections):
    status = str(row["Standardized Status"]).strip().lower()
    if status == "":
        activePerson = str(row["Entry #"]).strip()
        continue

    match = re.search(r"id=([^&\s]+)", row["Dashboard Link"])
    if not match:
        print(f'Invalid URL: {row["Dashboard Link"]} (#{row["Row"]})')
        continue

    id = match.group(1)

    if id not in lookup:
        print(f'Could not find record Id: {id}')
        continue

    if status != "duplicate with above":
        activeDuplicateId = id

    if status in ("duplicate", "ambiguous"):
        continue

    row["Id"] = id
    row["Person"] = activePerson

    if status.startswith("duplicate of "):
        dupeParent = status[len("duplicate of "):].strip()
        status = "duplicate of"
        row["DupeParent"] = dupeParent

    elif status.startswith("remove duplicates "):
        RemoveIds = [id.strip() for id in status[len("remove duplicates "):].strip().split(",")]
        status = "remove duplicates"
        row["RemoveIds"] = RemoveIds

    elif status.startswith("remove duplicate"):
        removeId = status[len("remove duplicate "):].strip()
        status = "remove duplicates"
        row["RemoveIds"] = [removeId]

    elif status == "duplicate with above":
        status = "duplicate of"
        row["DupeParent"] = activeDuplicateId

    row["Status"] = status
    corrections.append(row)

    # if minor mention, also remove it from central mention
    if status == "minor mention":
        corrections.append({
            "Id": id,
            "Person": activePerson,
            "Status": "false positive",
            "Minor Mention": True
        })

# copy corrections to child records
for row in corrections:
    if row["Status"] in ("false positive", "minor mention", "unrecognized") and row["Id"].endswith("_merged"):
        childIds = getChildIds(row["Id"])
        for id in childIds:
            newRow = row.copy()
            newRow["Id"] = id
            corrections.append(newRow)

# validate statuses
statuses = unique([row["Status"] for row in corrections])
print('Statuses:')
pprint(statuses)
print('-----------------')

# Should be:
# 'unrecognized',
# 'remove duplicates',
# 'duplicate of',
# 'false positive',
# 'minor mention',
# 'false merge'

# validate names
names = set([])
for row in rows:
    rowNames = row["Entities People"]

    if isinstance(rowNames, str):
        rowName = rowNames.strip()
        if rowName == "":
            continue
        rowNames = [rowName]

    for name in rowNames:
        name = name.strip()
        if name == "":
            continue
        if name not in names:
            names.add(name)

print('Validating names...')
namesInCorrections = unique([row["Person"] for row in corrections])
for name in namesInCorrections:
    if name not in names:
        print(f'Name {name} not in names')

correctionsOut = []
for row in corrections:
    status = row["Status"]
    id = row["Id"]
    action = status
    field = ""
    value = ""
    notes = ""

    if status in ("unrecognized", "false positive"):
        field = "Entities People"

    elif status in ("minor mention"):
        field = "Entities People Mentioned"

    if status in ("unrecognized", "minor mention"):
        action = "add"
        value = row["Person"]

    elif status in ("false positive"):
        action = "remove"
        value = row["Person"]

    elif status in ("remove duplicates"):
        action = "remove"
        field = "Duplicates"
        value = row["RemoveIds"]

    elif status in ("duplicate of"):
        action = "set"
        field = "Duplicate Of"
        value = row["DupeParent"]

    elif status in ("false merge"):
        action = "remove"
        field = "Duplicates"
        if not id.endswith("_merged"):
            print(f'{id} cannot be set as false merge since it is not a merged item')
            continue
        value = getChildIds(id)
        notes = "unmerge"

    if field == "Duplicate Of":
        # don't make a merged record a duplicate of a single one
        if id == value:
            print(f'Warning: trying to set {id} as Duplicate Of {value} (same value)')
            continue
            
        if id.endswith("_merged") and not value.endswith("_merged"):
            id = value
            value = row["Id"]

        # if both are merged, unmerge this one and add each of those unmerged records to the parent
        elif id.endswith("_merged") and value.endswith("_merged"):
            childIds = getChildIds(id)
            # unmerge this record
            correctionsOut.append({
                "Id": id,
                "Field": "Duplicates",
                "Correct Value": childIds,
                "Action": "remove",
                "Notes": "unmerge"
            })
            # make each of those records duplicates of this one
            for childId in childIds:
                correctionsOut.append({
                    "Id": childId,
                    "Field": "Duplicate Of",
                    "Correct Value": row["DupeParent"],
                    "Action": "set"
                })
            continue

    correctionsOut.append({
        "Id": id,
        "Field": field,
        "Correct Value": value,
        "Action": action,
        "Notes": notes
    })

    if status in ("false positive") and "Minor Mention" not in row:
        correctionsOut.append({
            "Id": id,
            "Field": "Entities People Mentioned",
            "Correct Value": value,
            "Action": action,
            "Notes": "false positive"
        })

print('Done.')

makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, correctionsOut, headings=["Id", "Field", "Correct Value", "Action", "Notes"])
