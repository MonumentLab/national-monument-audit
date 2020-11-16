# -*- coding: utf-8 -*-

import argparse
import collections
import inspect
import math
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/records.csv", help="Input csv file")
parser.add_argument('-props', dest="PROPS", default="duration,samples", help="Comma-separated list of properties")
parser.add_argument('-enc', dest="ENCODING", default="utf8", help="Encoding of source file")
parser.add_argument('-filter', dest="FILTER", default="", help="Filter string")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default="", help="If a list, provide delimeter(s)")
parser.add_argument('-lim', dest="LIMIT", default=-1, type=int, help="Limit list length")
a = parser.parse_args()

# Parse arguments
PROPS = [p.strip() for p in a.PROPS.strip().split(",")]

# Read rows
fields, rows = readCsv(a.INPUT_FILE, encoding=a.ENCODING)
rowCount = len(rows)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

for prop in PROPS:
    values = [row[prop] for row in rows if prop in row]
    if len(a.LIST_DELIMETER) > 0:
        expandedValues = []
        for value in values:
            expanded = [v.strip() for v in re.split(a.LIST_DELIMETER, str(value))]
            expanded = [v for v in expanded if len(v) > 0] # remove blanks
            expandedValues += expanded
        values = expandedValues
    uvalues = unique(values)

    counter = collections.Counter(values)
    counts = None
    if a.LIMIT > 0:
        counts = counter.most_common(a.LIMIT)
    else:
        counts = counter.most_common()
    print("---------------------------")
    print(f'{len(uvalues)} unique values for "{prop}"')
    print("---------------------------")
    for value, count in counts:
        percent = round(1.0 * count / rowCount * 100.0, 1)
        if value == "":
            value = "<empty>"
        # print(f'{formatNumber(count)} ({percent}%)\t{value}')
        print(f'{value} ({percent}%)')
