# -*- coding: utf-8 -*-

import argparse
from bs4 import BeautifulSoup
import inspect
import os
from pprint import pprint
import re
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
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/me_usm_wwi_html/items/*.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/me/usm_wwi_memorial_inventory.csv", help="Where to store metadata")
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
    idUrl = id.replace('_', '/')
    item = {
        "Vendor Entry ID": id,
        "URL": f'https://digitalcommons.usm.maine.edu/{idUrl}'
    }

    # find lat/lon, e.g.
        # mapOptions.lat = 43.51533077062756;
    	# mapOptions.lng = -70.37611218993527;
    lats = re.findall(r'mapOptions.lat = ([0-9\.]+)', contents)
    lons = re.findall(r'mapOptions.lon = ([0-9\.]+)', contents)
    if len(lats) > 0 and len(lons) > 0:
        item["Latitude"] = lats[0]
        item["Longitude"] = lons[0]

    # find image
    imgs = re.findall(r'id="img-med" class="btn" href="(.+preview.jpg)"', contents)
    if len(imgs) > 0:
        item["Image"] = imgs[0]
    else:
        print(f'Could not find image in {fn}')

    main = bs.find("div", {"id": "main"})
    if not main:
        print(f'Could not find main in {fn}')
        return item

    # imgLink = main.find("a", {"id": "img-med"})
    # if imgLink:
    #     item["Image"] = imgLink.get("href")
    # else:
    #     print(f'Could not find image in {fn}')

    elements = main.find_all("div", {"class": "element"})
    for element in elements:
        heading = element.find("h4")
        if not heading:
            continue

        key = heading.get_text(strip=True).strip()
        ps = element.find_all("p")
        value = " ".join([p.get_text(strip=True).strip() for p in ps])

        if key not in item:
            if key == "Title":
                name = ""
                city = ""
                if ":" in value:
                    citystate, name = tuple(value.split(":", 1))
                    if "," in citystate:
                        city, state = tuple(citystate.split(",", 1))
                    else:
                        city = citystate
                elif "," in value:
                    parts = value.split(",")
                    if len(parts) == 2:
                        city, state = tuple(value.split(",", 1))
                    elif len(parts) == 3:
                        city, state, name = tuple(value.split(",", 2))
                    if "(" in state:
                        # e.g. Mount Desert Island, Maine (Alessandro Fabbri Memorial, Acadia National Park)
                        city, state = tuple(value.split(",", 1))
                        state, name = tuple(state.split("(", 1))
                        name = name.strip().strip(")")
                elif "/" in value:
                    city, name = tuple(value.split("/", 1))
                if len(name.strip()) < 1:
                    name = city
                item["Name"] = name.strip()
                item["City"] = city.strip()
            else:
                item[key] = value

        else:
            existingValue = item[key]
            if isinstance(existingValue, list):
                item[key].append(value)
            else:
                item[key] = [existingValue, value]

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
