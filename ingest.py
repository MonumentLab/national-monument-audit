# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
from geopy.geocoders import Nominatim
import os
from pprint import pprint
import re
import sys

from lib.collection_utils import *
from lib.geo_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *
from lib.data_utils import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="config/ingest/*.json", help="Input .json config files")
parser.add_argument('-model', dest="DATA_MODEL_FILE", default="config/data-model.json", help="Input .json data model file")
parser.add_argument('-app', dest="APP_DIRECTORY", default="app/", help="App directory")
parser.add_argument('-delimeter', dest="LIST_DELIMETER", default=" | ", help="How lists should be delimited")
parser.add_argument('-geo', dest="GEOCACHE_FILE", default="data/preprocessed/geocoded.csv", help="Cached csv file for storing geocoded addresses")
parser.add_argument('-ent', dest="ENTITIES_FILE", default="data/preprocessed/monumentlab_national_monuments_audit_entities_for_indexing.csv", help="Input entities file")
parser.add_argument('-county', dest="COUNTIES_GEO_FILE", default="app/data/counties.json", help="County geojson file (generated from make_boundaries.py)")
parser.add_argument('-countycache', dest="COUNTIES_CACHE_FILE", default="data/preprocessed/counties_matched.csv", help="Cached csv file for storing lat/lon matched against county data")
parser.add_argument('-validate', dest="VALIDATION_FILE", default="data/validation_set.csv", help="CSV file of entries for validation")
parser.add_argument('-corrections', dest="CORRECTIONS_FILE", default="data/corrections.csv", help="CSV file of corrections")
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
    if "isDisabled" in data and data["isDisabled"]:
        continue
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
fieldsForEntities = set(dataModel["fieldsForEntities"])
conditionalFieldsForEntities = set(dataModel["conditionalFieldsForEntities"])
dataFields = dataModel["fields"]
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
    dataEncoding = d["dataEncoding"] if "dataEncoding" in d else "utf-8-sig"
    data = []
    for dataPath in dataPaths:
        fData = None
        if dataPath.endswith(".zip"):
            dataFile = d["dataFile"] if "dataFile" in d else None
            dataPath = unzipFile(dataPath, dataFile)
        if dataPath.endswith(".shp") or dataPath.endswith(".dbf") or dataFormat == "shapefile":
            fData = readShapefile(dataPath)
        elif dataPath.endswith(".csv") or dataFormat == "csv":
            fFields, fData = readCsv(dataPath, encoding=dataEncoding)
            # print(dataPath)
            # print(fFields)
            # print('============================')
        if fData is not None and "fileMap" in d:
            for j, row in enumerate(fData):
                fData[j]["_srcFilename"] = os.path.basename(dataPath)
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
    fileMap = d["fileMap"] if "fileMap" in d else None
    firstWarning = True
    uids = [] # keep track of UIDs if we need to merge
    for rowIndex, rowIn in enumerate(data):
        rowOut = {
            "Vendor ID": d["id"],
            "Source": d["name"]
        }
        rowOut[ID_NAME] = str(rowIndex+1) # this should be overwritten by vendor entry ID in source config if present

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

        # set source priority
        if "priority" in d:
            rowOut["Source Priority"] = d["priority"]
        else:
            rowOut["Source Priority"] = 999

        # set source priority
        if "latlonPriority" in d:
            rowOut["Source LatLon Priority"] = d["latlonPriority"]
        else:
            rowOut["Source LatLon Priority"] = 999

        # set source type
        if "sourceType" in d:
            rowOut["Source Type"] = d["sourceType"]
        else:
            rowOut["Source Type"] = "Official"

        # inherit object type defaults
        if "objectTypes" in d:
            rowOut["Object Types"] = d["objectTypes"]

        # check for file-specific metadata
        if fileMap is not None and rowIn["_srcFilename"] in fileMap:
            for prop, value in fileMap[rowIn["_srcFilename"]].items():
                rowOut[prop] = value

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

            # check for string pattern
            if "stringPattern" in propMap:
                stringPattern = propMap["stringPattern"]
                value = stringPattern.format(**rowIn)

            # strip whitespace
            if isinstance(value, str):
                value = value.strip()

            # map this property to another property
            if "to" in propMap:
                toProperty = propMap["to"]

            # check for regex
            if "regex" in propMap:
                match = re.match(toProperty, value)
                if match:
                    matchDict = match.groupdict()
                    rowOut.update(matchDict)
                continue

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

            # else check for timestamp
            elif "isTimestamp" in propMap:
                isMilliseconds = ("isMilliseconds" in propMap)
                yearValue = timestampToYear(value, isMilliseconds)
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

            # check to see if property is already set; if so, add it as a list (exclude identifiers)
            if toProperty in rowOut and toProperty != ID_NAME:
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

    # Validate lat/lon
    if "Latitude" in row and (not isNumber(row["Latitude"]) or row["Latitude"] <= 0):
        if not isNumber(row["Latitude"]) and len(row["Latitude"]) > 0:
            print(f' ** Warning: Invalid latitude: {row["Latitude"]}')
        rowsOut[i]["Latitude"] = ""
        rowsOut[i]["Longitude"] = ""

