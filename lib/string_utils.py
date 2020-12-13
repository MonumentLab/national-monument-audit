import re

def cleanText(string):
    string = re.sub('\s', ' ', string)
    return string

def padNum(number, total):
    padding = len(str(total))
    return str(number).zfill(padding)

def stringToId(string):
    string = string.lower()
    string = re.sub('[^a-z0-9]+', '_', string)
    return string
