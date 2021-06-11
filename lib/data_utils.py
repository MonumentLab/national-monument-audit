# -*- coding: utf-8 -*-

from lib.collection_utils import *
from lib.math_utils import *
from lib.string_utils import *

def applyDataTypeConditions(rows, dataType, allowMany=False, reasonKey=None, scoreKey=None):
    conditionRows = []
    remainingRows = []
    name = dataType["name"]
    value = dataType["value"]
    score = dataType["score"] if "score" in dataType else 0

    if "remainder" in dataType:
        for row in rows:
            row[name] = value
            conditionRows.append(row)
        return (conditionRows, remainingRows)

    conditions = dataType["conditions"]
    for _row in rows:
        row = _row.copy()
        isValid = False
        reasons = []
        rowEnts = row["_entities"] if "_entities" in row else []
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
            if "precededBy" in cond:
                _phrases = []
                for phrase in phrases:
                    for pword in cond["precededBy"]:
                        _phrases.append(pword + " " + phrase)
                phrases = _phrases
            if "followedBy" in cond:
                _phrases = []
                for phrase in phrases:
                    for fword in cond["followedBy"]:
                        _phrases.append(phrase + " " + fword)
                phrases = _phrases
            if "entities" in cond and len(rowEnts) > 0:
                validEnts = [ent for ent in rowEnts if ent["Property"] in cond["fields"] and ent["Type"] in cond["entities"]]
                for ent in validEnts:
                    reasons.append(f'{ent["Property"]} field contains possible historic {ent["Type"]}: "{ent["Value"]}"')
                # no valid entity, skip
                if len(validEnts) <= 0:
                    continue
                # if there are no other conditions, this is valid
                elif len(words) <= 0 and len(phrases) <= 0:
                    isValid = True
                    break
            for field in cond["fields"]:
                if field not in row:
                    continue
                rawValue = row[field]
                for word in words:
                    if containsWord(rawValue, word, isFirstWord, isLastWord):
                        if isFirstWord:
                            reasons.append(f'{field} field starts with "{word}"')
                        elif isLastWord:
                            reasons.append(f'{field} field ends with "{word}"')
                        else:
                            reasons.append(f'{field} field contains "{word}"')
                        isValid = True
                        break
                for phrase in phrases:
                    if containsPhrase(rawValue, phrase):
                        reasons.append(f'{field} field contains "{phrase}"')
                        isValid = True
                        break
                if isValid:
                    break
            if isValid:
                break
        if isValid:
            row[name] = value
            if len(reasons) > 0 and reasonKey is not None:
                row[reasonKey] = reasons
            if scoreKey is not None:
                row[scoreKey] = score
            conditionRows.append(row)
        else:
            if scoreKey is not None:
                row[scoreKey] = score
            remainingRows.append(row)

    return (conditionRows, remainingRows)

def applyDuplicationFields(rows, latlonPrecision=1):

    # Lat lon precision is in nth of a degree (e.g. precision of 2 is a hundredth of a degree)
        # In Charlottesville, VA:
        # One degree of latitude ~= 69 miles
        # One degree of longitude ~= 54.6 miles
        # https://www.usgs.gov/faqs/how-much-distance-does-a-degree-minute-and-second-cover-your-maps?qt-news_science_products=0#qt-news_science_products

    # First, add normalized lat/lon and name for grouping
    multiplier = 10 ** latlonPrecision
    decimal = 0.1 ** latlonPrecision
    validRows = []
    for i, row in enumerate(rows):
        lat = roundInt(roundToNearest(row["Latitude"] * multiplier, decimal)) if "Latitude" in row and isNumber(row["Latitude"]) else ""
        lon = roundInt(roundToNearest(row["Longitude"] * multiplier, decimal)) if "Longitude" in row and isNumber(row["Longitude"]) else ""
        # exclude entries with only approximated
        if lat == "" or lon == "" or row["Geo Type"] not in ("Exact coordinates provided", "Geocoded based on street address provided"):
            continue
        nname = normalizeName(row["Name"])
        # In this case: (World War I Memorial), (sculpture)
        # We want: World War I Memorial
        if nname == "" and "(" in row["Name"] and ")" in row["Name"]:
            matches = getValuesInParentheses(row["Name"])
            if matches and len(matches) > 0:
                nname = normalizeName(matches[0])
        if nname == "":
            nname = row["Name"]
        row["_latlonGroup"] = (lat, lon)
        row["_nameGroup"] = nname
        row["_index"] = i
        row["_isMonument"] = 1 if "Object Groups" in row and row["Object Groups"] == "Monument" or isinstance(row["Object Groups"], list) and "Monument" in row["Object Groups"] else 0
        validRows.append(row)

    # group items by lat/lon
    itemsByLatLon = groupList(validRows, "_latlonGroup")
    groupCount = len(itemsByLatLon)
    duplicateRows = []
    duplicateCount = 0
    for i, latlonGroup in enumerate(itemsByLatLon):
        nameGroups = {}

        ## group items by name
        # nameGroups = groupList(latlonGroup["items"], "_nameGroup")

        # sort by string length (desc) so that e.g. "Caddo Parish Confederate Monument" comes before "Confederate Monument"
        # give priority to monuments
        items = sorted(latlonGroup["items"], key=lambda item: (-item["_isMonument"], -len(item["_nameGroup"])))

        for item in items:
            nname = item["_nameGroup"]
            if nname in nameGroups:
                nameGroups[nname]["items"].append(item)
                continue
            foundSimilar = False
            for value in nameGroups:
                # if this contains or is contained by existing value, e.g. "Lincoln Memorial" and "The Lincoln Memorial"
                if value in nname or nname in value:
                    nameGroups[value]["items"].append(item)
                    foundSimilar = True
                    break
            if not foundSimilar:
                nameGroups[nname] = {
                    "items": [item],
                    "_nameGroup": nname
                }

        for nameKey, nameGroup in nameGroups.items():
            if len(nameGroup["items"]) <= 1:
                continue

            # ignore items with no name or "untitled"
            if nameGroup["_nameGroup"] in ("untitled", "unknown") or nameGroup["_nameGroup"] == "":
                continue

            itemsSortedByPriority = sorted(nameGroup["items"], key=lambda item: item["Source Priority"])
            primaryRecord = itemsSortedByPriority[0]

            itemsBySource = groupList(itemsSortedByPriority, "Vendor ID")
            # all items are from the same source and the source is official, assume they are not duplicates
            # if len(itemsBySource) <= 1 and primaryRecord["Source Type"] == "Official":
            #     continue

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

