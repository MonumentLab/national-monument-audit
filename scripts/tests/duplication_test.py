# -*- coding: utf-8 -*-

# python3 scripts/tests/duplication_test.py -filter "Name CONTAINS Martin Luther King AND Source != Multiple AND State = DC"
# python3 scripts/tests/duplication_test.py -filter "Name CONTAINS Cuban AND Source != Multiple AND State = DC"

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
parser.add_argument('-filter', dest="FILTER", default="Name CONTAINS Caddo Parish AND Source != Multiple", help="Filter string")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

duplicateCount, duplicateRows, rows = applyDuplicationFields(rows)
print("---------------------------")

for row in duplicateRows:
    if "Id" not in row:
        print("---------------------------")
        continue
    print(f'{row["Name"]} / {row["Id"]} / {row["URL"]}')

dupedIds = set([row["Id"] for row in duplicateRows if "Id" in row])
notMatched = [row for row in rows if row["Id"] not in dupedIds]
print("---------------------------")
print("Not duplicates: ")

for row in notMatched:
    print(f'{row["Name"]} / {row["Id"]} / {row["URL"]}')
