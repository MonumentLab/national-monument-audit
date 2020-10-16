#!/usr/bin/env python3
#
# Search metadata in the EDAN API
# v0.1
# Source: https://github.com/Smithsonian/EDAN-python/blob/master/edan.py
#

import urllib.parse
import urllib.request
import datetime
import email.utils
import uuid
import hashlib
import json
from base64 import b64encode

#for testing
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def queryEDAN(edan_q, url, AppID, AppKey):
    """
    Execute the query
    """
    #Date of request
    dt = datetime.datetime.now()
    RequestDate = email.utils.format_datetime(dt)
    #Generated uniquely for this request
    Nonce = str(uuid.uuid4()).replace('-', '')
    #This will be the value of X-AuthContent, each element is joined by a single newline
    StringToSign = "{}\n{}\n{}\n{}".format(Nonce, edan_q, RequestDate, AppKey)
    #First hash using SHA1
    HashedString = hashlib.sha1(StringToSign.encode('utf-8')).hexdigest()
    #Base64 encode
    EncodedString = b64encode(HashedString.encode('utf-8')).decode('utf-8')
    #Set headers
    headers = {'X-AppId': AppID, 'X-Nonce': Nonce, 'X-RequestDate': RequestDate, 'X-AuthContent': EncodedString}
    #Make request
    req = urllib.request.Request(url = url, headers = headers, method = "GET")
    try:
        response = urlopen(req)
    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error: {} ({})'.format(e.reason, e.code))
        return False
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
        return False
    else:
        data = response.read().decode('utf-8')
        return json.loads(data)



def searchEDAN(edan_query, AppID, AppKey, rows = 10, start = 0):
    """
    Search EDAN
    """
    #Request
    edan_query = urllib.parse.quote_plus(edan_query)
    edan_q = "q={}&rows={}&start={}&facet=true".format(edan_query, rows, start)
    #Put whole thing together
    url = 'https://edan.si.edu/metadata/v2.0/collections/search.htm?{}'.format(edan_q)
    #Execute query
    result = queryEDAN(edan_q, url, AppID, AppKey)
    return result



def getContentEDAN(edan_id, AppID, AppKey):
    """
    Get details from an item using an EDAN ID
    """
    #Request
    edan_q = "url={}".format(edan_id)
    #Put whole thing together
    url = 'https://edan.si.edu/content/v2.0/content/getContent.htm?{}'.format(edan_q)
    #Execute query
    result = queryEDAN(edan_q, url, AppID, AppKey)
    return result
