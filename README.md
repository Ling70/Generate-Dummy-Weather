# Generate-Dummy-Weather

Background 

1. 	This code will generate dummy weather data for 10 stations, it can be used to generate any stations with temperature min/max value for each stations
2. 	This code generates dummy weather for Sydney, Melbourne, Adelaide, Brisbane, Canberra, Darwin, Perth, Hobart, Newcastle, Gold Coast
	  each station's reference temperature scope data (min, max by month) was extracted from below website: 
	  http://www.bom.gov.au/climate/data/index.shtml?bookmark=200
3. 	Geographical information was extracted via google api based on stations' name and country. It could be generated via geographic map provided, 
    however send request to googleapi to get station name by latitude and longtitude sometimes produce error. 

Set up

1. You need python 3.6 to run this code. 

2. Please install the following libraries: 
    pip install geopy
    pip install rasterio
    pip install pyproj
    
3. Save "temperature_scope.csv" file at the same directory as GenerateWeather.py.

Run

Run python classifier.py to generate data, output file name "weather_data.dat"
