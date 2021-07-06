# -*- coding: utf-8 -*-

import math
import time
import sys

def ceilInt(n):
    return int(math.ceil(n))

def ceilToNearest(n, nearest):
    return 1.0 * math.ceil(1.0*n/nearest) * nearest

def floorInt(n):
    return int(math.floor(n))

def formatDecimal(n, precision=1):
    return "{0}".format(str(round(n, precision) if n % 1 else int(n)))

def formatNumber(n):
    return "{:,}".format(n)

def isInt(string):
    answer = False
    try:
        if "." not in str(string) and "e" not in str(string):
            num = int(string)
            answer = True
    except ValueError:
        answer = False
    return answer

def isNumber(n):
    return isinstance(n, (int, float))

def lerp(ab, amount):
    a, b = ab
    return (b-a) * amount + a

def lim(value, ab=(0, 1)):
    a, b = ab
    return max(a, min(b, value))

def norm(value, ab, limit=False):
    a, b = ab
    n = 0.0
    if (b - a) != 0:
        n = 1.0 * (value - a) / (b - a)
    if limit:
        n = lim(n)
    return n

def parseFloat(string):
    return parseNumber(string, alwaysFloat=True)

def parseInt(string, defaultValue=""):
    try:
        num = int(string)
        return num
    except ValueError:
        return defaultValue
    except TypeError:
        return defaultValue

def parseNumber(string, alwaysFloat=False):
    if isinstance(string, list):
         return string
    try:
        num = float(string)
        if "." not in str(string) and "e" not in str(string) and not alwaysFloat:
            num = int(string)
        return num
    except ValueError:
        return string
    except TypeError:
        return ""

def parseYear(string, minYear=1000, maxYear=2050):
    try:
        num = int(string)
        if num >= minYear and num <= maxYear:
            return num
        return False
    except ValueError:
        return False

def parseNumbers(arr, keyExceptions=['id', 'identifier', 'uid', 'Vendor Entry ID']):
    for i, item in enumerate(arr):
        if isinstance(item, (list,)):
            for j, v in enumerate(item):
                arr[i][j] = parseNumber(v)
        else:
            for key in item:
                if key not in keyExceptions:
                    arr[i][key] = parseNumber(item[key])
    return arr

def printProgress(step, total, prepend=""):
    sys.stdout.write('\r')
    sys.stdout.write("%s%s%%" % (prepend, round(1.0*step/total*100,2)))
    sys.stdout.flush()

def roundInt(n):
    return int(round(n))

def roundToNearest(n, nearest):
    return 1.0 * round(1.0*n/nearest) * nearest