# states = unique([row["State"] for row in rowsOut if "State" in row])
# pprint(states)

# Validate entries
print("Validating rows...")
validRows = []
uids = set([])
vendorDupes = {}
for row in rowsOut:
    isValid = True
    # validate unique Id
    if row["Id"] is None:
        print(f' ** Warning: No ID for {row["Source"]} / {row[ID_NAME]}')
        continue
    # check for duplicates
    if row["Id"] in uids:
        if row["Vendor ID"] in vendorDupes:
            vendorDupes[row["Vendor ID"]] += 1
        else:
            vendorDupes[row["Vendor ID"]] = 1
        vendorDupeCount = vendorDupes[row["Vendor ID"]]
        if vendorDupeCount <= 25:
            print(f' ** Warning: Duplicate ID: {row["Id"]}')
        continue
    uids.add(row["Id"])
    # check for required fields
    for key, item in dataModel.items():
        if "required" in item and item["required"]:
            if key not in row or str(row[key]).strip() == "":
                isValid = False
                break
    if isValid:
        validRows.append(row)
print("Vendor duplicate stats: ")
pprint(vendorDupes)
rowsOut = validRows

# Validate lat/lon
print("Checking lat/lon data...")
rowsOut = applyGeoTypes(rowsOut)

print("Geocoding data...")
geolocator = Nominatim(user_agent="national-monument-audit/1.0 (brian.foo@monumentlab.com)")
rowsOut = geocodeItems(rowsOut, a.GEOCACHE_FILE, geolocator)
geoValueCounts = getCounts(rowsOut, "Geo Type")
for value, count in geoValueCounts:
    print(f'  {value}: {formatNumber(count)}')

print("Matching lat/lon data against county data...")
_, latlonCountyMatches = readCsv(a.COUNTIES_CACHE_FILE, doParseNumbers=False)
latlonCountyLookup = createLookup(latlonCountyMatches, "latlon")
countyGeoJSON = readJSON(a.COUNTIES_GEO_FILE)
# create a state lookup for county data
countyStateLookup = {}
for feature in countyGeoJSON["features"]:
    geoId = str(feature["properties"]["GEOID"])
    state = fipsToState(str(feature["properties"]["STATEFP"]), defaultValue="")
    countyStateLookup[geoId] = state
countyLookupChanged = False
noCountMatches = 0
rowCount = len(rowsOut)
def saveCountyDataCache(fn, lookup):
    latlonCountyMatches = []
    for latlon, item in lookup.items():
        latlonCountyMatches.append({
            "latlon": latlon,
            "countyGeoId": item["countyGeoId"]
        })
    writeCsv(fn, latlonCountyMatches, headings=["latlon", "countyGeoId"], verbose=False)

