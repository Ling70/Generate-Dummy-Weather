# -*- coding: utf-8 -*-
"""
Date: June 4th 2018 
Brief: This python code generates dummy weather data, the required output is as below: 
    Station|GEO Location|Local Time|Conditions|Temperature|Pressure|Humidity
    SYD|-33.86,151.21,39|2015-12-23T05:02:12Z|Rain|+12.5|1004.3|97
    MEL|-37.83,144.98,7|2015-12-24T15:30:55Z|Snow|-5.3|998.4|55
    ADL|-34.92,138.62,48|2016-01-03T12:35:37Z|Sunny|+39.4|1114.1|12
@author: Ling Qi
"""

from geopy.geocoders import Nominatim
import urllib.request
import json
import random
import itertools
import copy
import calendar
import numpy as np
import pandas as pd
from datetime import timedelta
from datetime import datetime
from geopy.exc import GeocoderTimedOut
from collections import defaultdict
from time import strptime
import rasterio
from affine import Affine
from pyproj import Proj, transform

# declare stations with IATA codes which need to generate weather data 
sta_list = {"SYD": "Sydney, Australia", "MEL": "Melbourne, Australia", "ADL": "Adelaide, Australia", 
            "PER": "Perth, Australia", "BRB": "Brisbane, Australia", "DAR": "Darwin, Australia", 
            "HOB": "Hobart, Australia", "CAN": "Canberra, Australia", 
            "NTL": "Newcastle, Australia", "OOL": "Gold Coast, Australia"}

# declare weather condition, I was not able to find historical data, so this is assumption based on experience
w_conditions = {"Sunny": {"temperature": (10, 46.5), "pressure": (1000, 1200), "humidity": (10, 40)},
              "Cloudy": {"temperature": (10, 38), "pressure": (900, 1000), "humidity": (20, 50)},
              "Rain": {"temperature": (0, 38), "pressure": (700, 900), "humidity": (50, 99)},
              "Snow": {"temperature": (-15, 0), "pressure": (700, 900), "humidity": (50, 99)}}

# read temperature scope file
def read_data(csvfilename): 
    return pd.read_csv(csvfilename)

# generate temperature dictionary
def get_temperature_for_station(dframe, station, s_name, size): 
    dic_temperature = defaultdict(dict)
    df_station = dframe.loc[dframe['Station'] == station]
    df_highest = df_station.loc[dframe['temperature'] == 'Highest']
    df_lowest = df_station.loc[dframe['temperature'] == 'Lowest']
    for c in dframe.columns[2:]:  
        h = df_highest[c].item()
        l = df_lowest[c].item()
        numb = np.random.uniform(l, h, size)
        dic_temperature[s_name][c] = ['%.1f' % n for n in numb]
    return dic_temperature
   
# function to generate random weather 
def generate_weather(d):
    cond = random.choice(list(d.keys()))
    condition = w_conditions[cond]
    (tempMin, tempMax) = condition["temperature"]
    (presMin, presMax) = condition["pressure"]
    (humtMin, humtMax) = condition["humidity"]

    return cond, str(round(random.uniform(presMin, presMax), 1)), str(random.randint(humtMin, humtMax))

# function to generate random weather based on temperature
def generate_weather_basedOnTemperature(d, t):
    dic_temp = copy.deepcopy(d)
    for k in d.keys(): 
        condition = w_conditions[k]
        (tMin, tMax) = condition["temperature"]
        if float(t) < float(tMin) or float(t) > float(tMax): 
           del dic_temp[k]
    
    return (generate_weather(dic_temp))
      
# function to generate random datetime based on month short name
def generate_date(start, end, mon):
    s_year = strptime(start, '%m/%d/%Y').tm_year
    e_year = strptime(end, '%m/%d/%Y').tm_year
    year = np.random.choice(range(s_year, e_year))
    month = strptime(mon,'%b').tm_mon
    dates = calendar.Calendar().itermonthdates(year, month)
    date_in_m = random.choice([date for date in dates if date.month == month])
    date_in_mon = datetime.combine(date_in_m, datetime.min.time())
    random_second = random.choice(range(0, 23*60*60))
    date_format = "%Y-%m-%dT%H:%M:%SZ" 
    random_date = date_in_mon + timedelta(seconds=random_second)
    return datetime.strftime(random_date, date_format)

