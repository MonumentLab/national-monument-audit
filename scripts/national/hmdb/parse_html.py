# -*- coding: utf-8 -*-

import argparse
from bs4 import BeautifulSoup
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

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Path to .csv file for hmdb data")
parser.add_argument('-filter', dest="FILTER", default="Source=HMdb", help="Filter query string")
parser.add_argument('-html', dest="HTML_FILE", default="tmp/hmdb_html/%s.html", help="HTML file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/vendor/national/hmdb/hmdb_additional_metadata.csv", help="Where to store additional metadata")
a = parser.parse_args()

fields, rows = readCsv(a.INPUT_FILE)
rowCount = len(rows)

if len(a.FILTER) > 0:
    rows = filterByQueryString(rows, a.FILTER)
    rowCount = len(rows)
    print(f'{rowCount} rows after filtering')

makeDirectories(a.OUTPUT_FILE)

def parseHTMLFile(fn):
    contents = ""

    if not os.path.isfile(fn):
        # print(f'{fn} does not exist; skipping')
        return None

    with open(fn, "r", encoding="utf8", errors="replace") as f:
        contents = f.read()

    if len(contents) < 1:
        print(f'{fn} is empty; skipping')
        return None

    bs = BeautifulSoup(contents, "html.parser")
    isEmpty = True
    item = {
        "Subjects": "",
        "Text": "",
        "Image": "",
        "Images": "",
        "Captions": ""
    }

    # Look for article
    article = bs.find("article", {"class": "bodyserif"})
    if not article:
        print(f'No article found in {fn}; skipping')
        return None

    # Look for inscription
    inscriptionContainer = article.find(id="inscription1")
    if inscriptionContainer:
        isEmpty = False
        item["Text"] = inscriptionContainer.get_text().strip()

    # Look for subjects
    subjects = []
    links = article.find_all("a")
    for link in links:
        href = link.get("href")
        if href and "Search=Topic" in href:
            subject = link.get_text().strip()
            if len(subject) > 0:
                subjects.append(subject)
    if len(subjects) > 0:
        isEmpty = False
        item["Subjects"] = subjects

    # Look for image
    photoContainer = article.find("div", {"class": "photoright"})
    if photoContainer:
        imageTag = photoContainer.find("img", {"class": "photoimage"})
        if imageTag:
            imageSrc = imageTag.get("src")
            if imageSrc:
                path = imageSrc.strip()
                if path and len(path) > 0:
                    url = "https://www.hmdb.org/" + path
                    item["Image"] = url

    # Look for images
    imageTags = article.find_all("img", {"class": "photoimage"})
    images = []
    for imageTag in imageTags:
        imageSrc = imageTag.get("src")
        if imageSrc:
            path = imageSrc.strip()
            if path and len(path) > 0:
                url = "https://www.hmdb.org/" + path
                images.append(url)
    if len(images) > 0:
        item["Images"] = " | ".join(images)

    # Look for image captions
    captionTags = article.find_all("div", {"class": "imagecaption"})
    captions = []
    for captionTag in captionTags:
        caption = captionTag.get_text().strip()
        captions.append(caption)
    if len(captions) > 0:
        item["Captions"] = " | ".join(captions)

    if isEmpty:
        return None

    return item

items = []
for i, row in enumerate(rows):
    id = row['Vendor Entry ID']
    htmlFile = a.HTML_FILE % id
    item = parseHTMLFile(htmlFile)
    if item is not None:
        item["Vendor Entry ID"] = id
        items.append(item)
    printProgress(i+1, rowCount)

writeCsv(a.OUTPUT_FILE, items, headings=["Vendor Entry ID", "Subjects", "Text", "Image", "Images", "Captions"])
