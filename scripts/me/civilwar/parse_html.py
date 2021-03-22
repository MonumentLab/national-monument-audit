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
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/me_civilwar_html/*.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/me/maine_gov_civilwar_monuments.csv", help="Where to store metadata")
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
        "URL": f'https://www.maine.gov/civilwar/monuments/{id}.html'
    }

    table = bs.find("table")

    if not table:
        print(f'Could not find table in {fn}')
        return item

    h1 = table.find("h1")
    if h1:
        item["Name"] = h1.get_text(strip=True).strip()

    metaTds = table.find_all("td")
    for td in metaTds:
        content = td.get_text(strip=True).strip()
        if ":" not in content:
            continue

        key, value = tuple(content.split(":", 1))
        item[key.strip()] = value.strip()

    img = table.find("img")
    if img:
        imgUrl = img.get("src")
        item["Image"] = imgUrl.replace('..', 'https://www.maine.gov/civilwar')

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
