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
from lib.math_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/vendor/ms/mdah_mississippi_landmarks.html", help="Path to .html file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="tmp/mdah_html/%s.html", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing data?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just print details?")
parser.add_argument('-delay', dest="DELAY", default=1, type=int, help="Wait this long between requests")
a = parser.parse_args()

contents = readTextFile(a.INPUT_FILE)

makeDirectories(a.OUTPUT_FILE)

ids = re.findall( r'GotoProperty\(\&\#39\;([0-9]+)\&\#39\;\)', contents)
idCount = len(ids)
print(f'{idCount} ids found')

for i, id in enumerate(ids):
    url = f'https://www.apps.mdah.ms.gov/Public/prop.aspx?id={id}&view=facts&y=1040'
    filename = a.OUTPUT_FILE % id

    if not os.path.isfile(filename) or a.OVERWRITE:
        if not a.PROBE:
            contents = downloadFileFromUrl(url, filename)
            time.sleep(a.DELAY)
        else:
            print(f'Downloading {url} to {filename}')
    else:
        print(f'{filename} already exists, skipping')

    printProgress(i+1, idCount)

print("Done.")
