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
parser.add_argument('-html', dest="HTML_FILE", default="tmp/si_html/%s.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/si/sos_data.csv", help="Where to store metadata")
parser.add_argument('-debug', dest="DEBUG", action="store_true", help="Print first result?")
a = parser.parse_args()

makeDirectories(a.OUTPUT_FILE)

stateMap = getStates()
states = stateMap.keys()
stateCount = len(states)

fieldnames = ["Name", "Id", "Url", "Latitude", "Longitude", "State"]

def parseHTMLFile(fn):
    global fieldnames
    items = []
    contents = readTextFile(fn)

    if len(contents) < 1:
        print(f' **Warning***: No contents for {fn}')
        return items

    bs = BeautifulSoup(contents, "html.parser")
    resultsContainer = bs.find("div", {"class": "listing results"})
    if not resultsContainer:
        print(f' **Warning***: No container for {fn}; likely no results')
        return items

    records = resultsContainer.find_all("div", {"class": "record"})
    for record in records:
        item = {}

        titleEl = record.find("h2", {"class": "title"})
        if not titleEl:
            continue

        # Name and ID are required
        item["Name"] = titleEl.get_text().strip()
        item["Id"] = titleEl.get("id").strip()

        # Look for url
        recordLink = record.find("a", {"class": "tag"})
        if recordLink:
            href = recordLink.get("href").strip()
            item["Url"] = "https://collections.si.edu" + href.split('?')[0]

        # Look for lat lon
        mapLink = record.find("a", {"class": "map"})
        if mapLink:
            href = mapLink.get("href").strip()
            latlonString = href.split("=")[-1]
            lat, lon = tuple(latlonString.split(","))
            item["Latitude"] = float(lat)
            item["Longitude"] = float(lon)

        # Go through record metadata
        dls = record.find_all("dl")
        for dl in dls:
            dt = dl.find("dt")
            if not dt:
                continue
            dkey = dt.get_text().strip().strip(':')

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

            if dkey not in fieldnames:
                fieldnames.append(dkey)

            item[dkey] = dvalue

        items.append(item)

    return items

items = []
for i, stateString in enumerate(states):
    stateId = stringToId(stateString)
    stateFilesString = a.HTML_FILE % (stateId + '-*')
    print(f'Parsing {stateFilesString}')
    stateFilenames = getFilenames(stateFilesString)
    stateAbbrev = stateMap[stateString]

    for fn in stateFilenames:
        fileItems = parseHTMLFile(fn)

        for j, item in enumerate(fileItems):
            fileItems[j]["State"] = stateAbbrev

        if len(fileItems) > 0:
            items += fileItems

        if a.DEBUG:
            pprint(items[0])
            break

    printProgress(i+1, stateCount)

    if a.DEBUG:
        break

if a.DEBUG:
    sys.exit()

writeCsv(a.OUTPUT_FILE, items, headings=fieldnames)
