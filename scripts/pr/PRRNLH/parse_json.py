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
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/pr/Puerto Rico Registro Nacional de Lugares Historicos.json", help="Input JSON file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/pr/Puerto Rico Registro Nacional de Lugares Historicos.csv", help="Output csv")
a = parser.parse_args()

data = readJSON(a.INPUT_FILE)
makeDirectories(a.OUTPUT_FILE)

layers = data["operationalLayers"]
rows = []
fieldnames = ["x", "y"]
for layer in layers:
    features = layer["featureCollection"]["layers"][0]["featureSet"]["features"]
    for f in features:
        row = {}
        row["x"] = f["geometry"]["x"]
        row["y"] = f["geometry"]["y"]
        for key in f["attributes"]:
            row[key] = f["attributes"][key]
            if key not in fieldnames:
                fieldnames.append(key)
        rows.append(row)

writeCsv(a.OUTPUT_FILE, rows, headings=fieldnames)
