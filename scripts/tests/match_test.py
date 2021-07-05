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
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input csv file")
parser.add_argument('-in2', dest="INPUT_FILE2", default="data/compiled/monumentlab_national_monuments_audit_final_2021-07-04.csv", help="Input csv file to compare")
parser.add_argument('-field', dest="FIELD", default="Object Groups", help="Field to compare")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter string")
a = parser.parse_args()

_, rows = readCsv(a.INPUT_FILE)
_, rows2 = readCsv(a.INPUT_FILE2)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rows2 = filterByQueryString(rows2, a.FILTER)

# rows = sorted(rows, key=lambda row: row["Id"])
# rows2 = sorted(rows2, key=lambda row: row["Id"])
row2Lookup = createLookup(rows2, "Id")

for i, row in enumerate(rows):
    if row["Id"] not in row2Lookup:
        print(f'Could not find {row["Id"]} in {a.INPUT_FILE2}')
        continue
    row2 = row2Lookup[row["Id"]]
    if row[a.FIELD] != row2[a.FIELD]:
        print(f'Mismatch at row {i+1} (id={row["Id"]}={row2["Id"]}): {row[a.FIELD]} != {row2[a.FIELD]}')

print('Done.')
