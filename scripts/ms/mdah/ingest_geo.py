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
parser.add_argument('-in', dest="INPUT_FILE", default="tmp/mdah_html/*.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/mdah_geojson/%s.json", help="Where to store .json metadata")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
filecount = len(filenames)

makeDirectories(a.OUTPUT_FILE)

for i, fn in enumerate(filenames):
    id = getBasename(fn)

    url = f'https://www.apps.mdah.ms.gov/MDAHProxy/proxy.ashx?https://www.gisonline.ms.gov/arcgis/rest/services/MDAH/HSMT_Archist/MapServer/0/query?f=json&where=mapdata.DBO.Inventory_ArchistPri_point.PrimaryKey%20%3D%20{id}&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*'
    filename = a.OUTPUT_FILE % id

    if not os.path.isfile(filename) or a.OVERWRITE:
        downloadJSONFromURL(url, filename)
    else:
        print(f'{filename} already exists, skipping')

    printProgress(i+1, filecount)
