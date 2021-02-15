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
from lib.math_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/historyillinois_html/*.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/il/HistoryIllinoisCountyMarkers/HistoryIllinoisCountyMarkers.csv", help="Where to store additional metadata")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
filecount = len(filenames)

makeDirectories(a.OUTPUT_FILE)

def parseHTMLFile(fn):
    contents = readTextFile(fn)

    if len(contents) < 1:
        print(f'{fn} is empty; skipping')
        return None

    bs = BeautifulSoup(contents, "html.parser")
    id = getBasename(fn)
    item = {
        "Vendor Entry ID": id,
        "URL": f'https://www.historyillinois.org/FindAMarker/MarkerDetails.aspx?MarkerID={id}'
    }

    container = bs.find("div", {"id": "dnn_ctr7993_ModuleContent"})
    if not container:
        print(f'No container found for {fn}')
        return None

    rows = container.find_all("div", {"class": "row"})
    for i, row in enumerate(rows):
        colLeft = row.find("div", {"class": "col-sm-3 text-right"})
        colRight = row.find("div", {"class": "col-sm-9"})
        img = row.find("img", {"class": "img-responsive"})

        if not colLeft or (not colRight and not img):
            continue

        label = colLeft.get_text(strip=True).strip(" :")
        value = colRight.get_text(strip=True).strip() if colRight else ""
        if label == "Picture" and img:
            item["Image"] = "https://www.historyillinois.org" + img.get("src").strip()

        elif label == "County":
            item["County"] = value.split("(")[0].strip()

        elif label == "Dedication By":
            sponsors = value.split(" and ")
            if len(sponsors) < 2:
                sponsors = value.split(", and ")
            if len(sponsors) > 1:
                sponsors = sponsors[0].split(",") + sponsors[1:]
            sponsors = [s.strip(" ,") for s in sponsors]
            item["Dedication By"] = sponsors

        elif label != "Map":
            item[label] = value

    # pprint(item)

    return item

rows = []
fieldnames = []
for i, fn in enumerate(filenames):
    row = parseHTMLFile(fn)
    if row is not None:
        rows.append(row)
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    printProgress(i+1, filecount)

writeCsv(a.OUTPUT_FILE, rows, headings=fieldnames, listDelimeter=a.LIST_DELIMETER)
