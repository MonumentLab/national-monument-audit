# -*- coding: utf-8 -*-

# python3 scripts/tests/duplication_test.py -filter "Name CONTAINS Martin Luther King AND Source != Multiple AND State = DC"
# python3 scripts/tests/duplication_test.py -filter "Name CONTAINS Friendship AND Source != Multiple AND State = DC"

import argparse
import inspect
import os
from pprint import pprint
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
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Output csv file")
parser.add_argument('-corrections', dest="CORRECTIONS_FILE", default="data/corrections.csv", help="CSV file of corrections")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter string")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE, doParseLists=True, listDelimeter=a.LIST_DELIMETER)
rowCount = len(rows)
lookup = createLookup(rows, "Id")

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

_, corrections = readCsv(a.CORRECTIONS_FILE, doParseLists=True, listDelimeter=a.LIST_DELIMETER)

for i, correction in enumerate(corrections):
    id = correction["Id"]
    field = correction["Field"]
    value = correction["Correct Value"]
    action = correction["Action"]
    notes = correction["Notes"]
    row = lookup[id] if id in lookup else None

    # assume duplicate removals are unmerges
    if field == "Duplicates" and action == "remove":
        if row is not None and "unmerge" in notes:
            print(f'{i+1}. {id} was supposed to be unmerged but still exists')
            childIds = [row["Id"] for row in rows if row["Duplicate Of"] == id]
            print('  ---')
            for v in childIds:
                print(f'   {i+1}. {v} has Duplicate Of = {id}')
            print('  ---')

        value = stringToList(value)
        for v in value:
            if lookup[v]["Duplicate Of"] == id:
                print(f'   {i+1}. {v} was supposed to remove Duplicate Of = {id}')

        continue

    if row is None:
        print(f'{i+1}. Could not find id = {id}')
        continue

    newValue = row[field]
    ogValue = newValue
    if isinstance(value, list):
        value = tuple(set(sorted(value)))
    if isinstance(newValue, list):
        newValue = tuple(set(sorted(newValue)))

    if field == "Duplicate Of" and action == "set" and not value.endswith("_merged"):
        newValue = newValue[:-len("_merged")]
        if newValue == value or newValue == id:
            continue

    if action == "set" and newValue != value:
        print(f'{i+1}. {id} was supposed to set {field} = {value} but is "{ogValue}"')
        continue

    if isinstance(value, tuple):
        value = list(value)
    if isinstance(newValue, tuple):
        newValue = list(newValue)

    value = stringToList(value)
    newValue = stringToList(newValue)

    if action == "add":
        for v in value:
            if v not in newValue:
                print(f'{i+1}. {id} was supposed to add {v} to {field} but does not exist in "{ogValue}"')
        continue

    if action == "remove":
        for v in value:
            if v in newValue:
                print(f'{i+1}. {id} was supposed to remove {v} from {field} but exists in "{ogValue}"')
