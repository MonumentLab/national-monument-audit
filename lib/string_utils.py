from datetime import datetime, timedelta
import hashlib
import re
import string
import urllib

from lib.geo_utils import *
from lib.math_utils import *

def cleanText(value):
    value = re.sub('\s', ' ', value)

    # remove invalid xml values
    # https://docs.aws.amazon.com/cloudsearch/latest/developerguide/preparing-data.html#creating-document-batches
    # https://stackoverflow.com/questions/14258909/removing-invalid-characters-from-amazon-cloud-search-sdf
    RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                 u'|' + \
                 u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                  (chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                   chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                   chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff))
    value = re.sub(RE_XML_ILLEGAL, "", value)

    return value

def containsPhrase(rawValue, phrase):
    value = str(rawValue).lower().strip()
    phrase = normalizeString(phrase)

    return (phrase in value)

def containsWord(rawValue, word, isFirstWord=False, isLastWord=False, caseSensitive=False):
    response = False

    # normalize everything to a list
    values = rawValue
    if not isinstance(values, list):
        values = [values]

    if not caseSensitive:
        word = word.lower()

    for value in values:
        value = normalizeString(value, caseSensitive)
        if len(value) < 1:
            continue
        words = value.split()
        words = [word for word in words if len(word) > 0]
        if len(words) < 1:
            continue
        if isLastWord:
            words = [words[-1]]
        elif isFirstWord:
            words = [words[0]]
        if word in words:
            response = True
            break

    return response

def itemNotEmpty(row, key):
    return (key in row and len(str(row[key]).strip()) > 0)

def itemToId(row):
    if "Vendor ID" not in row:
        return None
    if "Vendor Entry ID" not in row or str(row["Vendor Entry ID"]).strip() == "":
        return None

    return stringToId(row["Vendor ID"]) + "_" + stringToId(str(row["Vendor Entry ID"]).strip(), lowercase=False)

def md5string(value):
    return hashlib.md5(str(value).encode('utf-8')).hexdigest()

def normalizeName(value):
    value = str(value).strip()
    value = value.replace("'s", "")
    value = value.replace("’s", "")
    value = value.replace('-', ' ')
    value = re.sub('\s', ' ', value) # replace all whitespace with a single space

    # e.g. Smith, John -> John Smith
    if "," in value:
        parts = [p.strip() for p in value.split(",")]
        if len(parts) == 2:
            parts.reverse()
            value = ' '.join(parts)
    value = value.lower()

    replaceWords = [("americans", "american")]
    for fromWord, toWord in replaceWords:
        value = value.replace(fromWord, toWord)

    # remove "the" from the beginning
    trimBeginningWords = ["the"]
    for w in trimBeginningWords:
        testStr = w + " "
        if value.startswith(testStr):
            value = value[len(testStr):]

    trimEndingWords = ["jr.", "jr", "'s"]
    for w in trimEndingWords:
        testStr = " "+w
        if value.endswith(testStr):
            value = value[:-len(testStr)]

    # strip words
    stripWords = ["historic", "building", "landmark", "memorial", "monument", "trail", "site", "marker", "library", "center", "space", "lake"]
    for word in stripWords:
        value = value.replace(word, "")

    value = re.sub('[^a-z0-9 ]+', '', value)
    value = re.sub('\s', ' ', value)
    value = value.strip()

    # remove middle initial
    words = value.split(" ")
    if len(words) == 3 and len(words[1]) == 1:
        words = [words[0]] + [words[2]]
        value = " ".join(words)

    return value

def normalizeString(value, caseSensitive=False):
    value = str(value).strip()
    if not caseSensitive:
        value = value.lower()
    value = value.replace("'s", "")
    value = value.replace("’s", "")
    value = value.replace('-', ' ')
    value = re.sub('\s', ' ', value) # replace all whitespace with a single space
    value = re.sub('[^a-z0-9\. ]+', ' ', value)
    value = re.sub('\s', ' ', value)
    value = value.strip()
    return value

def normalizeWhitespace(value):
    value = str(value)
    value = re.sub('\s', ' ', value)
    value = value.strip()
    return value

def padNum(number, total):
    padding = len(str(total))
    return str(number).zfill(padding)

def pluralizeString(value):
    value = str(value).strip()
    if len(value) < 1:
        return value

    lvalue = value.lower()
    if lvalue.endswith('s'):
        return value
    elif lvalue.endswith('y'):
        return value[:-1] + 'ies'
    else:
        return value + 's'

def stringToId(value, lowercase=True):
    value = str(value)
    if lowercase:
        value = value.lower()
    value = re.sub('[^A-Za-z0-9\-]+', '_', value)
    return value

def stringToTitle(value):
    value = value.replace("'s", "")
    value = value.replace("’s", "")
    value = re.sub('\s', ' ', value)

    # e.g. Smith, John -> John Smith
    if "," in value:
        parts = [p.strip() for p in value.split(",")]
        if len(parts) == 2:
            parts.reverse()
            value = ' '.join(parts)

    words = [word.strip() for word in value.split()]
    formattedWords = []
    # strip words
    stripWords = ("Historic", "Building", "Landmark", "Memorial", "Monument", "Trail", "Site", "Marker", "Library", "Center", "Space", "Lake")
    stopWords = ("a", "of", "the")
    for i, word in enumerate(words):
        if i > 0 and word in stopWords:
            formattedWords.append(word)
        else:
            fword = word[0].upper() + word[1:]
            if fword not in stripWords:
                formattedWords.append(fword)

    formatted = " ".join(formattedWords)
    return formatted

def stringToYear(value, minYear=1000, maxYear=2050):
    matches = re.findall('\d{4}', str(value))
    year = None
    if matches:
        for match in matches:
            matchInt = int(match)
            if (minYear is None or matchInt >= minYear) and (maxYear is None or matchInt <= maxYear):
                year = matchInt
                break
    return year

def stripTags(text):
    text = str(text)
    text = re.sub('<[^<]+?>', '', text)
    return text

def timestampToYear(value, isMilliseconds=False):
    yearValue = None
    intValue = parseInt(value, defaultValue=False)
    if intValue is not False:
        if isMilliseconds:
            intValue = intValue / 1000
        try:
            if intValue < 0:
                dt = datetime(1970, 1, 1) + timedelta(seconds=intValue)
                yearValue = dt.year
            else:
                yearValue = int(datetime.utcfromtimestamp(intValue).strftime('%Y'))
        except OSError:
            print(f'Invalid timestamp: {intValue}')
            yearValue = None
    return yearValue

def urlEncodeString(value):
    return urllib.parse.quote_plus(value)

def validateNameString(value):
    return validateTitleString(value)

def validateStateString(value):
    stateMap = getStates()
    # convert to lower case
    nStateMap = {}
    for k, v in stateMap.items():
        nStateMap[k.lower()] = v
    nvalue = value.lower()
    if nvalue in nStateMap:
        return nStateMap[nvalue]
    elif value in set(stateMap.values()):
        return value
    else:
        print("Could not validate state: %s" % value)
        return value

def validateTitleString(value):
    formatted = str(value)
    formatted = formatted.replace('_', ' ')
    formatted = " ".join(word[0].upper() + word[1:] for word in formatted.split())
    return formatted
