# -*- coding: utf-8 -*-

from lib.collection_utils import *
from lib.math_utils import *
from lib.string_utils import *

def applyDataTypeConditions(rows, dataType):
    conditionRows = []
    remainingRows = []
    name = dataType["name"]
    value = dataType["value"]

    if "remainder" in dataType:
        for row in rows:
            row[name] = value
            conditionRows.append(row)
        return (conditionRows, remainingRows)

    conditions = dataType["conditions"]
    for row in rows:
        isValid = False
        for cond in conditions:
            pluralize = ("pluralize" in cond)
            isFirstWord = ("startswith" in cond)
            isLastWord = ("endswith" in cond)
            words = []
            if "words" in cond:
                for word in cond["words"]:
                    words.append(word)
                    if pluralize:
                        pword = pluralizeString(word)
                        if pword != word:
                            words.append(pword)
            phrases = cond["phrases"] if "phrases" in cond else []
            for field in cond["fields"]:
                if field not in row:
                    continue
                rawValue = row[field]
                for word in words:
                    if containsWord(rawValue, word, isFirstWord, isLastWord):
                        isValid = True
                        break
                for phrase in phrases:
                    if containsPhrase(rawValue, phrase):
                        isValid = True
                        break
                if isValid:
                    break
            if isValid:
                break
        if isValid:
            row[name] = value
            conditionRows.append(row)
        else:
            remainingRows.append(row)

    return (conditionRows, remainingRows)

def applyDuplicationFields(rows, latlonPrecision=2):

    # Lat lon precision is in nth of a degree (e.g. precision of 2 is a hundredth of a degree)
        # In Charlottesville, VA:
        # One degree of latitude ~= 69 miles
        # One degree of longitude ~= 54.6 miles
        # https://www.usgs.gov/faqs/how-much-distance-does-a-degree-minute-and-second-cover-your-maps?qt-news_science_products=0#qt-news_science_products

    # First, add normalized lat/lon and name for grouping
    multiplier = 10 ** latlonPrecision
    validRows = []
    for i, row in enumerate(rows):
        lat = roundInt(row["Latitude"] * multiplier) if "Latitude" in row and isNumber(row["Latitude"]) else ""
        lon = roundInt(row["Longitude"] * multiplier) if "Longitude" in row and isNumber(row["Longitude"]) else ""
        if lat == "" or lon == "":
            continue
        row["_latlonGroup"] = (lat, lon)
        row["_nameGroup"] = normalizeName(row["Name"])
        row["_index"] = i
        validRows.append(row)

    # group items by lat/lon
    itemsByLatLon = groupList(validRows, "_latlonGroup")
    groupCount = len(itemsByLatLon)
    duplicateRows = []
    duplicateCount = 0
    for i, latlonGroup in enumerate(itemsByLatLon):
        # group items by name
        itemsByName = groupList(latlonGroup["items"], "_nameGroup")
        for nameGroup in itemsByName:
            if len(nameGroup["items"]) <= 1:
                continue

            itemsSortedByPriority = sorted(nameGroup["items"], key=lambda item: item["Source Priority"])
            primaryRecord = itemsSortedByPriority[0]

            itemsBySource = groupList(itemsSortedByPriority, "Vendor ID")
            # all items are from the same source and the source is official, assume they are not duplicates
            if len(itemsBySource) <= 1 and primaryRecord["Source Type"] == "Official":
                continue

            duplicateRecords = itemsSortedByPriority[1:]

            # Set fields for primary record
            rows[primaryRecord["_index"]]["Has Duplicates"] = 1
            rows[primaryRecord["_index"]]["Duplicates"] = [record["Id"] for record in duplicateRecords]
            duplicateRows.append(rows[primaryRecord["_index"]].copy())

            # Set fields for duplicate records
            for record in duplicateRecords:
                rows[record["_index"]]["Is Duplicate"] = 1
                rows[record["_index"]]["Duplicate Of"] = primaryRecord["Id"]
                duplicateRows.append(rows[record["_index"]].copy())
                duplicateCount += 1

            # add empty line
            duplicateRows.append({})

        printProgress(i+1, groupCount)

    print(f'{duplicateCount} duplicate records found.')

    return (duplicateCount, duplicateRows, rows)
