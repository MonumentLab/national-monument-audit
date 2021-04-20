# -*- coding: utf-8 -*-

import geopy
from pprint import pprint
import shapefile
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

def geocodeItems(rows, geoCacheFile, geolocator, gkey="Geo Type", waitSeconds=5):
    validRows = []
    for i, row in enumerate(rows):
        if row[gkey] != "No coordinates provided":
            continue

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

        elif itemNotEmpty(row, "Street Address") and itemNotEmpty(row, "City") and itemNotEmpty(row, "State"):
            lookupDict = {
                "city": row["City"],
                "state": row["State"],
                "country": "United States"
            }
            lookupString = f'{row["City"]}, {row["State"]}'
            rows[i][gkey] = "Approximate coordinates geocoded based on city"

        else:
            rows[i][gkey] = "No geographic data provided"
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
            rows[index][gkey] = "No valid geographic data provided"

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
