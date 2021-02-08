# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.geo_utils import *
from lib.io_utils import *
from lib.string_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="config/ingest/*.json", help="Input .json config files")
parser.add_argument('-model', dest="DATA_MODEL_FILE", default="config/data-model.json", help="Input .json data model file")
parser.add_argument('-app', dest="APP_DIRECTORY", default="app/", help="App directory")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/compiled/monumentlab_national_monuments_audit_final.csv", help="Output csv file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output details and don't write data?")
a = parser.parse_args()
# Parse arguments

OUTPUT_DIR = os.path.dirname(a.OUTPUT_FILE) + "/"

################################################################
# Read config JSON FILES
################################################################
filenames = getFilenames(a.INPUT_FILE)
dataSources = []
for fn in filenames:
    data = readJSON(fn)
    data["configFile"] = fn.replace("\\", "/")
    dataSources.append(data)

################################################################
# Read data model
################################################################
dataModel = readJSON(a.DATA_MODEL_FILE)
idField = findByValue(dataModel["fields"], "identifier", True)
if idField is None:
    print("Could not find identifier in data model")
    sys.exit()
ID_NAME = idField["key"]
dataTypes = dataModel["types"]
dataModel = createLookup(dataModel["fields"], "key")

################################################################
# Parse raw data and do light processing
################################################################
rowsOut = []
for dSourceIndex, d in enumerate(dataSources):
    print("------------------------")
    print(f'Processing {d["name"]}')

    # Read data
    dataPaths = getFilenames(d["dataPath"])
    dataFormat = d["dataFormat"] if "dataFormat" in d else None
    dataEncoding = d["dataEncoding"] if "dataEncoding" in d else "utf8"
    data = []
    for dataPath in dataPaths:
        if dataPath.endswith(".zip"):
            dataFile = d["dataFile"] if "dataFile" in d else None
            dataPath = unzipFile(dataPath, dataFile)
        if dataPath.endswith(".shp") or dataPath.endswith(".dbf") or dataFormat == "shapefile":
            fData = readShapefile(dataPath)
        elif dataPath.endswith(".csv") or dataFormat == "csv":
            fFields, fData = readCsv(dataPath, encoding=dataEncoding)
        data += fData
    if len(dataPaths) > 1:
        print(f' {len(data)} total records found')
    dataSources[dSourceIndex]['recordCountBeforeFiltering'] = len(data)

    # check for additional data from pre-processes
    additionalData = None
    if "additionalData" in d:
        print(" Parsing additional data...")
        additionalData = []
        for pathString in d["additionalData"]:
            dataPaths = getFilenames(pathString)
            for dataPath in dataPaths:
                _, fData = readCsv(dataPath)
                additionalData += fData
        # create a look-up dictionary based on ID
        print(f' Found {len(additionalData)} rows of additional data.')
        additionalData = createLookup(additionalData, ID_NAME)

    if len(data) <= 0:
        print(" No data found, skipping.")
        continue

    if "filter" in d:
        data = filterByQueryString(data, d["filter"])
        print(f'  {len(data)} records after filtering')
    dataSources[dSourceIndex]['recordCount'] = len(data)

    mappings = d["mappings"] if "mappings" in d else {}
    firstWarning = True
    uids = [] # keep track of UIDs if we need to merge
    for rowIn in data:
        rowOut = {
            "Vendor ID": d["id"],
            "Source": d["name"]
        }

        # merge with additional data
        if additionalData is not None:
            idName = None
            for k, v in mappings.items():
                if "to" in v and v["to"] == ID_NAME:
                    idName = k
                    break
            if idName is not None:
                id = str(rowIn[idName])
                if id in additionalData:
                    rowIn.update(additionalData[id])

        # inherit city/count/state from dataset metadata as defaults
        if "state" in d:
            rowOut["State"] = d["state"]
        if "county" in d:
            rowOut["County"] = d["county"]
        if "city" in d:
            rowOut["City"] = d["city"]

        for prop in d["properties"]:
            if prop not in rowIn:
                if firstWarning:
                    print(f'  Warning: "{prop}" property not found')
                    firstWarning = False
                continue

            value = rowIn[prop]
            toProperty = prop
            propMap = mappings[prop] if prop in mappings else {}
            dtype = propMap["dtype"] if "dtype" in propMap else None

            # strip whitespace
            if isinstance(value, str):
                value = value.strip()

            # map this property to another property
            if "to" in propMap:
                toProperty = propMap["to"]

            if "valueMaps" in propMap and isinstance(value, str) and value in propMap["valueMaps"]:
                value = propMap["valueMaps"][value]

            # Interpret coordinates as lat lon
            if toProperty == "Coordinates":
                lat = lon = None
                try:
                    lat, lon = tuple([float(v.strip()) for v in str(value).split(",")])
                except ValueError:
                    lat = ""
                    lon = ""
                rowOut["Latitude"] = lat
                rowOut["Longitude"] = lon
                continue

            # Convert UTM to lat lon
            if toProperty == "UTM":
                easting = value
                northing = rowIn[propMap["utmNorthing"]]
                zoneNumber = rowIn[propMap["utmZone"]]
                lat = lon = None
                lat, lon = utmToLatLon(easting, northing, zoneNumber, northern=True)
                rowOut["Latitude"] = lat
                rowOut["Longitude"] = lon
                continue

            # check for empty string
            if value == "" and toProperty not in rowOut and toProperty:
                rowOut[toProperty] = value
                continue

            # check for formatting
            if toProperty in dataModel:
                propModel = dataModel[toProperty]
                if "format" in propModel:
                    for formatType in propModel["format"]:
                        if formatType == "title":
                            value = validateTitleString(value)
                        elif formatType == "name":
                            value = validateNameString(value)
                        elif formatType == "state":
                            value = validateStateString(value)

            # check to see if this is a list
            if "delimeter" in propMap:
                value = [v.strip() for v in re.split(propMap["delimeter"], str(value))]
                value = [v for v in value if len(v) > 0] # remove blanks

            # parse date, convert to year
            if "dateFormat" in propMap:
                dt = None
                # no support for list of dates yet
                if isinstance(value, list):
                    value = value[0]
                try:
                    dt = datetime.strptime(str(value).strip(), propMap["dateFormat"])
                except ValueError:
                    dt = False
                if not dt:
                    value = ""
                else:
                    value = int(dt.strftime("%Y"))

            # else if marked as year, try to extract year
            elif "year" in propMap:
                yearValue = None
                if isinstance(value, list):
                    value = value[0]
                yearValue = stringToYear(value)
                value = yearValue if yearValue is not None else ""

            # parse bool
            if dtype == "bool":
                value = str(value).lower()
                trueValues = ["yes", "y", "true"] if "trueValues" not in propMap else propMap["trueValues"]
                if value in trueValues:
                    value = "y"
                else:
                    value = "n"

            if "mapValues" in propMap:
                for fromValue in propMap["mapValues"]:
                    if value == fromValue:
                        value = propMap["mapValues"][fromValue]

            # check to see if property is already set; if so, add it as a list
            if toProperty in rowOut:
                existingValue = rowOut[toProperty]
                if not isinstance(value, list):
                    value = [value]
                if not isinstance(existingValue, list):
                    existingValue = [existingValue]
                uValues = unique(existingValue + value)
                uValues = [v for v in uValues if len(str(v)) > 0]
                rowOut[toProperty] = uValues
            else:
                rowOut[toProperty] = value

        if "needsMerge" in d and d["needsMerge"] and ID_NAME in rowOut:
            uid = rowOut[ID_NAME]
            if uid not in uids:
                uids.append(uid)
            # skip if already found
            else:
                dataSources[dSourceIndex]['recordCount'] -= 1
                continue

        rowsOut.append(rowOut)

