import re

def cleanText(string):
    string = re.sub('\s', ' ', string)

    # remove invalid xml values
    # https://docs.aws.amazon.com/cloudsearch/latest/developerguide/preparing-data.html#creating-document-batches
    # https://stackoverflow.com/questions/14258909/removing-invalid-characters-from-amazon-cloud-search-sdf
    RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                 u'|' + \
                 u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                  (chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                   chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                   chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff))
    string = re.sub(RE_XML_ILLEGAL, "", string)

    return string

def padNum(number, total):
    padding = len(str(total))
    return str(number).zfill(padding)

def stringToId(string):
    string = string.lower()
    string = re.sub('[^a-z0-9]+', '_', string)
    return string
