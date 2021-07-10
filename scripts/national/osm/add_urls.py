# -*- coding: utf-8 -*-

import argparse
import inspect
import os
from pprint import pprint
import re
import sys

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
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/national/osm/quickOSM/*.csv", help="Input file")
parser.add_argument('-url', dest="URL_KEY", default="URL", help="URL key")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()

filenames = getFilenames(a.INPUT_FILE)
fields = {}
rows = {}
for fn in filenames:
    ffields, frows = readCsv(fn)
    if a.URL_KEY not in ffields:
        ffields.append(a.URL_KEY)
    else:
        print(f'Warning: {a.URL_KEY} already in {fn}')

    for i, row in enumerate(frows):
        url = ""
        # https://www.openstreetmap.org/way/319326430
        if "@id" in row:
            url = f'https://www.openstreetmap.org/{row["@id"]}'
        else:
            url = f'https://www.openstreetmap.org/node/{row["osm_id"]}'
        frows[i][a.URL_KEY] = url

    rows[fn] = frows
    fields[fn] = ffields

# https://www.openstreetmap.org/node/1707845568
# https://www.openstreetmap.org/way/319326430

if a.PROBE:
    sys.exit()

for fn in filenames:
    frows = rows[fn]
    ffields = fields[fn]
    writeCsv(fn, frows, headings=ffields)

print("Done.")
