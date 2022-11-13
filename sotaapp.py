#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_compress import Compress

import json

from gsi_geocoder import gsi_geocoder, gsi_rev_geocoder, gsi_geocoder_vue, radio_station_qth
from aprs_tracklog import aprs_track_stations, aprs_track_tracks
from sotasummit import sotasummit,jaffpota_parks, sotajaffpota_ref
from sotaalerts import sotaalerts, sotaspots, sotaalerts_and_spots
from geomag import kp_indicies

app = Flask(__name__)
#app.config["COMPRESS_REGISTER"] = False
compress = Compress()
compress.init_app(app)
CORS(app, resources={r"/api": {"origins":"*"}})

@app.route("/api/reverse-geocoder/LonLatToAddress")
def LonLatAddress():
    lat = request.args.get('lat')
    lng = request.args.get('lon')
    res = gsi_rev_geocoder(lat, lng)
    return(json.dumps(res))

@app.route("/api/reverse-geocoder/LonLatToAddressElev")
def LonLatAddressElev():
    lat = request.args.get('lat')
    lng = request.args.get('lon')
    res = gsi_rev_geocoder(lat, lng, True)
    return(json.dumps(res))

@app.route("/api/reverse-geocoder/LonLatToAddressElevMapCode")
def LonLatAddressElevMapCode():
    lat = request.args.get('lat')
    lng = request.args.get('lon')
    res = gsi_rev_geocoder(lat, lng, True, True)
    return(json.dumps(res))

@app.route("/api/radio-station/qth")
def CallToQTH():
    callsign = request.args.get('call')
    res = radio_station_qth(callsign, False)
    return(json.dumps(res))

@app.route("/api/radio-station/qth_code")
def CallToQTHwithCode():
    callsign = request.args.get('call')
    res = radio_station_qth(callsign, True)
    return(json.dumps(res))

@app.route("/api/jcc-jcg-search",methods=['POST','GET'])
def JCCJCGGeocoder():
    try:
        if request.method == 'POST':
            q = request.get_json()['q']
        else:
            q = request.args.get('q','')
        res = gsi_geocoder_vue(q, True, False)
        return(json.dumps(res))
    except Exception as err:
        raise err
        return(json.dumps({'error query': q}))


@app.route("/api/aprs-tracklog/stations")
def AprsTrackLogStations():
    rg = request.args.get('range')
    res = aprs_track_stations(rg)
    return(json.dumps(res))


@app.route("/api/aprs-tracklog/tracks")
def AprsTrackLogTracks():
    stn = request.args.get('station')
    rg = request.args.get('range')
    res = aprs_track_tracks(stn, rg)
    return(json.dumps(res))

@app.route("/api/sotalive-json/<string:filename>")
def SOTAliveFile(filename):
    path = '/usr/share/nginx/html/json/'
    try:
        with open(path+filename, 'r') as f:
            return(json.dumps(json.load(f)))
    except FileNotFoundError as e:
        return(json.dumps({'Error':path+filename+" not found."}))
    except Exception as e:
        print(e)
        return(json.dumps({'Error':'internal error'}))

@app.route("/api/jaff-pota")
def JaffpotaParks():
    parkid = request.args.get('parkid')
    lat = request.args.get('lat')
    lng = request.args.get('lon')
    lat2 = request.args.get('lat2')
    lng2 = request.args.get('lon2')
    size= request.args.get('size')
    res = jaffpota_parks({'parkid': parkid,
                          'lat':lat,'lon':lng,
                          'lat2':lat2,'lon2':lng2,
                          'size':size})
    return(json.dumps(res))

@app.route("/api/sota-jaff-pota")
def SOTAJAFFPOTAParks():
    refid = request.args.get('refid')
    res = sotajaffpota_ref({'refid': refid})
    return(json.dumps(res))

@app.route("/api/sotasummits/<string:region>")
def SOTAsummits(region):
    ambg = request.args.get('ambg')
    code = request.args.get('code')
    name = request.args.get('name')
    lat = request.args.get('lat')
    lng = request.args.get('lon')
    lat2 = request.args.get('lat2')
    lng2 = request.args.get('lon2')
    rng = request.args.get('range')
    srng = request.args.get('srange')
    park= request.args.get('park')
    elev = request.args.get('elevation')
    flag = request.args.get('flag')
    potadb = request.args.get('potadb')
    res = sotasummit(region,
                     {'code': code,
                      'name': name,
                      'ambg': ambg,
                      'flag':flag,
                      'lat':lat,'lon':lng,
                      'lat2':lat2,'lon2':lng2,
                      'park':park,
                      'potadb':potadb,
                      'elevation':elev,
                      'range':rng,
                      'srange':srng})
    return(json.dumps(res))

@app.route("/api/sotaalerts/summits/<string:code_prefix>")
def SOTAlertsSummit(code_prefix):
    fm = request.args.get('from')
    to = request.args.get('to')
    res = sotaalerts(code_prefix, None, fm, to)
    return(json.dumps(res))


@app.route("/api/sotaalerts/continent/<string:continent>")
def SOTAlertsContinent(continent):
    fm = request.args.get('from')
    to = request.args.get('to')
    res = sotaalerts(None, continent.split(','), fm, to)
    return(json.dumps(res))


@app.route("/api/sotaalerts")
def SOTAlerts():
    fm = request.args.get('from')
    to = request.args.get('to')
    res = sotaalerts(None, None, fm, to)
    return(json.dumps(res))

@app.route("/api/sotaspots/summits/<string:code_prefix>")
def SOTASpotsSummit(code_prefix):
    mode = request.args.get('mode')
    to = request.args.get('to')
    res = sotaspots(code_prefix, None, mode, to)
    return(json.dumps(res))

@app.route("/api/sotaspots/continent/<string:continent>")
def SOTASpotsContinent(continent):
    mode = request.args.get('mode')
    to = request.args.get('to')
    res = sotaspots(None, mode, continent.split(','), to)
    return(json.dumps(res))

@app.route("/api/sotaspots")
def SOTASpots():
    mode = request.args.get('mode')
    to = request.args.get('to')
    res = sotaspots(None, mode, None, to)
    return(json.dumps(res))

@app.route("/api/sota-alerts-spots/summits/<string:code_prefix>")
def SOTAAlertsSpotsSummit(code_prefix):
    mode = request.args.get('mode')
    fm = request.args.get('from')
    to = request.args.get('to')
    res = sotaalerts_and_spots(code_prefix, mode, None, fm, to)
    return(json.dumps(res))

@app.route("/api/sota-alerts-spots/continent/<string:continent>")
def SOTAAlertsSpotsContinent(continent):
    mode = request.args.get('mode')
    fm = request.args.get('from')
    to = request.args.get('to')
    res = sotaalerts_and_spots(None, mode, continent.split(','), fm, to)
    return(json.dumps(res))

@app.route("/api/sota-alerts-spots")
def SOTAAlertsSpots():
    mode = request.args.get('mode')
    fm = request.args.get('from')
    to = request.args.get('to')
    res = sotaalerts_and_spots(None, mode, None, fm, to)
    return(json.dumps(res))

@app.route("/api/geomag")
def GeoMag():
    res = kp_indicies()
    return(json.dumps(res))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port = 5000)
