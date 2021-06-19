# -*- coding: utf-8 -*-

import geopy
from pprint import pprint
import shapefile
import shapely.geometry
import utm
import sys
import time

from lib.collection_utils import *
from lib.io_utils import *
from lib.math_utils import *
from lib.string_utils import *

def applyGeoTypes(rows, clusterThreshold=10, multiplier=10000, gkey="Geo Type"):
    validRows = []
    for i, row in enumerate(rows):
        lat = roundInt(row["Latitude"] * multiplier) if "Latitude" in row and isNumber(row["Latitude"]) else ""
        lon = roundInt(row["Longitude"] * multiplier) if "Longitude" in row and isNumber(row["Longitude"]) else ""
        if lat == "" or lon == "":
            rows[i][gkey] = "No coordinates provided"
            continue
        row["_latlonGroup"] = (lat, lon)
        row["_index"] = i
        rows[i][gkey] = "Exact coordinates provided"
        validRows.append(row)

    # group items by lat/lon
    itemsByLatLon = groupList(validRows, "_latlonGroup")
    for group in itemsByLatLon:
        if group["count"] < clusterThreshold:
            continue
        # if there's more than <threshold> items at a single lat/lon, assume this is
        for row in group["items"]:
            i = row["_index"]
            rows[i][gkey] = "Approximate coordinates provided"

    return rows

def codeToState(abbrev, defaultValue="Unknown"):
    stateMap = getStates()
    value = defaultValue
    for name, code in stateMap.items():
        if abbrev == code:
            value = name
            break
    return value

def fipsToState(fipsString, defaultValue="Unknown"):
    if isNumber(fipsString):
        fipsString = str(fipsString).zfill(2)
    fipsMap = {
        "01": "AL",
        "02": "AK",
        "04": "AZ",
        "05": "AR",
        "06": "CA",
        "08": "CO",
        "09": "CT",
        "10": "DE",
        "11": "DC",
        "12": "FL",
        "13": "GA",
        "15": "HI",
        "16": "ID",
        "17": "IL",
        "18": "IN",
        "19": "IA",
        "20": "KS",
        "21": "KY",
        "22": "LA",
        "23": "ME",
        "24": "MD",
        "25": "MA",
        "26": "MI",
        "27": "MN",
        "28": "MS",
        "29": "MO",
        "30": "MT",
        "31": "NE",
        "32": "NV",
        "33": "NH",
        "34": "NJ",
        "35": "NM",
        "36": "NY",
        "37": "NC",
        "38": "ND",
        "39": "OH",
        "40": "OK",
        "41": "OR",
        "42": "PA",
        "44": "RI",
        "45": "SC",
        "46": "SD",
        "47": "TN",
        "48": "TX",
        "49": "UT",
        "50": "VT",
        "51": "VA",
        "53": "WA",
        "54": "WV",
        "55": "WI",
        "56": "WY",
        "60": "AS",
        "64": "FM",
        "66": "GU",
        "67": "JA",
        "68": "MH",
        "69": "MP",
        "70": "PW",
        "72": "PR",
        "74": "UM",
        "76": "NI",
        "78": "VI",
        "81": "BI",
        "86": "JI",
        "89": "KR"
    }
    stateStr = fipsMap[fipsString] if fipsString in fipsMap else defaultValue
    return stateStr

