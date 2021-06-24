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

parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="config/ingest/*.json", help="Input .json config files")
parser.add_argument('-props', dest="PROPS", default="Subjects,Object Types", help="List of properties to look up")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
PROPS = [p.strip() for p in a.PROPS.split(",")]

propMap = {}
for p in PROPS:
    propMap[p] = set([])
for fn in filenames:
    data = readJSON(fn)
    if "mappings" not in data:
        continue
    for k,v in data["mappings"].items():
        if "to" not in v:
            continue
        toProp = v["to"]
        if toProp in propMap and k not in propMap[toProp]:
            propMap[toProp].add(k)

for p in PROPS:
    print(f'Source field names for "{p}":')
    names = sorted(list(propMap[p]))
    pprint(names)
    print('------------------------------')
