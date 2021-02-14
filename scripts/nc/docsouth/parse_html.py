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
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/docsouth_html/*.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/nc/unc_docsouth_commland.csv", help="Where to store additional metadata")
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
        "URL": f'https://docsouth.unc.edu/commland/monument/{id}/'
    }

    container = bs.find("div", {"id": "pagewrap"})
    if not container:
        print(f'No container found for {fn}')
        return None

    # get image
    imgContainer = container.find("div", {"class": "rep"})
    if imgContainer:
        imgTag = imgContainer.find("img")
        if imgTag:
            imgUrl = imgTag.get("src")
            if imgUrl:
                item["Image"] = imgUrl

    metaContainer = container.find("div", {"class", "metabox"})
    if not metaContainer:
        print(f'No meta container found for {fn}')
        return None

    metaItems = metaContainer.find_all("li")
    for metaItem in metaItems:
        label = metaItem.find("h5")
        values = metaItem.find_all("p")
        labelText = label.get_text(strip=True).strip()
        valuesText = [v.get_text(strip=True).strip() for v in values]
        if len(valuesText) == 1:
            valuesText = valuesText[0]

        if labelText == "Geographic Coordinates":
            # look for lat lon
            m = re.search("([0-9\.]+) , (\-[0-9\.]+)", valuesText)
            if m:
                item["Latitude"] = m.group(1)
                item["Longitude"] = m.group(2)

        else:
            item[labelText] = valuesText

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
