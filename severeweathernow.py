#!/uufs/chpc.utah.edu/common/home/u0540701/MyVenv/bin/python

# Created by Randall Vowles, API token and twitter account belong to me

import configparser
import requests
import json
import tweepy
import datetime
import random
#import matplotlib.pyplot as plt
import time
import xmltodict
import urllib


config = configparser.RawConfigParser()
config.read(r'swnconfig.txt')
consumer_key = config.get('swn', 'consumer_key')
consumer_secret = config.get('swn', 'consumer_secret')
access_token = config.get('swn', 'access_token')
access_token_secret = config.get('swn', 'access_token_secret')
api_token = config.get('swn', 'api_token')
gps_token = config.get('swn', 'gps_token')

baseurl = 'http://api.mesowest.net/v2/stations/timeseries'
ozone_parameters = {"status": "active", "token": api_token, "qc": "on", 'qc_remove_data': 'on',
                    "vars": "ozone_concentration", "units": "english",
                    "qc_checks": "synopticlabs", "recent": "30", "network": "9,40,57,113,142,150,178,181,206,207,136"}
pm25_parameters = {"status": "active", "token": api_token, "qc": "on", 'qc_remove_data': 'on',
                   "vars": "PM_25_concentration", "units": "english",
                   "qc_checks": "synopticlabs", "recent": "30", "network": "9,40,57,113,142,150,178,181,206,207,136"}
weather_parameters = {"status": "active", "token": api_token, "qc": "on", 'qc_remove_data': 'on',
                      "vars": "weather_condition,weather_cond_code",
                      "qc_checks": "synopticlabs", "recent": "30", "network": "1", "units": "english"}
windChill_parameters = {"status": "active", "token": api_token, "qc": "on", 'qc_remove_data': 'on',
                        "vars": "heat_index,wind_chill", "units": "english",
                        "qc_checks": "synopticlabs", "recent": "30", "network": "1"}
#"network": "9,40,57,113,142,150,178,181,206,207,136"
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

all_states = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de',
              'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks',
              'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms',
              'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny',
              'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
              'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv',
              'wi', 'wy']
ready_tweets = []
tweeting_stids = {"ozone": [], "pm25": [], "thunder": [], "visibility": [], "rain": [], "snow": []}
start_time = datetime.date.today().strftime('%Y%m%d%H%M')
end_time = (datetime.datetime.utcnow()).strftime('%Y%m%d%H%M')


def apiCall(PARAMETERS):
    results = requests.get(baseurl, params=PARAMETERS)
    results1 = results.json()
    print results.url
    return results1


def haversine(lon1, lat1, lon2, lat2):
    from math import radians, cos, sin, asin, sqrt, atan2, degrees
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 3959  # Radius of earth in miles. Use 6371 for kilometers
    distance = c * r
    bearing = atan2(sin(lon2 - lon1) * cos(lat2), cos(lat1) *
                    sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1))
    bearing = degrees(bearing)
    bearing = (bearing + 360) % 360
    if distance is None or bearing is None:
        print('Error calculating with lat/lon '+str(lat1)+','+str(lon1)+','+str(lat2)+','+str(lon2))
    else:
        return distance, bearing


def findCity(stid):
    r2 = apiCall({"stid": stid, "recent": 120, "token": api_token})
    lat = r2['STATION'][0]['LATITUDE']
    lon = r2['STATION'][0]['LONGITUDE']
    loc = requests.get('https://maps.googleapis.com/maps/' +
                       'api/geocode/json?latlng=' + lat +
                       ',' + lon + '&key=' + gps_token)
#    print loc.url
    loc1 = loc.json()
    loc_city = r2['STATION'][0]['NAME']
    for i in range(len(loc1['results'])):
        if loc1['results'][i]['types'][0] == "locality":
            loc_city = loc1['results'][i]['address_components'][0]['short_name']
        else:
            continue
#    print loc_city
    return loc_city


def findOzone():
    results = apiCall(ozone_parameters)
    for i in range(len(results['STATION'])):
#        a = len(results['STATION'][0]['OBSERVATIONS']['ozone_concentration_set_1']) - 1
#        print results['STATION'][i]['OBSERVATIONS']
        variable = (results['STATION'][i]['SENSOR_VARIABLES']['ozone_concentration']).keys()
        if results['STATION'][i]['OBSERVATIONS'][variable[0]][0] >= 70:
            stid = results['STATION'][i]['STID']
            tweeting_stids["ozone"].append(stid)
            city = findCity(stid)
            state = results['STATION'][i]['STATE']
            ozone = results['STATION'][i]['OBSERVATIONS'][variable[0]][0]
            hashtags = " #" + state.lower() + "wx #ozone #airquality "
            long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                        stid + "&start=" + start_time + "&end=" + end_time)
            tweet = city + " is experiencing unhealthy ozone levels right now (" + str(ozone) + " ppb)" + hashtags + long_url
#            print tweet
            ready_tweets.append(tweet)


def findPM25():
    results = apiCall(pm25_parameters)
    for i in range(len(results['STATION'])):
