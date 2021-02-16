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
from lib.math_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-json', dest="JSON_OUTPUT_FILE", default="tmp/travelks_json/%s.json", help="Output json file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/ks/travelks.csv", help="Output file")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
a = parser.parse_args()

makeDirectories([a.JSON_OUTPUT_FILE, a.OUTPUT_FILE])

page = 0
per_page = 6
total = 148
rows = []
while True:
    filename = a.JSON_OUTPUT_FILE % page
    resp = {}
    skip = page * per_page
    if skip >= total:
        break

    if not os.path.isfile(filename) or a.OVERWRITE:
        url = f'https://www.travelks.com/includes/rest_v2/plugins_listings_listings/find/?json=%7B%22filter%22%3A%7B%22filter_tags%22%3A%7B%22%24in%22%3A%5B%22site_primary_subcatid_452%22%5D%7D%7D%2C%22options%22%3A%7B%22limit%22%3A6%2C%22skip%22%3A{skip}%2C%22fields%22%3A%7B%22address1%22%3A1%2C%22altphone%22%3A1%2C%22categories%22%3A1%2C%22city%22%3A1%2C%22crmtracking%22%3A1%2C%22description%22%3A1%2C%22detailURL%22%3A1%2C%22dtn%22%3A1%2C%22isDTN%22%3A1%2C%22loc%22%3A1%2C%22latitude%22%3A1%2C%22longitude%22%3A1%2C%22media%22%3A1%2C%22phone%22%3A1%2C%22primary_site%22%3A1%2C%22primary_image%22%3A1%2C%22primary_image_url%22%3A1%2C%22rankid%22%3A1%2C%22rankorder%22%3A1%2C%22rankname%22%3A1%2C%22recid%22%3A1%2C%22regionid%22%3A1%2C%22state%22%3A1%2C%22social%22%3A1%2C%22title%22%3A1%2C%22weburl%22%3A1%2C%22zip%22%3A1%2C%22detail_type%22%3A1%2C%22primary_category%22%3A1%2C%22acctid%22%3A1%2C%22qualityScore%22%3A1%2C%22oncethere_orgid%22%3A1%2C%22offers_ids%22%3A1%2C%22offers.recid%22%3A1%2C%22offers.title%22%3A1%2C%22offers.price%22%3A1%2C%22offers.source%22%3A1%7D%2C%22count%22%3Atrue%2C%22hooks%22%3A%5B%22afterFind_offers%22%5D%2C%22sort%22%3A%7B%22qualityScore%22%3A-1%2C%22sortcompany%22%3A1%7D%7D%7D&token=31cadbb1f3261ffa0d3afaaa8f0c2f02'
        resp = downloadJSONFromURL(url, filename)

    else:
        resp = readJSON(filename)

    if "docs" not in resp or "docs" not in resp["docs"] or len(resp["docs"]["docs"]) < 1:
        print(f'No docs in {filename}')
        break

    for doc in resp["docs"]["docs"]:
        row = {}

        for key in ["recid", "title", "address1", "city", "description", "absolute_url", "latitude", "longitude", "primary_image_url"]:
            if key in doc:
                row[key] = stripTags(doc[key])

        if "categories" in doc:
            row["categories"] = [c["subcatname"] for c in doc["categories"]]

        rows.append(row)

    page += 1

fieldsOut = []
for row in rows:
    for key in row:
        if key not in fieldsOut:
            fieldsOut.append(key)

writeCsv(a.OUTPUT_FILE, rows, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)