# function to output latitude and longtitude from geographic image file 
def get_lon_lat_from_image(fname): 
    rs = rasterio.open(fname)
    ulc = rs.affine
    p1 = Proj(rs.crs)
    pv = rs.read() 
    
    col, row = np.meshgrid(np.arange(pv.shape[2]), np.arange(pv.shape[1]), sparse = True)
    
    ult = ulc*Affine.translation(0.5, 0.5)
    rc_est_nth = lambda r, c: (r, c)*ult
    
    east, north = np.vectorize(rc_est_nth, otypes=[np.float, np.float])(row, col)

    p2 = Proj(proj = 'latlong', datum = 'WGS84')
    lon, lat = transform(p1, p2, east, north)
    
    return lon, lat
    
# test function
# print(get_lon_lat_from_image('gebco_08_rev_elev_D2_grey_geo.tif'))

# function to get latitude and longitude from city and its country
# send request to google api, maximum 2500 request per day 
def get_lon_lat_from_station(s_citycountry): 
    geolocator = Nominatim()
    try:
        location = geolocator.geocode(s_citycountry, timeout=None)
        return location.latitude, location.longitude
    except GeocoderTimedOut as e:
        print("Error: geocode failed on input ", s_citycountry)
        return None, None

# function to get elevation from latitude and longitude, 
# send request to google api, maximum 2500 request per day 
def get_elevation(lat, lng, sensor=False):
    url = 'http://maps.google.com/maps/api/elevation/json'
    url_fit = "locations=%.7f,%.7f&sensor=%s" % (lat, lng, "true" if sensor else "false")
    url_full = url + "?" + url_fit
    
    request = urllib.request.urlopen(url_full)
    response = json.loads(request.read().decode()) 
    if response["status"] == "OK":
        result = response["results"][0]
        return int(result["elevation"])
    else: 
        return None

# create dictionary to store all stations lat, lon, elevation 
def get_geo_dict(s_list): 
    geo_dict = {}
    
    for k, v in s_list.items():
        print(v)
        la, ln = get_lon_lat_from_station(v)
        el = get_elevation(la, ln, sensor=False)
        geo_dict[k] = (la, ln, el)
    
    return geo_dict

# since there is limited number of google api request per day, 
# I have pre-generated latitude, longitude and elevation for all stations
geo_dict_manual = {'ADL': (-34.9274284, 138.599899, 45),
 'BRB': (-27.4689682, 153.0234991, 16),
 'CAN': (-35.2975906, 149.1012676, 555),
 'DAR': (-12.46044, 130.8410469, 33),
 'HOB': (-42.8825088, 147.3281233, 11),
 'MEL': (-37.8142176, 144.9631608, 9),
 'NTL': (-32.80608325, 151.842490802548, 4),
 'OOL': (-28.164853, 153.508104553275, 6),
 'PER': (-31.9527121, 115.8604796, 13),
 'SYD': (-33.8548157, 151.2164539, 4)}

def main():         
      
    s_date = '1/1/1998'
    e_date = '1/1/2018'
    
    pd_tpt = read_data('temperature_scope.csv')

    dic_tmpt = defaultdict(dict)
    for k, v in sta_list.items(): 
        dic_t = get_temperature_for_station(pd_tpt, v, k, 1000)
        dic_tmpt.update(dic_t)

    weatherFile = open("weather_data.dat", "w")
    weatherFile.write('Station|GEO Location|Local Time|Conditions|Temperature|Pressure|Humidity\n')
    
    for k, d in dic_tmpt.items(): 
        for ke, va in d.items():
            for i in va: 
                #geo_dic = get_geo_dict(k)  # use this for automaticately generated lat, lon and elevation
                geo_dic = geo_dict_manual # use this for pre-generated lat, lon and elevation
                geo = geo_dic[k]
                local_time = generate_date(s_date, e_date, ke)
                c, p, h = generate_weather_basedOnTemperature(w_conditions, i) 
                record = k + "|" + ','.join(map(str, geo)) + "|" + str(local_time) + "|" + c + "|" + str(i) + "|" + p + "|" + h + "\n"
                weatherFile.write(record)
        
    weatherFile.close()
    
if __name__ == '__main__':
    main()

