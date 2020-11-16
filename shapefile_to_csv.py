# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.geo_utils import *
from lib.io_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="path/to/shapefile", help="Input path to shapefile")
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/shapefile.csv", help="Output csv file")
a = parser.parse_args()
# Parse arguments

data = readShapefile(a.INPUT_FILE)
makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, data)
