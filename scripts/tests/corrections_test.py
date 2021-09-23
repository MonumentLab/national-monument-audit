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
parser.add_argument('-in', dest="INPUT_FILE", default="E:/Dropbox/monumentlab/data/monumentlab_national_monuments_audit_final_2021-07-03.csv", help="Output csv file")
parser.add_argument('-corrections', dest="CORRECTIONS_FILE", default="data/corrections.csv", help="CSV file of corrections")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter string")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE, doParseLists=True, listDelimeter=a.LIST_DELIMETER)
rowCount = len(rows)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

corrections = []
if os.path.isfile(a.CORRECTIONS_FILE):
    _, allCorrections = readCsv(a.CORRECTIONS_FILE, doParseLists=True, listDelimeter=a.LIST_DELIMETER)
    for correction in allCorrections:
        if correction["Field"] not in ("Duplicates", "Duplicate Of"):
            corrections.append(correction)

rows = processCorrections(rows, corrections, verbose=True)
print("Done.")