def mergeDuplicates(rows, dataFields):
    rows = addIndices(rows, keyName="_index")
    drows = [row for row in rows if "Has Duplicates" in row and row["Has Duplicates"] == 1 or "Is Duplicate" in row and row["Is Duplicate"] == 1]

    for i, row in enumerate(drows):
        group = row["Id"]
        if "Is Duplicate" in row and row["Is Duplicate"] == 1 and "Duplicate Of" in row:
            group = row["Duplicate Of"]
        drows[i]["_duplicateGroup"] = group
        # Give lower priority to items that had geocoded addresses
        if row["Geo Type"] != "Exact coordinates provided":
            drows[i]["Source LatLon Priority"] = 1000

    fieldListsToMerge = [f["key"] for f in dataFields if "type" in f and f["type"] == "string_list"] # merge these field names as lists

    itemsByDuplicationGroup = groupList(drows, "_duplicateGroup")
    for group in itemsByDuplicationGroup:
        if len(group["items"]) <= 1:
            continue

        itemsSortedByPriority = sorted(group["items"], key=lambda item: item["Source Priority"])
        itemsSortedByLatLonPriority = sorted(group["items"], key=lambda item: item["Source LatLon Priority"])

        mergedItem = itemsSortedByPriority[0].copy() # source with the highest priority should be the default

        # create a new Id

        mergedItem["Id"] = str(mergedItem["Id"]) + "_merged"
        mergedItem["Vendor Entry ID"] = mergedItem["Id"]

        # update source/sources
        mergedItem["Source"] = "Multiple"
        mergedItem["Sources"] = [item["Source"] for item in itemsSortedByPriority]

        # update lat/lon in the first availabile lat/lon sorted by source lat/lon priority
        for item in itemsSortedByLatLonPriority:
            lat = item["Latitude"] if "Latitude" in item and isNumber(item["Latitude"]) else ""
            lon = item["Longitude"] if "Longitude" in item and isNumber(item["Longitude"]) else ""
            # exclude entries with only approximated
            if lat == "" or lon == "" or item["Geo Type"] not in ("Exact coordinates provided", "Geocoded based on street address provided"):
                continue
            # update lat/lon, geo type, county geoid
            mergedItem["Latitude"] = lat
            mergedItem["Longitude"] = lon
            mergedItem["Geo Type"] = item["Geo Type"]
            countyGeoId = mergedItem["County GeoId"] if "County GeoId" in mergedItem else ""
            countyGeoId = item["County GeoId"] if "County GeoId" in item and item["County GeoId"] != "" else countyGeoId
            mergedItem["County GeoId"] = countyGeoId
            break

        # merge list fields
        for field in fieldListsToMerge:
            values = []
            for item in itemsSortedByPriority:
                if field not in item:
                    continue
                value = item[field]
                if isinstance(value, list):
                    values += value
                else:
                    values.append(value)
            if len(values) > 0:
                values = unique(values)
                mergedItem[field] = values

        # update duplication fields
        mergedItem["Is Duplicate"] = 0
        mergedItem["Has Duplicates"] = 1
        mergedItem["Duplicates"] = [item["Id"] for item in itemsSortedByPriority]
        mergedItem["Duplicate Of"] = ""

        # update child items
        for item in itemsSortedByPriority:
            rows[item["_index"]]["Is Duplicate"] = 1
            rows[item["_index"]]["Has Duplicates"] = 0
            rows[item["_index"]]["Duplicates"] = []
            rows[item["_index"]]["Duplicate Of"] = mergedItem["Id"]

        # add alternate name if applicable
        if "Alternate Name" not in mergedItem or mergedItem["Alternate Name"] == "":
            for item in itemsSortedByPriority:
                if item["Name"] != mergedItem["Name"]:
                    mergedItem["Alternate Name"] = item["Name"]
                    break

        # add remaining fields that don't exist
        for item in itemsSortedByPriority:
            for field in item:
                if field not in mergedItem:
                    mergedItem[field] = item[field]

        # add the new, merged item
        rows.append(mergedItem)

    return rows
