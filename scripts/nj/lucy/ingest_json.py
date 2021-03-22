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
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/nj_lucy_json/%s.json", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just print details?")
parser.add_argument('-delay', dest="DELAY", default=0, type=int, help="Wait this long between requests")
a = parser.parse_args()

if not a.PROBE:
    makeDirectories(a.OUTPUT_FILE)

page = 0
per_page = 100
total = 121065
offset = 0
while True:
    filename = a.OUTPUT_FILE % page

    if not os.path.isfile(filename) or a.OVERWRITE:

        url = f'https://njwebmap.state.nj.us/arcgis/rest/services/Features/Land/MapServer/55/query?f=json&where=(DIGIPOST%20%3D%204)%20AND%20(DEMOLISHED%20%3C%3E%20%27YES%27)&returnGeometry=geojson&spatialRel=esriSpatialRelIntersects&geometry=%7B%22xmin%22%3A-8699525.138486328%2C%22ymin%22%3A4700378.730237906%2C%22xmax%22%3A-7900299.570736563%2C%22ymax%22%3A5070945.443364422%2C%22spatialReference%22%3A%7B%22wkid%22%3A102100%7D%7D&geometryType=esriGeometryEnvelope&inSR=102100&outFields=*&orderByFields=OBJECTID%20ASC&outSR=102100&resultOffset={offset}&resultRecordCount={per_page}'

        if a.PROBE:
            print(url)

        else:
            resp = downloadFileFromUrl(url, filename)

            if a.DELAY > 0:
                time.sleep(a.DELAY)

    else:
        print(f'{filename} already exists.')

    offset += per_page
    page += 1

    if offset >= total:
        break

print("Done.")
