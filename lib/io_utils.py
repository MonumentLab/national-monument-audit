# -*- coding: utf-8 -*-

import csv
import glob
import json
import os
from pprint import pprint
import re
import requests
import shutil
import subprocess
import sys
import zipfile

from lib.collection_utils import *
from lib.math_utils import *

def appendToFilename(fn, appendString):
    ext = getFileExt(fn)
    extLen = len(ext)
    return fn[:-extLen] + appendString + ext

def copyDir(src, dst):
    shutil.copytree(src, dst)

def curlRequest(string, filename, isJson=False):
    result = subprocess.run(string, stdout=subprocess.PIPE)
    content = result.stdout.decode('utf-8')
    if isJson:
        content = json.loads(content)
        writeJSON(filename, content)
    else:
        writeTextFile(filename, content)
    return content

def downloadBinaryFile(url, filename, overwrite=False):
    if os.path.isfile(filename) and not overwrite:
        print("%s already exists." % filename)
        return True
    print("Downloading %s..." % url)
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        shutil.copyfileobj(response.raw, f)
    del response

def downloadFileFromUrl(url, filename, overwrite=False, verbose=True):
    if os.path.isfile(filename) and not overwrite:
        if verbose:
            print("%s already exists." % filename)
        return readTextFile(filename)

    if verbose:
        print(f'Downloading {url} to {filename}...')
    r = requests.get(url)
    contents = r.text

    with open(filename, "w", encoding="utf8", errors="replace") as f:
        f.write(contents)

    return contents

def downloadJSONFromURL(url, filename, overwrite=False, save=True):
    if save and os.path.isfile(filename) and not overwrite:
        return readJSON(filename)

    print("Downloading %s" % url)
    data = {}
    try:
        r = requests.get(url)
        data = r.json()
        if save:
            writeJSON(filename, data)
    except json.decoder.JSONDecodeError:
        print("Decode error for %s" % url)
        data = {}
    return data

def getBasename(fn):
    return os.path.splitext(os.path.basename(fn))[0]

def getFileExt(fn):
    basename = os.path.basename(fn)
    return "." + basename.split(".")[-1]

def getFilenames(fileString, verbose=True):
    files = []
    if "*" in fileString:
        files = glob.glob(fileString)
    else:
        files = [fileString]
    fileCount = len(files)
    files = sorted(files)
    if verbose:
        print("Found %s files" % fileCount)
    return files

def makeDirectories(filenames):
    if not isinstance(filenames, list):
        filenames = [filenames]
    for filename in filenames:
        dirname = os.path.dirname(filename)
        if len(dirname) > 0 and not os.path.exists(dirname):
            os.makedirs(dirname)

def parseHeadings(arr, headings):
    newArr = []
    headingKeys = [key for key in headings]
    for i, item in enumerate(arr):
        newItem = {}
        for key in item:
            if key in headingKeys:
                newItem[headings[key]] = item[key]
        newArr.append(newItem)
    return newArr

def readCsv(filename, headings=False, doParseNumbers=True, skipLines=0, encoding="utf-8-sig", readDict=True, verbose=True):
    rows = []
    fieldnames = []
    if os.path.isfile(filename):
        lines = []
        with open(filename, 'r', encoding=encoding, errors="replace") as f:
            lines = list(f)
        if skipLines > 0:
            lines = lines[skipLines:]
        if readDict:
            reader = csv.DictReader(lines, skipinitialspace=True)
            fieldnames = list(reader.fieldnames)
        else:
            reader = csv.reader(lines, skipinitialspace=True)
        rows = list(reader)
        if headings:
            rows = parseHeadings(rows, headings)
        if doParseNumbers:
            rows = parseNumbers(rows)
        if verbose:
            print("  Read %s rows from %s" % (len(rows), filename))
    return (fieldnames, rows)

def readJSON(filename):
    data = {}
    if os.path.isfile(filename):
        with open(filename, encoding="utf8") as f:
            data = json.load(f)
    return data

def readTextFile(filename):
    contents = ""
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf8", errors="replace") as f:
            contents = f.read()
    return contents

def removeDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)

def removeFiles(listOrString):
    filenames = listOrString
    if not isinstance(listOrString, list) and "*" in listOrString:
        filenames = glob.glob(listOrString)
    elif not isinstance(listOrString, list):
        filenames = [listOrString]
    print("Removing %s files" % len(filenames))
    for fn in filenames:
        if os.path.isfile(fn):
            os.remove(fn)

def replaceFileExtension(fn, newExt):
    extLen = len(getFileExt(fn))
    i = len(fn) - extLen
    return fn[:i] + newExt

def unzipFile(fn, dataFile=None, targetDir="tmp/", overwrite=False):
    basename = getBasename(fn)
    extractTo = targetDir + basename
    extractedFile = extractTo if dataFile is None else extractTo + "/" + dataFile
    if os.path.isdir(extractTo) and not overwrite:
        print(f'  {extractTo} already exists, skipping')
        return extractedFile
    if os.path.isdir(extractTo) and overwrite:
        print(f'  {extractTo} already exists, removing existing files before extracting')
        removeDir(extractTo)
    with zipfile.ZipFile(fn, 'r') as f:
        f.extractall(extractTo)
    return extractedFile

def writeCsv(filename, arr, headings="auto", append=False, encoding="utf8", verbose=True, listDelimeter=" | "):
    if headings == "auto":
        headings = arr[0].keys() if len(arr) > 0 and type(arr[0]) is dict else None
    mode = 'w' if not append else 'a'
    with open(filename, mode, encoding=encoding, newline='') as f:
        writer = csv.writer(f)
        if not append and headings is not None:
            writer.writerow(headings)
        for i, d in enumerate(arr):
            row = []
            if headings is not None:
                for h in headings:
                    value = ""
                    if h in d:
                        value = d[h]
                    if isinstance(value, list):
                        value = listDelimeter.join(value)
                    row.append(value)
            else:
                row = d
            writer.writerow(row)
    if verbose:
        print("Wrote %s rows to %s" % (len(arr), filename))

def writeJSON(filename, data, verbose=True, pretty=False):
    with open(filename, 'w') as f:
        if pretty:
            json.dump(data, f, indent=4)
        else:
            json.dump(data, f)
        if verbose:
            print("Wrote data to %s" % filename)

def writeTextFile(filename, text):
    with open(filename, "w", encoding="utf8", errors="replace") as f:
        f.write(text)
