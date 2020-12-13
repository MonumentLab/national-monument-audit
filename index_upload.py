# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import subprocess
import sys
import time

from lib.io_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="search-index/documents/*.json", help="Input batch .json documents")
parser.add_argument('-profile', dest="AWS_PROFILE", default="monumentlab", help="AWS CLI profile with your credentials")
parser.add_argument('-url', dest="ENDPOINT", default="https://doc-national-monument-audit-nuccsr3nq7s5kshgvyx4kuxsdq.us-east-1.cloudsearch.amazonaws.com", help="End point")
parser.add_argument('-wait', dest="WAIT_SECONDS", default=10, type=int, help="Wait this much time between requests (seconds)")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

filenames = getFilenames(a.INPUT_FILE, verbose=True)

for batchFilename in filenames:
    command = ["aws", "cloudsearchdomain", "upload-documents", "--endpoint-url", a.ENDPOINT, "--content-type", "application/json", "--documents", batchFilename, "--profile", a.AWS_PROFILE]
    print(" ".join(command))
    if not a.PROBE:
        finished = subprocess.check_call(command)
        if a.WAIT_SECONDS > 0:
            time.sleep(a.WAIT_SECONDS)
    print("-------------------------------")
