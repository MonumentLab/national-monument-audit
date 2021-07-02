# -*- coding: utf-8 -*-

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

from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/hmdb/HMdb-Historical-Markers-and-War-Memorials-in--20201204_Virginia.csv", help="Input csv file")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE, encoding="mbcs")

for row in rows:
    if str(row["MarkerID"]) == "3715":

        print(row["Title"])
        break
