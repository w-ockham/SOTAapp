# SOTA App
SOTA App is an API for SOTA Web Applications.

# API References
## Get Summits Information
### Resource URL
JA
```
https://www.sotalive.tk/api/sotasummits/ja
```
Worldwide
```
https://www.sotalive.tk/api/sotasummits/ww
```
### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
code | Return a SOTA summit specified by `code`        | | JA/NN-001|
<br> | Return SOTA summits within a given range of the lattitude and longitude. The parameter value is specified by `lat,lon,range`.
lat | attitude | | 35.754976
lon | longitude | | 138.232899
range| range in kilometers| 20 | 10

### Example Requests
```html
https://www.sotalive.tk/api/sotasummits/ja?lat=35.754976&lon=138.232879&range=5
```
### Example Response
```html
{"errors": "OK", "summits": [
{"code": "JA/YN-008", "lat": 35.7317, "lon": 138.2413, "pts": 10, "elev": 2799.0,
"name": "Asayomine", "desc": "Minami-Alps-cityHokuto-city",
"name_j": "\u30a2\u30b5\u30e8\u5cf0",
"desc_j": "\u5c71\u68a8\u770c\u5357\u30a2\u30eb\u30d7\u30b9\u5e02\u5c71\u68a8\u770c\u5317\u675c\u5e02"},

{"code": "JA/YN-005", "lat": 35.758, "lon": 138.2366, "pts": 10, "elev": 2967.0,
"name": "Komagatake", "desc": "Hokuto-cityIna-city",
"name_j": "\u99d2\u30f6\u5cb3",
"desc_j": "\u5c71\u68a8\u770c\u5317\u675c\u5e02\u9577\u91ce\u770c\u4f0a\u90a3\u5e02"},

{"code": "JA/YN-010", "lat": 35.779, "lon": 138.21, "pts": 10, "elev": 2685.0,
"name": "Nokogiriyama", "desc": "Hokuto-cityIna-city",
"name_j": "\u92f8\u5c71",
"desc_j": "\u5c71\u68a8\u770c\u5317\u675c\u5e02\u9577\u91ce\u770c\u4f0a\u90a3\u5e02"}]}
```
## Get JCC/JCG Code and Address (JA region only)
### Resource URL
```
https://www.sotalive.tk/api/reverse-geocoder/LonLatToAddress
```
Return with the elevation.
```
https://www.sotalive.tk/api/reverse-geocoder/LonLatToAddressElev
```
### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
<br>| Return the JCC/JCG and its address by a given lattitude and longitude. The parameter value is specified by `lat,lon`.
lat | attitude | | 35.754976
lon | longitude | | 138.232899

### Example Requests
```
https://www.sotalive.tk/api/reverse-geocoder/LonLatToAddressElev?lat=35.917757&lon=138.523715
```
### Example Response
```
{"pref": "\u9577\u91ce\u770c",
 "addr2": "\u5357\u4f50\u4e45\u90e1\u5ddd\u4e0a\u6751",
 "addr1": "\u5927\u5b57\u5fa1\u6240\u5e73",
 "type": "JCG", "jcg": "09017",
 "jcg_text": "\u5357\u4f50\u4e45\u90e1",
 "elevation": 1797.5,
 "hsrc": "5m\uff08\u30ec\u30fc\u30b6\uff09",
 "errors": "OK"}
```
## Get recent SOTA Alerts
Return alerts within the next 16 hours.  
You can also specify the summit by `code_prefix` or `continent_list`.
#### Resource URL
GET All Alerts
```
https://www.sotalive.tk/api/sotaalerts
```
GET Alerts specified by the summit code `code_prefix`.
```
https://www.sotalive.tk/api/sotaalerts/summits/<code_prefix>
```

GET Alerts specified by the continent list `continent_list` .   
`continent_list` is comma separated list of a continent .  
Available continent is in one of the following codes: 'EU','AF','AS','OC','NA' and 'SA'.
```
https://www.sotalive.tk/api/sotaalerts/continent/<continent_list>
```
#### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
range| Return alert list within a given range. The parameter value is specified by `range` in hours. | 16 | 3