setNoStateCount = 0
for i, row in enumerate(rowsOut):
    countyGeoId = "Unknown"
    if row["Geo Type"] in ("Exact coordinates provided", "Geocoded based on street address provided"):
        latlon = f'{row["Latitude"]},{row["Longitude"]}'
        if latlon in latlonCountyLookup:
            countyGeoId = latlonCountyLookup[latlon]["countyGeoId"]
        else:
            matchedFeature = searchPointInGeoJSON(row["Latitude"], row["Longitude"], countyGeoJSON)
            if matchedFeature is not None:
                countyGeoId = str(matchedFeature["properties"]["GEOID"])
                countyLookupChanged = True
            latlonCountyLookup[latlon] = {"countyGeoId": countyGeoId}
            saveCountyDataCache(a.COUNTIES_CACHE_FILE, latlonCountyLookup)
        if countyGeoId == "Unknown":
            noCountMatches += 1
    rowsOut[i]["County GeoId"] = countyGeoId
    # validate state
    geoState = countyStateLookup[countyGeoId] if countyGeoId in countyStateLookup else ""
    originalState = row["State"] if "State" in row else ""
    # set state if not already set
    if geoState != "" and originalState == "":
        url = row["URL"] if "URL" in row else ""
        # print(f' Setting state for {row["Id"]} / {url}: {geoState}')
        rowsOut[i]["State"] = geoState
        setNoStateCount += 1
    printProgress(i+1, rowCount)
print(f' County not matched for {noCountMatches} rows')
print(f' Set state for {setNoStateCount} rows based on lat/lon county')

print("Reading entities...")
entitiesByItem = {}
if os.path.isfile(a.ENTITIES_FILE):
    entFields, entRows = readCsv(a.ENTITIES_FILE)
    for i, entRow in enumerate(entRows):
        entRows[i]["idString"] = str(entRow["Id"])
    entById = groupList(entRows, "idString")
    entLookup = createLookup(entById, "idString")
    for i, row in enumerate(rowsOut):
        docId = str(row["Id"])
        rowsOut[i]["Entities Events"] = ""
        rowsOut[i]["Entities People"] = ""
        rowsOut[i]["Gender Represented"] = ""
        rowsOut[i]["Ethnicity Represented"] = ""
        # Add entities
        if docId in entLookup:
            rowEnts = entLookup[docId]["items"]
            rowsOut[i]["_entities"] = rowEnts # keep track of this for determining monument type
            eventEnts = []
            peopleEnts = []
            genders = []
            ethnicities = []
            for ent in rowEnts:
                value = str(ent["Value"]).strip()
                if len(value) < 1:
                    continue
                originalProperty = ent["Property"]
                if originalProperty not in fieldsForEntities and originalProperty not in conditionalFieldsForEntities:
                    continue
                # only include conditional fields if a word overlaps with the name, e.g. "Tubman Statue"
                if originalProperty in conditionalFieldsForEntities:
                    if not wordsOverlap(value, row["Name"]):
                        continue
                if ent["Type"] == "EVENT" and value not in eventEnts:
                    eventEnts.append(value)
                elif ent["Type"] == "PERSON" and value not in peopleEnts:
                    peopleEnts.append(value)
                    if ent["Gender"] != "" and ent["Gender"] != "NA" and ent["Gender"] not in genders:
                        genders.append(ent["Gender"])
                    if ent["Ethnic Group"] != "" and ent["Ethnic Group"] != "NA" and ent["Ethnic Group"] not in ethnicities:
                        ethnicities.append(ent["Ethnic Group"])

            if len(eventEnts) > 0:
                rowsOut[i]["Entities Events"] = eventEnts

            if len(peopleEnts) > 0:
                rowsOut[i]["Entities People"] = peopleEnts

            if len(genders) > 0:
                rowsOut[i]["Gender Represented"] = genders

            if len(ethnicities) > 0:
                rowsOut[i]["Ethnicity Represented"] = ethnicities
