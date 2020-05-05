# SOTA App
SOTA App is an API for SOTA Web Applications.

# API References
## Get Summits Information (JA region only)
### Resource URL
```
https://www.sotalive.tk/api/sotasummits/ja
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
Return alerts within the next 16 hours. You can also specify the summit by `code_prefix`.
#### Resource URL
```
https://www.sotalive.tk/api/sotaalerts

https://www.sotalive.tk/api/sotaalerts/summits/<code_prefix>
```
#### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
range| Return alert list within a given range. The parameter value is specified by `range` in hours. | 16 | 3

#### Example Requests
```
https://www.sotalive.tk/api/sotalerts/W4?range=16
```
#### Example Response
```
{"errors": "OK", "alerts": [
{"dateActivated": "2020-05-03T07:00:00+00:00",
 "activatingCallsign": "W1PTS",
 "summitCode": "W4C/WM-029",
 "summitDetails": "Rich Benchmark, 1556m, 8 pts",
 "lat": 35.2922, "lon": -83.0359,
 "frequency": "5-cw, 7-cw, 5-ssb, 7-ssb, 14-ssb, 145-fm",
 "comments": "time +/- Adventure Team FOG",
 "poster": "(Posted by W1PTS)"},
{"dateActivated": "2020-05-03T07:00:00+00:00",
 "activatingCallsign": "KB7HH",
 "summitCode": "W7A/AW-013",
 "summitDetails": "Spruce Mountain, 2346m, 10 pts",
 "lat": 34.4631, "lon": -112.4038,
 "frequency": "7.033-cw, 10.113-cw, 14.030-cw",
 "comments": "ANNUAL AZ S2S",
"poster": "(Posted by KB7HH)"}, ... ]}
```
## Get recent SOTA Spots
Return spots within the past 24 hours. You can also specify the summit by `code_prefix`.
#### Resource URL
```
https://www.sotalive.tk/api/sotaspots

https://www.sotalive.tk/api/sotaspots/summits/<code_prefix>
```
#### Parameters
Name | Description |Default Value|Example  
:----|:------------|:------------|:---------
range| Return spot list within a given range. The parameter value is specified by `range` in hours. | 24 | 3
mode | The mode of the spots for which to return results. | |cw

#### Example Requests
```
https://www.sotalive.tk/api/sotaspots/summits/W?range=16&mode=cw

```
#### Example Response
```
{"errors": "OK",
 "spots": [
 {"timeStamp": "2020-05-04T20:37:09",
 "activatorCallsign": "N0DNF",
 "summitCode": "W7I/SI-153",
 "summitDetails": "7081, 2158m, 4 pts",
 "lat": 42.7673, "lon": -112.4596,
 "frequency": "14.062",
 "mode": "CW",
 "comments": "De ZL1BYZ", "poster": "ZL1BYZ"},
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
station:Return activator's tracks in GeoJSON format by a given callsign. The parameter value is specified by `station` . |  | JL1NIE
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