# Post processing
for i, row in enumerate(rowsOut):
    # Add Unique ID
    rowsOut[i]["Id"] = itemToId(row)

    # Create a combined year field
    year = ""
    if "Year Dedicated" in row and parseYear(row["Year Dedicated"]) is not False:
        year = row["Year Dedicated"]
    elif "Year Constructed" in row and parseYear(row["Year Constructed"]) is not False:
        year = row["Year Constructed"]
    rowsOut[i]["Year Dedicated Or Constructed"] = year

    # Make alternate name the primary name if no name exists
    if "Name" in row and "Alternate Name" in row and len(str(row["Name"])) < 1 and len(str(row["Alternate Name"])) > 0:
        rowsOut[i]["Name"] = str(row["Alternate Name"])
        rowsOut[i]["Alternate Name"] = ""

# states = unique([row["State"] for row in rowsOut if "State" in row])
# pprint(states)

# Validate entries
print("Validating rows...")
validRows = []
uids = []
for row in rowsOut:
    isValid = True
    # validate unique Id
    if row["Id"] is None:
        print(f' ** Warning: No ID for {row["Source"]} / {row["Vendor Entry ID"]}')
        continue
    # check for duplicates
    if row["Id"] in uids:
        print(f' ** Warning: Duplicate ID: {row["Id"]}')
        continue
    uids.append(row["Id"])
    # check for required fields
    for key, item in dataModel.items():
        if "required" in item and item["required"]:
            if key not in row or str(row[key]).strip() == "":
                isValid = False
                break
    if isValid:
        validRows.append(row)
