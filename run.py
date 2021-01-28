# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-py', dest="PYTHON_NAME", default="python", help="Python command name, e.g. python or python3")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Only output commands?")
a = parser.parse_args()

commands = [
    [a.PYTHON_NAME, "ingest.py"],
    [a.PYTHON_NAME, "extract_entities.py"],
    [a.PYTHON_NAME, "normalize_entities.py"],
    [a.PYTHON_NAME, "resolve_entities.py"],
    [a.PYTHON_NAME, "visualize_entities.py"],
    [a.PYTHON_NAME, "index.py"]
]
count = len(commands)

for i, command in enumerate(commands):
    print(f'{i+1} of {count} ==============================')
    print(" ".join(command))
    print("==============================")
    if not a.PROBE:
        finished = subprocess.check_call(command)

print("==============================")
print("Done.")
