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

from lib.io_utils import *
from lib.string_utils import *

dataModel = readJSON("config/data-model.json")

fields = []
for field in dataModel["fields"]:
    key = field["key"]
    search_key = stringToId(key)

    if search_key == "latitude":
        search_key = "latlon"
    elif search_key == "longitude":
        continue

    if "facetAndSearch" in field and field["facetAndSearch"]:
        search_key += "_search"

    fields.append(search_key)

fields = sorted(fields)

print(fields)
