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
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/wisaard_json/%s.json", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just print details?")
parser.add_argument('-delay', dest="DELAY", default=1, type=int, help="Wait this long between requests")
a = parser.parse_args()

if not a.PROBE:
    makeDirectories(a.OUTPUT_FILE)

page = 0
per_page = 100
total = 2899
fromItem = None
toItem = None
while True:
    filename = a.OUTPUT_FILE % page
    fromItem = page * per_page
    toItem = fromItem + per_page

    if not os.path.isfile(filename) or a.OVERWRITE:

        resp = curlRequest(f'curl "https://wisaard.dahp.wa.gov/api/api//resultGroup/1162/query" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://wisaard.dahp.wa.gov/Search/1162" -H "content-type: application/json" -H "range: items={fromItem}-{toItem}" -H "Origin: https://wisaard.dahp.wa.gov" -H "Connection: keep-alive" --data-raw "{{""sort"":[{{""attribute"":""RegisterName"",""descending"":true}}]}}"', filename, isJson=True)

        if "success" not in resp or not resp["success"]:
            break
    else:
        print(f'{filename} already exists.')

    if toItem >= total:
        break

    page += 1

print("Done.")
