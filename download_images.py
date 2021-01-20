# -*- coding: utf-8 -*-

import argparse
import math
import os
from PIL import Image
from pprint import pprint
import shutil
import sys
import urllib

from lib.collection_utils import *
from lib.image_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Path to csv file")
parser.add_argument('-key', dest="KEY", default="Image", help="Key to retrieve asset url from")
parser.add_argument('-limit', dest="LIMIT", default=-1, type=int, help="Limit downloads; -1 for no limit")
parser.add_argument('-out', dest="OUTPUT_DIR", default="tmp/downloads/", help="Output directory")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default="", help="If the value is a list")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-sort', dest="SORT", default="", help="Query string to sort by")
parser.add_argument('-filter', dest="FILTER", default="Name CONTAINS monument OR Alternate Name CONTAINS monument OR Object Types CONTAINS monument OR Use Types CONTAINS monument OR Subjects CONTAINS monument", help="Query string to filter by")
parser.add_argument('-width', dest="TARGET_WIDTH", default=256, type=int, help="Resize images to this width; -1 for no resizing")
parser.add_argument('-height', dest="TARGET_HEIGHT", default=256, type=int, help="Resize images to this height; -1 for no resizing")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output debug info")
a = parser.parse_args()

# Make sure output dirs exist
makeDirectories(a.OUTPUT_DIR)

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

if len(a.SORT) > 0:
    rows = sortByQueryString(rows, a.SORT)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

rows = [row for row in rows if a.KEY in row and row[a.KEY] != ""]
rowCount = len(rows)
print(f'{rowCount} with value for {a.KEY}')

if a.LIMIT > 0 and rowCount > a.LIMIT:
    rows = rows[:a.LIMIT]
    rowCount = len(rows)

nofileCount = 0
downloads = 0
for i, row in enumerate(rows):
    url = row[a.KEY]
    urls = [url]
    if len(a.LIST_DELIMETER) > 0:
        urls = url.split(a.LIST_DELIMETER)
    id = itemToId(row)
    if id is None:
        print(f'No ID found for {url}')
        continue
    for j, url in enumerate(urls):
        ext = getFileExt(url)
        index = "_"+str(j) if j > 0 else ""
        filename = id + index + ext
        filepath = a.OUTPUT_DIR + filename
        if a.PROBE:
            if not os.path.isfile(filepath):
                nofileCount += 1
                downloads += 1
        elif not os.path.isfile(filepath) or a.OVERWRITE:
            downloadBinaryFile(url, filepath)
            if a.TARGET_WIDTH > 0 and a.TARGET_HEIGHT > 0:
                im = readImage(filepath)
                if im is not False:
                    im.thumbnail((a.TARGET_WIDTH, a.TARGET_HEIGHT))
                    im.save(filepath)
            downloads += 1
    printProgress(i+1, rowCount)

if a.PROBE:
    print(f'{nofileCount} files to download')

print(f'{downloads} files downloaded')
