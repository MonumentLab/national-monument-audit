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
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/nv/historical-markers-json.json", help="Path to .json file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/nv/historical-markers.csv", help="Output .csv file")
parser.add_argument('-html', dest="HTML_FILE", default="tmp/nv_shpo/%s.html", help="Output html file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
a = parser.parse_args()

rows = readJSON(a.INPUT_FILE)
rowCount = len(rows)

makeDirectories([a.OUTPUT_FILE, a.HTML_FILE])

for i, row in enumerate(rows):
    if 'slug' not in row:
        continue

    id = row['slug']
    fileOutName = a.HTML_FILE % id
    url = f'https://shpo.nv.gov/nevadas-historical-markers/historical-markers/{id}'
    rows[i]['url'] = url
    contents = ''
    if not os.path.isfile(fileOutName) or a.OVERWRITE:
        contents = downloadFileFromUrl(url, fileOutName)
    else:
        print(f'{fileOutName} already exists')
        contents = readTextFile(fileOutName)

    bs = BeautifulSoup(contents, "html.parser")
    container = bs.find("article", {"class": "content typography"})
    if container:
        paragraphs = container.find_all("p")
        if len(paragraphs) > 0:
            rows[i]["Description"] = " ".join([p.get_text().strip() for p in paragraphs])

    printProgress(i+1, rowCount)

fieldsOut = []
for i, row in enumerate(rows):
    for key in row:
        if row[key] == "---":
            rows[i][key] = ""
        if key not in fieldsOut:
            fieldsOut.append(key)

writeCsv(a.OUTPUT_FILE, rows, headings=fieldsOut)