else:
    print("Warning: no entities file found; run `python extract_entities.py && python normalize_entities.py && python resolve_entities.py && python visualize_entities.py` to generate this")

# break down by type
print("Determining types...")
rowsByDataType = {}
for dataTypeGroup in dataTypes:
    name = dataTypeGroup["key"]
    rowsByDataType[name] = {}
    allowMany = "allowMany" in dataTypeGroup and dataTypeGroup["allowMany"] > 0
    reasonKey = dataTypeGroup["reasonKey"] if "reasonKey" in dataTypeGroup else None
    scoreKey = dataTypeGroup["scoreKey"] if "scoreKey" in dataTypeGroup else None
    print(f'  {name}...')
    remainingRows = rowsOut[:]
    updatedRows = []
    ruleCount = len(dataTypeGroup["rules"])
    for j, _rule in enumerate(dataTypeGroup["rules"]):
        rule = _rule.copy()
        rule["name"] = name
        conditionRows, remainingRows = applyDataTypeConditions(remainingRows, rule, allowMany, reasonKey, scoreKey)
        updatedRows += conditionRows
        if len(conditionRows) > 0:
            if rule["value"] in rowsByDataType[name]:
                rowsByDataType[name][rule["value"]] += conditionRows
            else:
                rowsByDataType[name][rule["value"]] = conditionRows
        printProgress(j+1, ruleCount, prepend="  ")
    if len(remainingRows) > 0:
        updatedRows += remainingRows
    rowsOut = updatedRows[:]

print("Looking for duplicates...")
duplicateCount, duplicateRows, rowsOut = applyDuplicationFields(rowsOut)

print("Merging duplicates...")
rowsOut = mergeDuplicates(rowsOut, dataFields)

# Set "Sources" if not set
for i, row in enumerate(rowsOut):
    if "Sources" not in row:
        rowsOut[i]["Sources"] = [row["Source"]]

# Add corrections
if os.path.isfile(a.CORRECTIONS_FILE):
    _, corrections = readCsv(a.CORRECTIONS_FILE)
    idLookup = {}
    for i, row in enumerate(rowsOut):
        idLookup[row["Id"]] = i
    for correction in corrections:
        if correction["Id"] not in idLookup:
            print(f'Could not find Id {correction["Id"]} in corrections')
            continue
        index = idLookup[correction["Id"]]
        value = correction["Correct Value"]
        svalue = str(value)
        if a.LIST_DELIMETER in svalue:
            value = [v.strip() for v in svalue.split(a.LIST_DELIMETER)]
        rowsOut[index][correction["Field"]] = value

if a.PROBE:
    sys.exit()

################################################################
# Write processed data to .csv file
################################################################
fieldsOut = ["Id", "Vendor ID", ID_NAME]
for row in rowsOut:
    for field in row:
        if field not in fieldsOut and not field.startswith("_"):
            fieldsOut.append(field)
makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, rowsOut, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

