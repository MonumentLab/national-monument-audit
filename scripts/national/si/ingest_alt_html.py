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
from lib.geo_utils import *
from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/si/sos_data_location_fixed.csv", help="Input file")
parser.add_argument('-html', dest="HTML_FILE", default="tmp/si_html/items/%s.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/si_html/alt_items/%s.html", help="Where to store output html")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-debug', dest="DEBUG", action="store_true", help="Print first result?")
a = parser.parse_args()

makeDirectories(a.OUTPUT_FILE)

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)
noLinkFound = 0
for i, row in enumerate(rows):
    printProgress(i, rowCount)
    id = row["Id"]

    if id == "":
        continue

    filename = a.HTML_FILE % stringToId(id)
    filenameOut = a.OUTPUT_FILE % id

    if not a.OVERWRITE and os.path.isfile(filenameOut):
        continue

    if not os.path.isfile(filename):
        print(f' Could not find {filename}')
        continue

    contents = readTextFile(filename)
    if len(contents) < 1:
        print(f' No contents for {filename}')
        continue

    bs = BeautifulSoup(contents, "html.parser")
    recordLink = bs.find("a", {"title": "link to cataloged record"})

    if not recordLink:
        noLinkFound += 1
        continue

    url = recordLink.get("href").strip()
    contents = downloadFileFromUrl(url, filenameOut)

    if a.DEBUG:
        break

print(f'No link found for {noLinkFound} records')

print("Done.")
