from pprint import pprint
import shapefile
import utm
import sys

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