#        a = len(results['STATION'][0]['OBSERVATIONS']['ozone_concentration_set_1']) - 1
        variable = (results['STATION'][i]['SENSOR_VARIABLES']['PM_25_concentration']).keys()
        if results['STATION'][i]['OBSERVATIONS'][variable[0]][0] >= 35:
            stid = results['STATION'][i]['STID']
            tweeting_stids["pm25"].append(stid)
            city = findCity(stid)
            state = results['STATION'][i]['STATE']
            pm25 = results['STATION'][i]['OBSERVATIONS'][variable[0]][0]
            hashtags = " #" + state.lower() + "wx #PM25 #airquality "
            long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                    stid + "&start=" + start_time + "&end=" + end_time)
            tweet = city + " is experiencing unhealthy PM 2.5 levels right now (" + str(pm25) + " ug m^-3)" + hashtags + long_url
#            print tweet
            ready_tweets.append(tweet)


def findWeatherCondition():
    results = apiCall(weather_parameters)
    for i in range(len(results['STATION'])):
        try:
            x = results['STATION'][i]['OBSERVATIONS']['weather_cond_code_set_1'][0]

            if x == 78 or x == 29:
                # thunder
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #thunder "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
#                catchPhrases = ["Storm Alert! ", "Grab an umbrella! ", "Watch out! ", ""]
                tweet = "Storm Alert! " + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)

            elif x == 7 or x == 11 or x == 39 or x == 33 or x == 68 or x == 69 or x == 40 or x == 30:
                # smoke dust fog haze
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #airquality "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
#                catchPhrases = ["Air Quality Alert! ", "Breathe Carefully! ", "Stay Indoors! ", ""]
                tweet = "Air Quality Alert! " + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)

            elif x == 14 or x == 15 or x == 18 or x == 19 or x == 50 or x == 52 or x == 54:
                # heavy rain
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #rain "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
#                catchPhrases = ["Storm Alert! ", "Grab an umbrella! ", "Drive Safe! ", ""]
                tweet = "Storm Alert! " + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)

            elif x == 21 or x == 32 or x == 56 or x == 60 or x == 62 or x == 67 or x == 70 or x == 37:
                # heavy snow
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #snow "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
#                catchPhrases = ["Snow Alert! ", "Blizzard Warning! ", "Drive Safe! ", "Grab the hot cocoa, ", ""]
                tweet = "Snow Alert! " + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)
        except:
            continue


def findWindChill():
    results = apiCall(windChill_parameters)
#    print resultsl
    for i in range(len(results['STATION'])):
        try:
            x = results['STATION'][i]['OBSERVATIONS']
            if x['wind_chill'][0] < -20 and x['wind_chill'][0] is not None:
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                wind_chill = results['STATION'][i]['OBSERVATIONS']['wind_chill'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #freezing #windchill "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                tweet = "Warning! " + city + " is reporting a wind chill of " + wind_chill + u'\N{DEGREE SIGN}' + 'F ' + hashtags + long_url
                ready_tweets.append(tweet)

            elif x['heat_index'][0] > 130 and x['heat_index'][0] is not None:
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                heat_index = results['STATION'][i]['OBSERVATIONS']['heat_index'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #heat #hot "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                tweet = "Warning! " + city + " is reporting a heat index of " + heat_index + u'\N{DEGREE SIGN}' + 'F ' + hashtags + long_url
                ready_tweets.append(tweet)
        except:
            continue


def alertParser():
    """Active alerts XML parser"""
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
            url = str(this['feed']['entry'][x]['id'])
            break_url = [x for x in map(str.strip, url.split('.')) if x]
            last = len(break_url) - 1
            # push break_url[last] to duplicity dict
#            print break_url[last]
            that[break_url[last]] = tmp
        else:
            print('@@@@@@@@ Error in '+str(x)+' key, ' +
                  str(this['feed']['entry'][x]['title']))
        tmp = dict()
    return that


def findAlerts():
    """Queries for nearest stations for each polygon element"""
    alerts = alertParser()
    alertEmitter(alerts, 'NWS_ALERTS_current', False)
    alertKeys = alerts.keys()

#    print alertKeys
    for i in range(len(alerts)):
        if alerts[alertKeys[i]]['severity'] == "Severe":
            print alerts[alertKeys[i]]['category']

    # enable line below to save each alert json
    # emitter(alerts, 'NWS_ALERTS_', True)
#    print alerts
#    return alerts


def alertEmitter(dict_, filename, timestamp):
    """Emit the file"""
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


#findOzone()
#findPM25()
#findWeatherCondition()
#findWindChill()
findAlerts()


# TODO: add extreme wind, temps, precip
# check NWS for issued warnings (parse?), add dict with identifier to prevent duplicity among warnigns
# create unique identifier to each tweet to prevent duplicity
# revise/remove random catchphrases. more uniform and systematic


def sendToTwitter():
    findOzone()
    findPM25()
    findWeatherCondition()
    findAlerts()
#    length = len(ready_tweets)
#    delay = 3600000 / length
    for i in range(len(ready_tweets)):
        api.update_status(ready_tweets[i])
#        time.sleep(30000)

#sendToTwitter()
