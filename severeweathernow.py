#!/uufs/chpc.utah.edu/common/home/u0540701/MyVenv/bin/python

# Created by Randall Vowles, API token and twitter account belong to me

import configparser
import requests
import json
import tweepy
import datetime
import random
import matplotlib.pyplot as plt
import time

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
                      "vars": "weather_condition,weather_cond_code,heat_index,wind_chill",
                      "qc_checks": "synopticlabs", "recent": "30", "network": "1", "units": "english"}
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
#    print results.url
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
        try:
            if results['STATION'][i]['OBSERVATIONS'][variable[0]][0] >= 70:
                stid = results['STATION'][i]['STID']
                tweeting_stids["ozone"].append(stid)
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                ozone = results['STATION'][i]['OBSERVATIONS'][variable[0]][0]
                hashtags = " #" + state.lower() + "wx #ozone #airquality "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                tweet = city + " is experiencing unhealthy ozone levels right now (" + str(ozone) + "ppb)" + hashtags + long_url
#                print tweet
                ready_tweets.append(tweet)
        except(KeyError):
            continue


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
            tweet = city + " is experiencing unhealthy PM 2.5 levels right now (" + str(pm25) + "ug m^-3)" + hashtags + long_url
#            print tweet
            ready_tweets.append(tweet)


def findWeatherCondition():
    results = apiCall(weather_parameters)
    for i in range(len(results['STATION'])):
        try:
            x = results['STATION'][i]['OBSERVATIONS']['weather_cond_code_set_1'][0]
            if x == 5 or x == 20 or x == 66 or x == 78:
                # thunder
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #thunder "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                catchPhrases = ["Storm Alert! ", "Grab an umbrella! ", "Watch out! ", ""]
                tweet = random.choice(catchPhrases) + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)

            elif x == 7 or x == 8 or x == 11 or x == 39 or x == 33 or x == 34 or x == 35 or x == 68 or x == 69 or x == 40:
                # smoke dust fog haze
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #airquality "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                catchPhrases = ["Air Quality Alert! ", "Breathe Easy! ", "Stay Indoors! ", ""]
                tweet = random.choice(catchPhrases) + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)

            elif x == 1 or x == 2 or x == 14 or x == 15 or x == 16 or x == 18 or x == 19 or x == 50 or x == 52 or x == 54:
                # heavy rain
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #rain "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                catchPhrases = ["Storm Alert! ", "Grab an umbrella! ", "Drive Safe! ", ""]
                tweet = random.choice(catchPhrases) + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)

            elif x == 3 or x == 4 or x == 21 or x == 22 or x == 23 or x == 24 or x == 25 or x == 32 or x == 56 or x == 60 or x == 62 or x == 67 or x == 70 or x == 37:
                # heavy snow
                stid = results['STATION'][i]['STID']
                city = findCity(stid)
                state = results['STATION'][i]['STATE']
                code_string = results['STATION'][i]['OBSERVATIONS']['weather_condition_set_1d'][0]
                hashtags = " #" + state.lower() + "wx #wxalert #snow "
                long_url = ("https://synopticlabs.org/demos/tabtable/?stid=" +
                            stid + "&start=" + start_time + "&end=" + end_time)
                catchPhrases = ["Snow Alert! ", "Blizzard Warning! ", "Drive Safe! ", "Grab the hot cocoa, ", ""]
                tweet = random.choice(catchPhrases) + findCity(stid) + " is reporting " + code_string + hashtags + long_url
                ready_tweets.append(tweet)
        except:
            continue


#findOzone()
#findPM25()
#findWeatherCondition()


def sendToTwitter():
    findOzone()
    findPM25()
    findWeatherCondition()
    length = len(ready_tweets)
    delay = 3600000 / length
    for i in range(len(ready_tweets)):
        api.update_status(ready_tweets[i])
#        time.sleep(delay)

sendToTwitter()
