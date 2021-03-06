
import collections
import itertools
from operator import itemgetter
from pprint import pprint
import random
import sys

from lib.math_utils import *

def addIndices(arr, keyName="index", startIndex=0):
    for i, item in enumerate(arr):
        arr[i][keyName] = startIndex + i
    return arr

def addValueToStringOrList(strOrArr, value):
    if value == "":
        return strOrArr
    values = value
    if not isinstance(value, list):
        values = [str(value).strip()]
    if not isinstance(strOrArr, list):
        strOrArr = str(strOrArr).strip()
        if strOrArr == "":
            strOrArr = []
        else:
            strOrArr = [strOrArr]
    strOrArr = [str(v).strip() for v in strOrArr]
    for value in values:
        if value not in strOrArr:
            strOrArr.append(value)
    return strOrArr

def createLookup(arr, key):
    return dict([(str(item[key]), item) for item in arr])

def findByValue(arr, key, value):
    found = None
    for item in arr:
        if key in item and item[key] == value:
            found = item
            break
    return found

def filterByQuery(arr, ors, delimeter="|", caseSensitive=False):
    if isinstance(ors, tuple):
        ors = [[ors]]
    # pprint(ors)

    if len(ors) < 1:
        return arr

    # print("===============")
    # pprint(ors)
    # print("===============")

    results = []
    for item in arr:
        for ands in ors:
            andValid = True
            for key, comparator, value in ands:
                value = str(value)
                itemValue = str(item[key])
                if not caseSensitive:
                    value = value.lower()
                    itemValue = itemValue.lower()
                if comparator not in ["CONTAINS", "EXCLUDES", "CONTAINS LIST", "EXCLUDES LIST", "IN LIST", "NOT IN LIST"]:
                    value = parseNumber(value)
                    itemValue = parseNumber(itemValue)
                if comparator in ["IN LIST", "NOT IN LIST", "CONTAINS LIST", "EXCLUDES LIST"]:
                    value = [v.strip() for v in value.split(delimeter)]
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
                elif comparator == "IN LIST" and itemValue not in value:
                    andValid = False
                    break
                elif comparator == "NOT IN LIST" and itemValue in value:
                    andValid = False
                    break
                elif comparator == "CONTAINS LIST":
                    andValid = False
                    for v in value:
                        if v in itemValue:
                            andValid = True
                            break
                    break
                elif comparator == "EXCLUDES LIST":
                    for v in value:
                        if v in itemValue:
                            andValid = False
                            break
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
    queries = [parseQueryString(str) for str in str.split(" | ")]
    filteredArr = arr[:]
    for query in queries:
        filteredArr = filterByQuery(filteredArr, query)
    return filteredArr

def flattenList(arr):
    return [item for sublist in arr for item in sublist]

def getCountPercentages(arr, key, presence=False, otherTreshhold=None, excludeEmpty=False):
    if excludeEmpty:
        arr = [item for item in arr if key in item and str(item[key]).strip() != ""]
    arrLen = len(arr)
    counts = getCounts(arr, key, presence)
    data = []
    for value, count in counts:
        if value == "":
            if excludeEmpty:
                continue
            value = "<empty>"
        percent = round(1.0 * count / arrLen * 100.0, 2)
        data.append({"value": value, "percent": percent, "count": count})
    # always make "yes" first
    if presence:
        data = sorted(data, key=lambda d: d["value"], reverse=True)
    if otherTreshhold is not None and len(data) > otherTreshhold:
        otherData = data[otherTreshhold:]
        data = data[:otherTreshhold]
        otherCount = sum([d["count"] for d in otherData])
        otherPercent = sum([d["percent"] for d in otherData])
        otherPercent = round(otherPercent, 2)
        data.append({"value": "other", "percent": otherPercent, "count": otherCount})
    return data

def getCounts(arr, key=False, presence=False):
    values = arr[:]
    if key is not False:
        values = []
        for item in arr:
            value = ""
            if key in item:
                value = item[key]
            if isinstance(value, list) and not presence:
                values += value
            else:
                values.append(value)
        values = [str(v).strip() for v in values]
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
    comparators = ["<=", ">=", " NOT IN LIST ", " IN LIST ", " EXCLUDES LIST ", " CONTAINS LIST ", " EXCLUDES ", " CONTAINS ", "!=", ">", "<", "="]
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

def removeValueFromStringOrList(strOrArr, value):
    if value == "":
        return strOrArr
    values = value
    if not isinstance(value, list):
        values = [str(value).strip()]
    if not isinstance(strOrArr, list):
        strOrArr = str(strOrArr).strip()
        if strOrArr == "":
            strOrArr = []
        else:
            strOrArr = [strOrArr]
    strOrArr = [str(v).strip() for v in strOrArr]
    strOrArr = [v for v in strOrArr if v not in values]
    if len(strOrArr) < 1:
        strOrArr = ""
    return strOrArr

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

        if key == "random":
            random.shuffle(arr)
        else:
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
