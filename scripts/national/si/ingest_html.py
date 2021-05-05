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
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/si_html/%s.html", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-delay', dest="DELAY", default=2, type=int, help="Wait this long between requests")
a = parser.parse_args()

makeDirectories(a.OUTPUT_FILE)

stateMap = getStates()
states = stateMap.keys()
stateCount = len(states)

for i, stateString in enumerate(states):
    queryState = stateString.replace(' ', '+')
    baseQueryUrl = f'https://collections.si.edu/search/results.htm?date.slider=&q=&dsort=&fq=object_type%3A%22Outdoor+sculpture%22&fq=data_source%3A%22Art+Inventories+Catalog%2C+Smithsonian+American+Art+Museum%22&fq=place:%22{queryState}%22'
    start = 0
    while True:
        queryUrl = baseQueryUrl + '&start=' + str(start)
        basename = stringToId(queryState) + '-' + str(start)
        filename = a.OUTPUT_FILE % basename
        contents = ""

        if a.OVERWRITE or not os.path.isfile(filename):
            contents = downloadFileFromUrl(queryUrl, filename)
            time.sleep(a.DELAY)
        else:
            contents = readTextFile(filename)

        if len(contents) < 1:
            print(f' **Warning***: No contents for {queryUrl}')
            break

        bs = BeautifulSoup(contents, "html.parser")
        navContainer = bs.find("div", {"class": "subnav"})
        if not navContainer:
            print(f' **Warning***: No pagination for {queryUrl}; likely no results')
            break

        nextLink = navContainer.find("a", {"title": "next"})
        nextStart = False
        if nextLink:
            href = nextLink.get("href")
            if href and len(href) > 0:
                value = href.split("=")[-1]
                nextStart = int(value)

        if nextStart is not False:
            start = nextStart

        else:
            print(f'Finished downloading {stateString}')
            break

    printProgress(i+1, stateCount)

print("Done.")
