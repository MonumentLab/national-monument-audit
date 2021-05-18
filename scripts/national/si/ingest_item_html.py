# -*- coding: utf-8 -*-

import argparse
from bs4 import BeautifulSoup
import inspect
import os
from pprint import pprint
import shutil
import subprocess
import sys
import time

# add parent directory to sys path to import relative modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
parentdir = os.path.dirname(parentdir)
sys.path.insert(0,parentdir)

from lib.collection_utils import *
from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/si/sos_data.csv", help="Input file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/si_html/items/%s.html", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-delay', dest="DELAY", default=2, type=int, help="Wait this long between requests")
a = parser.parse_args()

makeDirectories(a.OUTPUT_FILE)

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

for i, row in enumerate(rows):
    id = row["Id"]
    url = row["Url"]

    printProgress(i, rowCount)

    if id == "" or url == "":
        continue

    filename = a.OUTPUT_FILE % stringToId(id)

    if not a.OVERWRITE and os.path.isfile(filename):
        continue

    contents = downloadFileFromUrl(url, filename)

print("Done.")
