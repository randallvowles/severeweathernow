#!/uufs/chpc.utah.edu/common/home/u0540701/MyVenv/bin/python
# encoding: utf-8
"""Provides the `Active Alerts` API"""


def parser():
    """Active alerts XML parser"""
    import xmltodict
    import urllib
    url = 'https://alerts.weather.gov/cap/us.php?x=0'
    # Initiate the parser's working vars
    response = urllib.urlopen(url).read()
    # print response

    this = xmltodict.parse(response)

    that = {}
    tmp = dict()
    nkeys = len(this['feed']['entry'])
    # print (this['feed']['entry'][0]['title'])
    for x in xrange(nkeys):
        if this['feed']['entry'][x]['id'] not in that:
            tmp['title'] = this['feed']['entry'][x]['title']
            tmp['summary'] = this['feed']['entry'][x]['summary']
            tmp['url'] = this['feed']['entry'][x]['id']
            tmp['category'] = this['feed']['entry'][x]['cap:event']
            tmp['severity'] = this['feed']['entry'][x]['cap:severity']
            tmp['type'] = this['feed']['entry'][x]['cap:event']
            tmp['area'] = this['feed']['entry'][x]['cap:areaDesc']
            that[this['feed']['entry'][x]['id']] = tmp
        else:
            print('@@@@@@@@ Error in '+str(x)+' key, ' +
                  str(this['feed']['entry'][x]['title']))
        tmp = dict()
    return that


def alert_query():
    """Queries for nearest stations for each polygon element"""
    import json
    alerts = parser()
    emitter(alerts, 'NWS_ALERTS_current', False)
    # emitter(alerts, 'NWS_ALERTS_', True)
    # print alerts
    return alerts


def emitter(dict_, filename, timestamp):
    """Emit the file"""
    import json
    import time
    if timestamp is True:
        timestamp = time.strftime('%Y%m%d%H%M', time.gmtime())
    else:
        timestamp = ''
    # !! This is where problems can occur.
    # This should be surfaced as an option.
    filename1 = str(filename) + str(timestamp) + '.json'
    output_dir = 'C:\\severeweathernow\\storage\\'
    # output_dir = '../storage/'
    file_out = output_dir + filename1
    with open(file_out, 'w') as file_out:
        # json.dump(dict_, file_out, sort_keys=True, separators=(',', ':'),
                #   encoding="utf-8")/
        json.dump(dict_, file_out, sort_keys=True, indent=4)


alert_query()
