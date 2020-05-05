#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask
from flask import request
import json

from reverse_geocoder import rev_geocode
from aprs_tracklog import aprs_track_stations, aprs_track_tracks
from sotasummit import sotasummit_ja
from sotaalerts import sotaalerts, sotaspots

app = Flask(__name__)

@app.route("/api/reverse-geocoder/LonLatToAddress")
def LonLatAddress():
     lat = request.args.get('lat')
     lng = request.args.get('lon')
     res = rev_geocode(lat, lng, False)
     return(json.dumps(res))

@app.route("/api/reverse-geocoder/LonLatToAddressElev")
def LonLatAddressElev():
     lat = request.args.get('lat')
     lng = request.args.get('lon')
     res = rev_geocode(lat, lng, True)
     return(json.dumps(res))
            
@app.route("/api/aprs-tracklog/stations")
def AprsTrackLogStations():
     rg = request.args.get('range')
     res = aprs_track_stations(rg)
     return(json.dumps(res))

@app.route("/api/aprs-tracklog/tracks")
def AprsTrackLogTracks():
     rg = request.args.get('range')
     res = aprs_track_tracks(rg)
     return(json.dumps(res))

@app.route("/api/sotasummits/ja")
def SOTAsummitsJA():
     code = request.args.get('code')
     lat = request.args.get('lat')
     lng = request.args.get('lon')
     rng = request.args.get('range')
     res = sotasummit_ja(code,lat,lng,rng)
     return(json.dumps(res))

@app.route("/api/sotaalerts/<string:code_prefix>")
def SOTAlerts2(code_prefix):
     rng = request.args.get('range')
     res = sotaalerts(code_prefix, rng)
     return(json.dumps(res))

@app.route("/api/sotaalerts")
def SOTAlerts():
     rng = request.args.get('range')
     res = sotaalerts(None, rng)
     return(json.dumps(res))\

@app.route("/api/sotaspots/<string:code_prefix>")
def SOTASpots2(code_prefix):
     mode = request.args.get('mode')
     rng = request.args.get('range')
     res = sotaspots(code_prefix,mode,rng)
     return(json.dumps(res))

@app.route("/api/sotaspots")
def SOTASpots():
     mode = request.args.get('mode')
     rng = request.args.get('range')
     res = sotaspots(None,mode,rng)
     return(json.dumps(res))

if __name__ == "__main__":
     app.run()
