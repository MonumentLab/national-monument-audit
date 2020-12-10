# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.io_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input csv file")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter string")
parser.add_argument('-sort', dest="SORT", default="", help="Sort string")
parser.add_argument('-limit', dest="LIMIT", default=-1, type=int, help="Limit results; -1 for all")
parser.add_argument('-fields', dest="FIELDS", default="", help="Comma-separated list of fields to output; leave blank for all")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/filtered.csv", help="Output csv file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fields, rows = readCsv(a.INPUT_FILE)
if len(a.FIELDS) > 0:
    fields = [f.strip() for f in a.FIELDS.split(",")]
    fields = [f for f in fields if len(f) > 0]
rowCount = len(rows)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

if len(a.SORT) > 0:
    rows = sortByQueryString(rows, a.SORT)

if a.LIMIT > 0 and rowCount > a.LIMIT:
    rows = rows[:a.LIMIT]
    rowCount = len(rows)
    print(f'{rowCount} rows after limiting')

if a.PROBE:
    sys.exit()

makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, rows, headings=fields)
