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
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/hmdb/hmdb_additional_metadata.csv", help="Path to .csv file for hmdb data")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="If the value is a list")
parser.add_argument('-source', dest="SOURCE_NAME", default="HMdb", help="Source column")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/hmdb/hmdb_images.csv", help="Where to store image data")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)
rowsOut = []

for i, row in enumerate(rows):
    urls = row["Images"].split(a.LIST_DELIMETER)
    rows[i]["Source"] = a.SOURCE_NAME
    row["Source"] = a.SOURCE_NAME

    id = itemToId(row)
    if id is None:
        print(f'No ID found for {url}')
        continue

    for j, url in enumerate(urls):
        sUrl = str(url).strip()
        if len(sUrl) < 1:
            continue
        ext = getFileExt(sUrl)
        index = "_"+str(j) if j > 0 else ""
        filename = id + index + ext
        rowOut = {}
        rowOut["ItemId"] = id
        rowOut["Filename"] = filename
        rowsOut.append(rowOut)

writeCsv(a.OUTPUT_FILE, rowsOut, headings=["ItemId", "Filename"])