rowsOut = validRows

# break down by type

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
            for word in cond["words"]:
                words.append(word)
                if pluralize:
                    pword = pluralizeString(word)
                    if pword != word:
                        words.append(pword)
            for field in cond["fields"]:
                if field not in row:
                    continue
                rawValue = row[field]
                for word in words:
                    if containsWord(rawValue, word, isFirstWord, isLastWord):
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

print("Determining monument types...")
dateTypeGroups = groupList(dataTypes, "name")
rowsByDataType = {}
for dataTypeGroup in dateTypeGroups:
    name = dataTypeGroup["name"]
    remainingRows = rowsOut[:]
    updatedRows = []
    for dataType in dataTypeGroup["items"]:
        conditionRows, remainingRows = applyDataTypeConditions(remainingRows, dataType)
        updatedRows += conditionRows
        if len(conditionRows) > 0:
            rowsByDataType[dataType["value"]] = conditionRows
    if len(remainingRows) > 0:
        updatedRows += remainingRows
    rowsOut = updatedRows[:]

if a.PROBE:
    sys.exit()

################################################################
# Write processed data to .csv file
################################################################
fieldsOut = ["Id", "Vendor ID", "Vendor Entry ID"]
for row in rowsOut:
    for field in row:
        if field not in fieldsOut:
            fieldsOut.append(field)
makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, rowsOut, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

