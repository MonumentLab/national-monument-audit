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

parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input .csv data file")
a = parser.parse_args()

cases = [
    {"contains": ["Mary, mother of Jesus", "Jesus"], "remove": "Jesus"},
    {"contains": ["Martin Luther King Jr.", "Martin Luther"], "remove": "Martin Luther"},
    {"contains": ["Mohammed Ali", "Mohammed"], "remove": "Mohammed"}
]

fields, rows = readCsv(a.INPUT_FILE, doParseLists=True)
rowCount = len(rows)

for i, row in enumerate(rows):
    ents = stringToList(row["Entities People"])

    for case in cases:
        match = True
        for name in case["contains"]:
            if name not in ents:
                match = False
                break
        if match:
            print(f'{row["Id"]}|Entities People|{case["remove"]}|remove|{row["Name"]}')
    # printProgress(i+1, rowCount)
print("Done.")
