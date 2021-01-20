import re
import string

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

def itemToId(row):
    if "Source" not in row:
        return None
    if "Vendor Entry ID" not in row or str(row["Vendor Entry ID"]).strip() == "":
        return None
    return stringToId(row["Source"]) + "_" + str(row["Vendor Entry ID"]).strip()

def padNum(number, total):
    padding = len(str(total))
    return str(number).zfill(padding)

def stringToId(value):
    value = value.lower()
    value = re.sub('[^a-z0-9]+', '_', value)
    return value

def validateNameString(value):
    return validateTitleString(value)

def validateStateString(value):
    stateMap = {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY",
        "American Samoa": "AS",
        "District of Columbia": "DC",
        "Federated States of Micronesia": "FM",
        "Guam": "GU",
        "Marshall Islands": "MH",
        "Northern Mariana Islands": "MP",
        "Palau": "PW",
        "Puerto Rico": "PR",
        "Virgin Islands": "VI"
    }
    if value in stateMap:
        return stateMap[value]
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
