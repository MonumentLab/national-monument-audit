import re

def cleanText(string):
    string = re.sub('\s', ' ', string)
    return string

def stringToId(string):
    string = string.lower()
    string = re.sub('[^a-z0-9]+', '_', string)
    return string