# write duplicate rows
writeCsv(appendToFilename(a.OUTPUT_FILE, "_duplicates"), duplicateRows, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

print("Writing validation rows...")
validationHeadings, validationRows = readCsv(a.VALIDATION_FILE)
if len(validationRows) > 0:
    validationRows = addIndices(validationRows, "_index")
    validationLookup = createLookup(validationRows, "Id")
    validCount = 0
    for row in rowsOut:
        if row["Id"] in validationLookup:
            vrow = validationLookup[row["Id"]]
            validationRows[vrow["_index"]]["Current Type"] = row["Object Groups"]
            validationRows[vrow["_index"]]["Valid"] = "Yes" if row["Object Groups"] == vrow["Expected Type"] else "No"
            if validationRows[vrow["_index"]]["Valid"] == "Yes":
                validCount += 1
    print(f'{round(1.0 * validCount / len(validationRows) * 100, 2)}% valid')
    writeCsv(a.VALIDATION_FILE, validationRows, validationHeadings)

# write type-specific output
for fieldValue, fieldTypes in rowsByDataType.items():
    for typeValue, typeRows in fieldTypes.items():
        appendString = "_" + stringToId(fieldValue) + "_" + stringToId(typeValue)
        writeCsv(appendToFilename(a.OUTPUT_FILE, appendString), typeRows, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

# write monument-score-specific output
rowsByScore = groupList(rowsOut, "Monument Score")
for scoreGroup in rowsByScore:
    if scoreGroup["Monument Score"] < 1:
        continue
    outScoreFilename = appendToFilename(a.OUTPUT_FILE, f'_monuments_{scoreGroup["Monument Score"]}')
    writeCsv(outScoreFilename, scoreGroup["items"], headings=["Id", "Vendor Id", "Name", "Alternate Name", "Object Group Reason", "Monument Score", "Object Types", "Use Types", "Subjects", "Text", "Description"], listDelimeter=a.LIST_DELIMETER)

# write source-specific output
rowsBySource = groupList(rowsOut, "Source")
for sourceGroup in rowsBySource:
    outSourceFilename = OUTPUT_DIR + "vendor/" + stringToId(sourceGroup["Source"]) + ".csv"
    makeDirectories(outSourceFilename)
    writeCsv(outSourceFilename, sourceGroup["items"], headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

monumentRows = rowsByDataType["Object Groups"]["Monument"]

# output just monument subjects
monumentSubjects = []
for record in monumentRows:
    if "Subjects" in record:
        subject = record["Subjects"]
        if isinstance(subject, list):
            monumentSubjects += subject
        else:
            monumentSubjects.append(subject)
monumentSubjectCounts = getCounts(monumentSubjects)
writeCsv(OUTPUT_DIR + "monumentlab_national_monuments_audit_final_monument_subjects.csv", [{"value": value, "count": count} for value, count in monumentSubjectCounts], ["value", "count"])

# output uncategorized monument types
uncategorizedMonuments = rowsByDataType["Monument Types"]["Uncategorized"]
uncategorizedObjectTypes = []
for record in uncategorizedMonuments:
    if "Object Groups" not in record or "Object Types" not in record:
        continue
    objectGroup = record["Object Groups"]
    if isinstance(objectGroup, list):
        objectGroup = objectGroup[0]
    if objectGroup != "Monument":
        continue
    objectTypes = record["Object Types"]
    if isinstance(objectTypes, list):
        uncategorizedObjectTypes += objectTypes
    else:
        uncategorizedObjectTypes.append(objectTypes)
uncategorizedValueCounts = getCounts(uncategorizedObjectTypes)
writeCsv(OUTPUT_DIR + "monumentlab_national_monuments_audit_final_monument_object_types_uncategorized.csv", [{"value": value, "count": count} for value, count in uncategorizedValueCounts], ["value", "count"])

################################################################
# Generate dashboard data
################################################################

rowsWithoutMergedRecords = [row for row in rowsOut if "Has Duplicates" not in row or row["Has Duplicates"] < 1]
rowsWithoutDupes = [row for row in rowsOut if "Is Duplicate" not in row or row["Is Duplicate"] < 1]
duplicateRows = [row for row in rowsOut if "Is Duplicate" in row and row["Is Duplicate"] == 1]

# dashboard summary numbers
dataSourceTotal = len(dataSources)
dataRecordTotal = len(rowsWithoutMergedRecords)
summaryData = {}
summaryData["dataSourceTotal"] = formatNumber(dataSourceTotal)
summaryData["dataRecordTotal"] = formatNumber(dataRecordTotal)
summaryData["dataRecordAverage"] = formatNumber(round(1.0 * dataRecordTotal / dataSourceTotal))
summaryData["dataRecordDuplicates"] = formatNumber(len(duplicateRows))

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