#### Example Requests
Request 1:
```
https://www.sotalive.tk/api/sotaalerts/summits/W4?range=16
```
Request 2:
```
https://www.sotalive.tk/api/sotaalerts/continent/NA,EU
```
#### Example Response
Response 1:
```
{"errors": "OK", "alerts": [
{"dateActivated": "2020-05-03T07:00:00+00:00",
 "activatingCallsign": "W1PTS/P",
 "staion": "W1PTS",
 "summitCode": "W4C/WM-029",
 "summitDetails": "Rich Benchmark, 1556m, 8 pts",
 "lat": 35.2922, "lon": -83.0359,
 "frequency": "5-cw, 7-cw, 5-ssb, 7-ssb, 14-ssb, 145-fm",
 "comments": "time +/- Adventure Team FOG",
 "poster": "(Posted by W1PTS)"},
{"dateActivated": "2020-05-03T07:00:00+00:00",
 "activatingCallsign": "KB7HH",
 "station": "KB7HH",
 "summitCode": "W7A/AW-013",
 "summitDetails": "Spruce Mountain, 2346m, 10 pts",
 "lat": 34.4631, "lon": -112.4038,
 "frequency": "7.033-cw, 10.113-cw, 14.030-cw",
 "comments": "ANNUAL AZ S2S",
"poster": "(Posted by KB7HH)"}, ... ]}
```
Response 2:
```
{"errors": "OK", "alerts": [
{"dateActivated": "2020-05-06T11:30:00",
"activatingCallsign": "DF3FS/P",
"station":"DF3FS",
"summitCode": "DM/HE-570",
"summitDetails": "Gro\u00dfe Haube, 658m, 6 pts",
"association": "Germany (Low Mountains)",
"continent": "EU",
"lat": 50.3877, "lon": 9.7546,
"frequency": "7-cw, 10-cw, 14-cw",
"comments": "Time may be + or - 1 hour",
"poster": "(Posted by DF3FS)"},
{"dateActivated": "2020-05-06T15:30:00",
 "activatingCallsign": "W1PTS",
 "station":"W1PTS",
 "summitCode": "W4G/NG-022",
 "summitDetails": "Black Mountain, 1140m, 8 pts",
 "association": "USA - Georgia",
 "continent": "NA",
 "lat": 34.6749, "lon": -84.0061,
 "frequency": "5-cw, 7-cw, 5-ssb, 7-ssb, 14-ssb, 145-fm",
 "comments": "time +/- Adventure Team FOG", "poster": "(Posted by W1PTS)"},
 ... ]}
```

## Get recent SOTA Spots
Return spots within the past 24 hours.   
You can also specify the summit by `code_prefix` or `continent_list`.
#### Resource URL
GET All spots
```
https://www.sotalive.tk/api/sotaspots
```
GET Spots specified by the summit code `code_prefix`.
```
https://www.sotalive.tk/api/sotaspots/summits/<code_prefix>
```
GET Spots specified by the continent list `continent_list` .  
`continent_list` is comma separated list of a continent.  
Available continent is in one of the following codes: 'EU','AF','AS','OC','NA' and 'SA'.
```
https://www.sotalive.tk/api/sotaspots/continent/<continent_list>
```
#### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
range| Return spot list within a given range. The parameter value is specified by `range` in hours. | 24 | 3
mode | The mode of the spots for which to return results. | |cw

#### Example Requests
Request 1:
```
https://www.sotalive.tk/api/sotaspots/summits/W?range=16&mode=cw

```
Request 2:
```
https://www.sotalive.tk/api/sotaspots/continent/NA?mode=cw

```
#### Example Response
Response 1:
```
{"errors": "OK",
 "spots": [
 {"timeStamp": "2020-05-04T20:37:09",
 "activatorCallsign": "N0DNF",
 "station": "N0DNF",
 "summitCode": "W7I/SI-153",
 "summitDetails": "7081, 2158m, 4 pts",
 "lat": 42.7673, "lon": -112.4596,
 "frequency": "14.062",
 "mode": "CW",
 "comments": "De ZL1BYZ", "poster": "ZL1BYZ"},
... ]}
 ```
Response 2:
```
{"errors": "OK",
"spots": [
{"timeStamp": "2020-05-05T15:23:10",
 "activatorCallsign": "N6MKW",
 "station":"N6MKW",
 "summitCode": "W6/CT-093",
 "summitDetails": "Burnt Peak, 1766m, 6 pts",
 "association": "USA",
 "continent": "NA",
 "lat": 34.6825,
 "lon": -118.5769,
 "frequency": "7.000",
 "mode": "cw",
 "comments": "[APRS2SOTA] QRT TU",
 "poster": "APRS2SOTA"},
 {"timeStamp": "2020-05-05T16:51:08",
 "activatorCallsign": "AC0PR/P",
 "station":"AC0PR",
 "summitCode": "W7U/IR-035",
 "summitDetails": "7450, 2271m, 4 pts",
 "association": "USA - Utah",
 "continent": "NA",
 "lat": 37.7038, "lon": -113.468,
 "frequency": "10.1110",
 "mode": "CW",
 "comments": "[RBNHole] at N0OI 22 WPM 21 dB SNR",
 "poster": "RBNHOLE"},
 ... ]}
```

## Get Activator's APRS tracks
### Station List
#### Resource URL
```
https://www.sotalive.tk/api/aprs-tracklog/stations
```
#### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
range| Return activator list within a given range. The parameter value is specified by `range` in hours. | 48 | 3

#### Example Requests
```
https://www.sotalive.tk/api/aprs-tracklog/stations?range=3
```
#### Example Response
```
{"stations": ["JL1NIE", "JS1YFC"]}
```
### Track List
#### Resource URL
```
https://www.sotalive.tk/api/aprs-tracklog/tracks
```
#### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
station|Return activator's tracks in GeoJSON format by a given callsign. The parameter value is specified by `station` . |  | JL1NIE
range| Return activator's tracks in GeoJSON format within a given range. The parameter value is specified by `range` in hours. | 48 | 32

#### Example Requests
```
https://www.sotalive.tk/api/aprs-tracklog/tracks?range=32&station=JL1NIE
```
#### Example Response
```
{"tracks": [
 {"type": "Feature",
   "geometry": {"type": "LineString", "coordinates": [[47.769667, 7.7455]]}, "properties":
   {"callsign": "JL1NIE", "ssid": "7", "lastseen": "2020-05-02T23:32:29"}},

  ]}  
```
