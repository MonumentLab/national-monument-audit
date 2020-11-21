
import collections
import itertools
from operator import itemgetter
from pprint import pprint
import sys

from lib.math_utils import *

def addIndices(arr, keyName="index", startIndex=0):
    for i, item in enumerate(arr):
        arr[i][keyName] = startIndex + i
    return arr

def createLookup(arr, key):
    return dict([(str(item[key]), item) for item in arr])

def filterByQuery(arr, ors):
    if isinstance(ors, tuple):
        ors = [[ors]]
    # pprint(ors)

    if len(ors) < 1:
        return arr

    results = []
    for item in arr:
        for ands in ors:
            andValid = True
            for key, comparator, value in ands:
                itemValue = item[key]
                if comparator not in ["CONTAINS", "EXCLUDES"]:
                    value = parseNumber(value)
                    itemValue = parseNumber(itemValue)
                if comparator == "<=" and itemValue > value:
                    andValid = False
                    break
                elif comparator == ">=" and itemValue < value:
                    andValid = False
                    break
                elif comparator == "<" and itemValue >= value:
                    andValid = False
                    break
                elif comparator == ">" and itemValue <= value:
                    andValid = False
                    break
                elif comparator == "CONTAINS" and value not in itemValue:
                    andValid = False
                    break
                elif comparator == "EXCLUDES" and value in itemValue:
                    andValid = False
                    break
                elif comparator == "!=" and itemValue == value:
                    andValid = False
                    break
                elif comparator == "=" and itemValue != value:
                    andValid = False
                    break
            if andValid:
                results.append(item)
                break
    return results

def filterByQueryString(arr, str):
    ors = parseQueryString(str)
    return filterByQuery(arr, ors)

def flattenList(arr):
    return [item for sublist in arr for item in sublist]

def getCountPercentages(arr, key, presence=False, otherTreshhold=None):
    arrLen = len(arr)
    counts = getCounts(arr, key, presence)
    data = []
    for value, count in counts:
        if value == "":
            value = "<empty>"
        percent = round(1.0 * count / arrLen * 100.0, 2)
        data.append({"value": value, "percent": percent})
    if otherTreshhold is not None and len(data) > otherTreshhold:
        otherData = data[otherTreshhold:]
        data = data[:otherTreshhold]
        otherSum = sum([d["percent"] for d in otherData])
        data.append({"value": "other", "percent": otherSum})
    return data

def getCounts(arr, key, presence=False):
    values = [str(v[key]).strip() if key in v else "" for v in arr]
    if presence:
        values = ["no" if len(v) < 1 else "yes" for v in values]
    counter = collections.Counter(values)
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

def parseQueryString(str):
    if len(str) <= 0:
        return []
    comparators = ["<=", ">=", " EXCLUDES ", " CONTAINS ", "!=", ">", "<", "="]
    orStrings = str.split(" OR ")
    ors = []
    for orString in orStrings:
        andStrings = orString.split(" AND ")
        ands = []
        for andString in andStrings:
            for comparator in comparators:
                if comparator in andString:
                    parts = [part.strip() for part in andString.split(comparator)]
                    ands.append(tuple([parts[0], comparator.strip(), parts[1]]))
                    break
        ors.append(ands)
    return ors

def parseSortString(str):
    if len(str) <= 0:
        return []
    conditionStrings = str.split(" AND ")
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
