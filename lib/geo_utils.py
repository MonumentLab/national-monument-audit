import utm

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
