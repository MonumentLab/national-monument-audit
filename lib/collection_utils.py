
import collections
import itertools
from operator import itemgetter
from pprint import pprint
from lib.math_utils import *

def addIndices(arr, keyName="index", startIndex=0):
    for i, item in enumerate(arr):
        arr[i][keyName] = startIndex + i
    return arr

def createLookup(arr, key):
    return dict([(str(item[key]), item) for item in arr])

def filterByQueryString(arr, queryString):
    return filterWhere(arr, parseFilterString(queryString))

def filterWhere(arr, filters):
    if isinstance(filters, tuple):
        filters = [filters]

    if len(arr) <= 0:
        return arr

    # Filter array
    for f in filters:
        mode = '='
        if len(f) == 2:
            key, value = f
        else:
            key, value, mode = f
        value = parseNumber(value)
        if mode == "<=":
            arr = [a for a in arr if key not in a or a[key] <= value]
        elif mode == ">=":
            arr = [a for a in arr if key not in a or a[key] >= value]
        elif mode == "<":
            arr = [a for a in arr if key not in a or a[key] < value]
        elif mode == ">":
            arr = [a for a in arr if key not in a or a[key] > value]
        elif mode == "~=":
            arr = [a for a in arr if key not in a or value in a[key]]
        elif mode == "!=":
            arr = [a for a in arr if key not in a or a[key] != value]
        elif mode == "!~=":
            arr = [a for a in arr if key not in a or value not in a[key]]
        elif mode == "?=":
            arr = [a for a in arr if key not in a or a[key] != ""]
        else:
            arr = [a for a in arr if key not in a or a[key] == value]

    return arr

def findWhere(arr, filters):
    results = filterWhere(arr, filters)
    if len(results) < 1:
        return None
    else:
        return results[0]

def flattenList(arr):
    return [item for sublist in arr for item in sublist]

def getCounts(arr, key):
    counter = collections.Counter([v[key] for v in arr])
    return counter.most_common()

def groupList(arr, groupBy, sort=False, desc=True):
    groups = []
    arr = sorted(arr, key=itemgetter(groupBy))
    for key, items in itertools.groupby(arr, key=itemgetter(groupBy)):
        group = {}
        litems = list(items)
        count = len(litems)
        group[groupBy] = key
        group["items"] = litems
        group["count"] = count
        groups.append(group)
    if sort:
        reversed = desc
        groups = sorted(groups, key=lambda k: k["count"], reverse=reversed)
    return groups

def parseFilterString(str):
    if len(str) <= 0:
        return []
    conditionStrings = str.split("&")
    conditions = []
    modes = ["<=", ">=", "~=", "!=", "!~=", "?=", ">", "<", "="]
    for cs in conditionStrings:
        for mode in modes:
            if mode in cs:
                parts = cs.split(mode)
                parts.append(mode)
                conditions.append(tuple(parts))
                break
    return conditions

def parseQueryString(str, doParseNumbers=False):
    if len(str) <= 0:
        return {}
    conditionStrings = str.split("&")
    conditions = {}
    for cs in conditionStrings:
        key, value = tuple(cs.split("="))
        if doParseNumbers:
            value = parseNumber(value)
        conditions[key] = value
    return conditions

def parseSortString(str):
    if len(str) <= 0:
        return []
    conditionStrings = str.split("&")
    conditions = []
    for cs in conditionStrings:
        if "=" in cs:
            parts = cs.split("=")
            conditions.append(tuple(parts))
        else:
            conditions.append((cs, "asc"))
    return conditions

def prependAll(arr, prepends):
    if isinstance(prepends, tuple):
        prepends = [prepends]

    for i, item in enumerate(arr):
        for p in prepends:
            newKey = None
            if len(p) == 3:
                key, value, newKey = p
            else:
                key, value = p
                newKey = key
            arr[i][newKey] = value + item[key]

    return arr

def sortBy(arr, sorters, targetLen=None):
    if isinstance(sorters, tuple):
        sorters = [sorters]

    if len(arr) <= 0:
        return arr

    # Sort array
    for s in sorters:
        trim = 1.0
        if len(s) > 2:
            key, direction, trim = s
            trim = float(trim)
        else:
            key, direction = s
        reversed = (direction == "desc")

        arr = sorted(arr, key=lambda k: k[key], reverse=reversed)

        if 0.0 < trim < 1.0:
            count = int(round(len(arr) * trim))
            if targetLen is not None:
                count = max(count, targetLen)
            arr = arr[:count]

    if targetLen is not None and len(arr) > targetLen:
        arr = arr[:targetLen]

    return arr

def sortByQueryString(arr, sortString, targetLen=None):
    sorters = parseSortString(sortString)

    if len(sorters) <= 0:
        return arr

    return sortBy(arr, sorters, targetLen)

def unique(arr):
    return list(set(arr))
