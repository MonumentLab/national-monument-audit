# -*- coding: utf-8 -*-

import argparse
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
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/ncpc_html/%s.html", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just print details?")
parser.add_argument('-delay', dest="DELAY", default=1, type=int, help="Wait this long between requests")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

if not a.PROBE:
    makeDirectories(a.OUTPUT_FILE)

for i, row in enumerate(rows):
    id = row['OBJECTID']
    if id == '':
        continue

    fileOutName = a.OUTPUT_FILE % id
    if not os.path.isfile(fileOutName) or a.OVERWRITE:
        url = f'https://www.ncpc.gov/memorials/detail/{id}/'
        if not a.PROBE:
            contents = downloadFileFromUrl(url, fileOutName)
            time.sleep(a.DELAY)
        else:
            print(f'Downloading {url} to {fileOutName}')
    else:
        print(f'{fileOutName} already exists, skipping')
    printProgress(i+1, rowCount)
