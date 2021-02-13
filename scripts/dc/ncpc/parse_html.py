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

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/dc/ncpc_xy_memorials.csv", help="Path to .csv file")
parser.add_argument('-html', dest="HTML_FILE", default="tmp/ncpc_html/%s.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/dc/ncpc_xy_memorials_supplemented.csv", help="Where to store additional metadata")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

makeDirectories(a.OUTPUT_FILE)

def parseHTMLFile(fn):
    contents = ""

    if not os.path.isfile(fn):
        # print(f'{fn} does not exist; skipping')
        return None

    with open(fn, "r", encoding="utf8", errors="replace") as f:
        contents = f.read()

    if len(contents) < 1:
        print(f'{fn} is empty; skipping')
        return None

    bs = BeautifulSoup(contents, "html.parser")

    # Look for article
    container = bs.find("div", {"class": "mem_right_box"})
    if not container:
        print(f'No data box found in {fn}; skipping')
        return None

    keys = container.find_all("h4")
    values = container.find_all("p")

    item = {}
    for key, value in zip(keys, values):
        keyText = key.get_text().strip()
        valueText = value.get_text().strip()
        if keyText in ("Coordinates", "Latitude/Longitude"):
            continue
        item[keyText] = valueText

    return item

updatedRows = []
for i, row in enumerate(rows):
    id = row['OBJECTID']
    if id == '':
        continue

    htmlFile = a.HTML_FILE % id
    item = parseHTMLFile(htmlFile)

    if item is not None:
        for key in item:
            if key not in fields:
                fields.append(key)
        row.update(item)
        updatedRows.append(row)
    printProgress(i+1, rowCount)

writeCsv(a.OUTPUT_FILE, updatedRows, headings=fields)
