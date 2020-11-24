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

# input
parser = argparse.ArgumentParser()
parser.add_argument('-config', dest="INPUT_FILE", default="config/ingest/*.json", help="Input .json config files")
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
    dataSources.append(data)

################################################################
# Parse raw data and do light processing
################################################################
rowsOut = []
for d in dataSources:
    print("------------------------")
    print(f'Processing {d["name"]}')

    # Read data
    dataPath = d["dataPath"]
    dataFormat = d["dataFormat"] if "dataFormat" in d else None
    fields = []
    data = []
    if dataPath.endswith(".zip"):
        dataFile = d["dataFile"] if "dataFile" in d else None
        dataPath = unzipFile(dataPath, dataFile)
    if dataPath.endswith(".shp") or dataPath.endswith(".dbf") or dataFormat == "shapefile":
        data = readShapefile(dataPath)
    elif dataPath.endswith(".csv") or dataFormat == "csv":
        dataEncoding = d["dataEncoding"] if "dataEncoding" in d else "utf8"
        fields, data = readCsv(dataPath, encoding=dataEncoding)

    if len(data) <= 0:
        print(" No data found, skipping.")
        continue

    if "filter" in d:
        data = filterByQueryString(data, d["filter"])
        print(f'  {len(data)} records after filtering')

    mappings = d["mappings"] if "mappings" in d else {}
    firstWarning = True
    for rowIn in data:
        rowOut = {
            "Source": d["name"]
        }

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
                rowOut[toProperty] = existingValue + value
            else:
                rowOut[toProperty] = value
        rowsOut.append(rowOut)

if a.PROBE:
    sys.exit()

################################################################
# Write processed data to .csv file
################################################################
fieldsOut = []
for row in rowsOut:
    for field in row:
        if field not in fieldsOut:
            fieldsOut.append(field)
makeDirectories(a.OUTPUT_FILE)
writeCsv(a.OUTPUT_FILE, rowsOut, headings=fieldsOut, listDelimeter=a.LIST_DELIMETER)

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
# Generate pie chart data
################################################################

pieChartData = {}
# record share
dataSourceRecordShare = getCountPercentages(rowsOut, "Source", otherTreshhold=7)
pieChartData["data-source-share"] = {
    "title": "Share of records by data source",
    "values": [d["percent"] for d in dataSourceRecordShare],
    "labels": [d["value"] for d in dataSourceRecordShare]
}
# geographic coverage/resolution
geographicCoverageData = getCountPercentages(dataSources, "geographicCoverage")
pieChartData["data-source-coverage"] = {
    "title": "Geographical coverage of data sources",
    "values": [d["percent"] for d in geographicCoverageData],
    "labels": [d["value"] for d in geographicCoverageData]
}
locData = []
for row in rowsOut:
    if "Latitude" in row and row["Latitude"] != "" and row["Latitude"] > 0:
        locData.append({"value": "lat/lon"})
    elif "Street Address" in row and row["Street Address"] != "":
        locData.append({"value": "street address"})
    elif "City" in row and row["City"] != "":
        locData.append({"value": "city"})
    elif "County" in row and row["County"] != "":
        locData.append({"value": "county"})
    elif "State" in row and row["State"] != "":
        locData.append({"value": "state"})
    else:
        locData.append({"value": "no geographic data"})
geographicResolutionData = getCountPercentages(locData, "value")
pieChartData["data-field-availability-location"] = {
    "title": "Geographical resolution of data",
    "values": [d["percent"] for d in geographicResolutionData],
    "labels": [d["value"] for d in geographicResolutionData]
}
availabilityConfig = [
    {"srcKey": "Year Constructed", "outKey": "data-field-availability-date-constructed"},
    {"srcKey": "Year Dedicated", "outKey": "data-field-availability-date-dedicated"},
    {"srcKey": "Honorees", "outKey": "data-field-availability-honoree"},
    {"srcKey": "Creator Name", "outKey": "data-field-availability-creator"},
    {"srcKey": "Sponsors", "outKey": "data-field-availability-sponsor"},
    {"srcKey": "Status", "outKey": "data-field-availability-status"},
    {"srcKey": "Text", "outKey": "data-field-availability-text"}
]
for row in availabilityConfig:
    pdata = getCountPercentages(rowsOut, row["srcKey"], presence=True)
    pieChartData[row["outKey"]] = {
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
    {"srcKey": "Status", "filename": "monumentlab_national_monuments_audit_final_status_counts.csv"},
    {"srcKey": "Creator Name", "filename": "monumentlab_national_monuments_audit_final_creator_counts.csv"},
    {"srcKey": "Categories", "filename": "monumentlab_national_monuments_audit_final_category_counts.csv"},
    {"srcKey": "Honorees", "filename": "monumentlab_national_monuments_audit_final_honoree_counts.csv"},
    {"srcKey": "Sponsors", "filename": "monumentlab_national_monuments_audit_final_sponsor_counts.csv"}
]
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
                value = "<blank>"
        rowFreqData.append({
            "label": value,
            "count": count
        })
        if len(rowFreqData) >= showTop:
            break
    # calculate "other" row
    if len(valueCounts) > showTop:
        otherCounts = list(valueCounts)
        otherCounts = otherCounts[showTop:]
        otherSum = sum([count for value, count in otherCounts])
        rowFreqData.append({
            "label": f'{len(otherCounts)} other values',
            "value": otherSum
        })
    freqData.append({
        "title": f'Top {showTop} values for "{row["srcKey"]}"',
        "rows": rowFreqData,
        "filename": row["filename"]
    })

jsonOut = {}
jsonOut["summary"] = summaryData
jsonOut["pieCharts"] = pieChartData
jsonOut["frequencies"] = freqData
writeJSON(a.APP_DIRECTORY + "data/dashboard.json", jsonOut)

################################################################
# Generate map data
################################################################

jsonOut = {
    "cols": ["lat", "lon", "name", "source", "year"],
    "groups": {
        "source": [d["name"] for d in dataSources]
    }
}
jsonRows = []
for row in rowsOut:
    lat = -999
    lon = -999
    if "Latitude" in row and row["Latitude"] != "" and row["Latitude"] > 0:
        lat = row["Latitude"]
        lon = row["Longitude"]
    jsonRow = [lat, lon]
    name = row["Name"] if "Name" in row and str(row["Name"]).strip() != "" else "<untitled>"
    source = jsonOut["groups"]["source"].index(row["Source"])
    year = parseYear(row["Year Dedicated"]) if "Year Dedicated" in row else False
    if year is False:
        year = parseYear(row["Year Constructed"]) if "Year Constructed" in row else False
    if year is False:
        year = -1
    jsonRow += [name, source, year]
    jsonRows.append(jsonRow)
jsonOut["rows"] = jsonRows
writeJSON(a.APP_DIRECTORY + "data/records.json", jsonOut)
