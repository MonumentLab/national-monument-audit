# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-py', dest="PYTHON_NAME", default="", help="Python command name, e.g. python or python3")
parser.add_argument('-entities', dest="PROCESS_ENTITIES", action="store_true", help="Also process entities?")
parser.add_argument('-index', dest="PROCESS_INDEX", action="store_true", help="Also process index files?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Only output commands?")
a = parser.parse_args()

PYTHON_NAME = a.PYTHON_NAME if len(a.PYTHON_NAME) > 0 else sys.executable

commands = [
    [PYTHON_NAME, "ingest.py"]
]
if a.PROCESS_ENTITIES:
    commands += [
        [PYTHON_NAME, "extract_entities.py"],
        [PYTHON_NAME, "normalize_entities.py"],
        [PYTHON_NAME, "resolve_entities.py"],
        [PYTHON_NAME, "visualize_entities.py"],
        [PYTHON_NAME, "ingest.py"]
    ]
if a.PROCESS_INDEX:
    commands += [
        [PYTHON_NAME, "index.py"]
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
