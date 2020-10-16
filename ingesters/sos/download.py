# -*- coding: utf-8 -*-

import argparse
import inspect
import os
from pprint import pprint
import sys

# add parent directory to sys path to import relative modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
sys.path.insert(0,parentdir)

from lib.edan import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-id', dest="APP_ID", default="", help="Your EDAN App Id")
parser.add_argument('-key', dest="API_KEY", default="", help="Your EDAN API key")
parser.add_argument('-query', dest="QUERY", default="orchids smithsonian gardens images", help="Query")
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/sos/results.csv", help="Output file")
parser.add_argument('-page', dest="START_PAGE", default=1, type=int, help="Page to start on")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just print details?")
a = parser.parse_args()

results = searchEDAN(a.QUERY, a.APP_ID, a.API_KEY)
pprint(results)