def geocodeItems(rows, geoCacheFile, geolocator, gkey="Geo Type", waitSeconds=5):
    validRows = []
    for i, row in enumerate(rows):
        if row[gkey] != "No coordinates provided" and row[gkey] != "Approximate coordinates provided":
            continue
        originalGeoType =  row[gkey]

        lookupString = None
        lookupDict = None

        if itemNotEmpty(row, "Street Address") and itemNotEmpty(row, "City") and itemNotEmpty(row, "State"):
            lookupDict = {
                "street": row["Street Address"],
                "city": row["City"],
                "state": row["State"],
                "country": "United States"
            }
            lookupString = f'{row["Street Address"]}, {row["City"]}, {row["State"]}'
            rows[i][gkey] = "Geocoded based on street address provided"

        else:
            rows[i][gkey] = originalGeoType
            continue

        row["_index"] = i
        row["_lookupString"] = lookupString
        row["_lookupDict"] = lookupDict
        validRows.append(row)

    _, existingGeodata = readCsv(geoCacheFile)
    existingGeodata = addIndices(existingGeodata, "_index")
    geoLookup = {}
    if len(existingGeodata) > 0:
        geoLookup = createLookup(existingGeodata, "Lookup String")

    geocodeCount = len(validRows)
    print(f'  {formatNumber(geocodeCount)} records to geocode.')
    for i, row in enumerate(validRows):

        lookupString = row["_lookupString"]
        lookupDict = row["_lookupDict"]
        matchedRow = None
        if lookupString not in geoLookup:
            location = None

            try:
                location = geolocator.geocode(lookupDict)
            except geopy.exc.GeocoderTimedOut:
                location = None

            newRow = { "Lookup String": lookupString, "Address": "", "Latitude": "", "Longitude": "" }
            if location is not None:
                newRow = {
                    "Lookup String": lookupString,
                    "Address": location.address,
                    "Latitude": location.latitude,
                    "Longitude": location.longitude
                }
            geoLookup[lookupString] = newRow
            newRow["_index"] = len(existingGeodata)
            existingGeodata.append(newRow)
            # cache the result
            writeCsv(geoCacheFile, existingGeodata, headings=["Lookup String", "Address", "Latitude", "Longitude"], verbose=False)
            matchedRow = newRow
            time.sleep(waitSeconds)

        else:
            matchedRow = geoLookup[lookupString]

        # validate location, e.g. Broad Street, Stonington, New London County, Connecticut, 06378, United States
        locationParts = [p.strip() for p in matchedRow["Address"].split(",")]
        if len(locationParts) >= 3:
            locCountry = locationParts[-1]
            locZip = parseInt(locationParts[-2].replace("-", "").replace(":", "").replace("`", "").replace('*', '').replace('+', '').rstrip('S'), defaultValue=None)
            locState = locationParts[-3]
            if locZip is None:
                locState = locationParts[-2] # no zip provided; assume this is state
            # Check if not in U.S. or state does not match lookup state
            if locCountry != "United States" or validateStateString(locState) != lookupDict["state"]:
                if locCountry != "United States":
                    print(f'  Invalid country: {matchedRow["Address"]} (Lookup: {lookupString})')
                else:
                    print(f'  State mismatch: {matchedRow["Address"]} (Lookup: {lookupString})')
                matchedRow = { "Lookup String": lookupString, "Address": "", "Latitude": "", "Longitude": "", "_index": matchedRow["_index"] }
                existingGeodata[matchedRow["_index"]] = matchedRow
                writeCsv(geoCacheFile, existingGeodata, headings=["Lookup String", "Address", "Latitude", "Longitude"], verbose=False)

        index = row["_index"]
        if matchedRow["Latitude"] != "" and matchedRow["Longitude"] != "":
            rows[index]["Latitude"] = matchedRow["Latitude"]
            rows[index]["Longitude"] = matchedRow["Longitude"]
        else:
            rows[index][gkey] = originalGeoType
            # rows[index]["Latitude"] = ""
            # rows[index]["Longitude"] = ""

        printProgress(i+1, geocodeCount)

    return rows

def readShapefile(fn):
    data = []
    sf = shapefile.Reader(fn)
    shapes = sf.shapes()
    print(f'  Found {len(shapes)} shapes in {fn}')
    # print(sf.shapeType)
    metadataFields = [f[0] for f in sf.fields]
    metadataRecords = sf.records()
    # print(f' Found {len(metadataRecords)} records in {fn}')
    for i, shape in enumerate(shapes):
        row = {}
        record = metadataRecords[i].as_dict()
        for j, fieldname in enumerate(metadataFields):
            row[fieldname] = record[fieldname] if fieldname in record else ""
        lon, lat = tuple(shape.points[0]) # assumes this is a point
        row["Latitude"] = lat
        row["Longitude"] = lon
        data.append(row)
    return data

def searchPointInGeoJSON(lat, lon, geojsonData):
    found = None
    point = shapely.geometry.Point(lon, lat)
    for feature in geojsonData["features"]:
        polygon = shapely.geometry.shape(feature['geometry'])
        if polygon.contains(point):
            found = feature
            break
    return found

def utmToLatLon(easting, northing, zoneNumber, zoneLetter=None, northern=None):
    lat = None
    lon = None
    try:
        lat, lon = utm.to_latlon(easting, northing, zoneNumber, zoneLetter, northern)
    except utm.error.OutOfRangeError:
        lat = lon = ""
    except TypeError:
        lat = lon = ""
    return (lat, lon)
