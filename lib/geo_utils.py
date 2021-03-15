# -*- coding: utf-8 -*-

from pprint import pprint
import shapefile
import utm
import sys

from lib.collection_utils import *
from lib.math_utils import *

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
