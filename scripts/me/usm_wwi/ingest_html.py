# -*- coding: utf-8 -*-

import argparse
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
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/me_usm_wwi_html/%s.html", help="Output file pattern")
parser.add_argument('-item', dest="OUTPUT_ITEM_FILE", default="tmp/me_usm_wwi_html/items/%s.html", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-delay', dest="DELAY", default=1, type=int, help="Wait this long between requests")
a = parser.parse_args()

makeDirectories(a.OUTPUT_FILE)

pages = 16
per_page = 8
for i in range(pages):
    page = i + 1

    url = 'https://digitalcommons.usm.maine.edu/all_wwi/index.html'
    if page > 1:
        url = f'https://digitalcommons.usm.maine.edu/all_wwi/index.{page}.html'

    filename = a.OUTPUT_FILE % page
    contents = ""

    if a.OVERWRITE or not os.path.isfile(filename):
        contents = downloadFileFromUrl(url, filename)
        time.sleep(a.DELAY)
    else:
        contents = readTextFile(filename)

    if len(contents) < 1:
        print(f' **Warning***: No contents for {url}')
        break

    ids = re.findall(r'<a class="cover" href="https://digitalcommons.usm.maine.edu/([a-z0-9\/]+)"', contents)
    if len(ids) != per_page:
        print(f' **Warning***: Only {len(ids)} entries found on page {page}')

    for id in ids:
        url = f'https://digitalcommons.usm.maine.edu/{id}'
        filename = a.OUTPUT_ITEM_FILE % id.replace('/', '_')

        if not os.path.isfile(filename) or a.OVERWRITE:
            contents = downloadFileFromUrl(url, filename)
            time.sleep(a.DELAY)
        else:
            print(f'{filename} already exists, skipping')

print("Done.")
