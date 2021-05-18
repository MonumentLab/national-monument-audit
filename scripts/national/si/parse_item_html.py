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
parser.add_argument('-html', dest="HTML_FILE", default="tmp/si_html/items/%s.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="", help="Output file")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-delay', dest="DELAY", default=2, type=int, help="Wait this long between requests")
a = parser.parse_args()

OUTPUT_FILE = a.OUTPUT_FILE if len(a.OUTPUT_FILE) > 0 else a.INPUT_FILE

makeDirectories(OUTPUT_FILE)

fieldNames, rows = readCsv(a.INPUT_FILE)
# rows = addIndices(rows, keyName="_index")
rowCount = len(rows)

for i, row in enumerate(rows):
    id = row["Id"]

    if id == "":
        continue

    filename = a.HTML_FILE % stringToId(id)

    if not os.path.isfile(filename):
        print(f' Could not find {filename}')
        continue

    contents = readTextFile(filename)
    if len(contents) < 1:
        print(f' No contents for {filename}')
        continue

    bs = BeautifulSoup(contents, "html.parser")
    metaContainer = bs.find("div", {"class": "meta"})
    if not metaContainer:
        print(f' No container for {filename}')
        continue

    dls = metaContainer.find_all("dl", {"class": "details"})
    for dl in dls:
        titleEl = dl.find("dt")
        if not titleEl:
            continue
        fieldName = titleEl.get_text().strip().strip(":")
        if fieldName in row:
            continue
        dds = dl.find_all("dd")
        dvalues = []
        for dd in dds:
            strings = list(dd.stripped_strings)
            if len(strings) > 0:
                dvalues.append(strings[0]) # get first string

        if len(dvalues) < 1:
            continue

        # Join multiple values
        dvalue = dvalues[0]
        if len(dvalues) > 1:
            dvalue = " | ".join(dvalues)

        if fieldName not in fieldNames:
            fieldNames.append(fieldName)

        # print(f'{fieldName} = {dvalue}')
        rows[i][fieldName] = dvalue

    printProgress(i+1, rowCount)

writeCsv(OUTPUT_FILE, rows, headings=fieldNames)
print("Done.")
