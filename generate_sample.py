# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import random
import re
import sys

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Input csv file")
parser.add_argument('-count', dest="COUNT", default=500, type=int, help="Number of records to sample")
parser.add_argument('-fields', dest="FIELDS", default="", help="Comma-separated list of fields to output; leave blank for all")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/monumentlab_sample.csv", help="Output csv file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

fields, rows = readCsv(a.INPUT_FILE)
if len(a.FIELDS) > 0:
    fields = [f.strip() for f in a.FIELDS.split(",")]
    fields = [f for f in fields if len(f) > 0]
rowCount = len(rows)

# randomize
random.shuffle(rows)

# sample a proportionate amount from each source
groups = groupList(rows, groupBy="Source")
groupCount = len(groups)
runningCount = 0
sampleRows = []
for i, group in enumerate(groups):
    targetCount = a.COUNT - runningCount
    if i < (groupCount-1):
        targetCount = roundInt(1.0 * group["count"] / rowCount * a.COUNT)
    targetCount = max(targetCount, 1)
    targetCount = min(targetCount, group["count"])
    sampleRows += group["items"][:targetCount]
    runningCount += targetCount

if a.PROBE:
    sys.exit()

makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, sampleRows, headings=fields)