# write type-specific output
for typeValue, typeRows in rowsByDataType.items():
    appendString = "_" + stringToId(typeValue)
    writeCsv(appendToFilename(a.OUTPUT_FILE, appendString), typeRows, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

monumentRows = rowsByDataType["Conventional monument"]

################################################################
# Generate dashboard data
################################################################

# dashboard summary numbers
dataSourceTotal = len(dataSources)
dataRecordTotal = len(rowsOut)
summaryData = {}
summaryData["dataSourceTotal"] = formatNumber(dataSourceTotal)
summaryData["dataRecordTotal"] = formatNumber(dataRecordTotal)
summaryData["dataRecordAverage"] = formatNumber(round(1.0 * dataRecordTotal / dataSourceTotal))

################################################################
# Generate data source data
################################################################

for i, d in enumerate(dataSources):
    dataSources[i]["percentOfTotal"] = round(1.0 * d["recordCount"] / dataRecordTotal * 100, 3)
dataSources = sorted(dataSources, key=lambda s: s["recordCount"], reverse=True)

################################################################
# Generate pie chart data
################################################################

availabilityData = {}
locData = []
for row in rowsOut:
    if "Latitude" in row and row["Latitude"] != "" and row["Latitude"] > 0:
        locData.append({"value": "yes"})
    else:
        locData.append({"value": ""})
geographicResolutionData = getCountPercentages(locData, "value", presence=True)
availabilityData["data-field-availability-location"] = {
    "title": "Lat/lon available?",
    "values": [d["percent"] for d in geographicResolutionData],
    "labels": [d["value"] for d in geographicResolutionData]
}
availabilityConfig = [
    {"srcKey": "Year Dedicated Or Constructed", "outKey": "data-field-availability-date"},
    {"srcKey": "Honorees", "outKey": "data-field-availability-honoree"},
    {"srcKey": "Creators", "outKey": "data-field-availability-creator"},
    {"srcKey": "Sponsors", "outKey": "data-field-availability-sponsor"},
    {"srcKey": "Status", "outKey": "data-field-availability-status"},
    {"srcKey": "Text", "outKey": "data-field-availability-text"}
]
for row in availabilityConfig:
    pdata = getCountPercentages(rowsOut, row["srcKey"], presence=True)
    availabilityData[row["outKey"]] = {
        "title": f'{row["srcKey"]} available?',
        "values": [d["percent"] for d in pdata],
        "labels": [d["value"] for d in pdata]
    }

################################################################
# Generate record value top frequencies
################################################################

showTop = 10
freqData = []
freqConfig = [
    {"srcKey": "Creators", "filename": "monumentlab_national_monuments_audit_final_creators.csv"},
    {"srcKey": "Subjects", "filename": "monumentlab_national_monuments_audit_final_subjects.csv"},
    {"srcKey": "Object Types", "filename": "monumentlab_national_monuments_audit_final_object_types.csv"},
    {"srcKey": "Use Types", "filename": "monumentlab_national_monuments_audit_final_use_types.csv"},
    {"srcKey": "Honorees", "filename": "monumentlab_national_monuments_audit_final_honorees.csv"},
    {"srcKey": "Sponsors", "filename": "monumentlab_national_monuments_audit_final_sponsors.csv"},
    {"srcKey": "Status", "filename": "monumentlab_national_monuments_audit_final_status.csv"}
]
allCounts = {}
for row in freqConfig:
    values = []
    for record in rowsOut:
        if row["srcKey"] in record:
            value = record[row["srcKey"]]
            if isinstance(value, list):
                values += value
            else:
                values.append(value)
    valueCounts = getCounts(values)
    # write to file
    countsOutFile = OUTPUT_DIR + row["filename"]
    writeCsv(countsOutFile, [{"value": value, "count": count} for value, count in valueCounts], ["value", "count"])
    # show top 10
    rowFreqData = []
    for i, valueCount in enumerate(valueCounts):
        value, count = valueCount
        if isinstance(value, str):
            value = value.strip()
            if len(value) < 1:
                value = "&lt;blank&gt;"
        rowFreqData.append([value, formatNumber(count)])
        if len(rowFreqData) >= showTop:
            break
    # calculate "other" row
    if len(valueCounts) > showTop:
        otherCounts = list(valueCounts)
        otherCounts = otherCounts[showTop:]
        otherSum = sum([count for value, count in otherCounts])
        rowFreqData.append([f'{formatNumber(len(otherCounts))} other values', formatNumber(otherSum)])
    displayTop = min(showTop, len(valueCounts))
    freqData.append({
        "title": f'Top {displayTop} values for "{row["srcKey"]}"',
        "rows": rowFreqData,
        "cols": ["Value", "Count"],
        "resourceLink": row["filename"]
    })
    allCounts[row["srcKey"]] = valueCounts

jsonOut = {}
jsonOut["summary"] = summaryData
jsonOut["sources"] = dataSources
jsonOut["availabilities"] = availabilityData
# jsonOut["frequencies"] = freqData # ***** Made obsolete by using the search index instead *****
writeJSON(a.APP_DIRECTORY + "data/dashboard.json", jsonOut)

################################################################
# Generate map data
################################################################

# topSubjects = list(allCounts["Subjects"])
# if len(topSubjects) > 100:
#     topSubjects = topSubjects[:100]
jsonOut = {
    "cols": ["lat", "lon", "source", "year", "id"],
    "groups": {
        "source": [d["name"] for d in dataSources]
        # "subjects": [value for value, count in topSubjects]
    }
}
jsonRows = []
for row in monumentRows:
    lat = -999
    lon = -999
    if "Latitude" in row and row["Latitude"] != "" and row["Latitude"] > 0:
        lat = row["Latitude"]
        lon = row["Longitude"]
    jsonRow = [lat, lon]
    source = jsonOut["groups"]["source"].index(row["Source"])
    year = parseYear(row["Year Dedicated Or Constructed"]) if "Year Dedicated Or Constructed" in row else False
    if year is False:
        year = -1
    id = row[ID_NAME]
    # subjects = []
    # if "Subjects" in row:
    #     subjectValues = row["Subjects"]
    #     if not isinstance(subjectValues, list):
    #         subjectValues = [subjectValues]
    #     for value in subjectValues:
    #         if value in jsonOut["groups"]["subjects"]:
    #             subjects.append(jsonOut["groups"]["subjects"].index(value))
    jsonRow += [source, year, id]
    jsonRows.append(jsonRow)
jsonOut["rows"] = jsonRows
writeJSON(a.APP_DIRECTORY + "data/records.json", jsonOut)
