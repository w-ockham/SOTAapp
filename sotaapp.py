#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask
from flask import request
import json

from reverse_geocoder import rev_geocode
from aprs_tracklog import aprs_track_stations, aprs_track_tracks
from sotasummit import sotasummit
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
     stn = request.args.get('station')
     rg = request.args.get('range')
     res = aprs_track_tracks(stn, rg)
     return(json.dumps(res))

@app.route("/api/sotasummits/<string:region>")
def SOTAsummits(region):
     code = request.args.get('code')
     lat = request.args.get('lat')
     lng = request.args.get('lon')
     rng = request.args.get('range')
     res = sotasummit(region, code, lat, lng, rng)
     return(json.dumps(res))

@app.route("/api/sotaalerts/summits/<string:code_prefix>")
def SOTAlertsSummit(code_prefix):
     rng = request.args.get('range')
     res = sotaalerts(code_prefix, None, rng)
     return(json.dumps(res))

@app.route("/api/sotaalerts/continent/<string:continent>")
def SOTAlertsContinent(continent):
     rng = request.args.get('range')
     res = sotaalerts(None, continent.split(','), rng)
     return(json.dumps(res))

@app.route("/api/sotaalerts")
def SOTAlerts():
     rng = request.args.get('range')
     res = sotaalerts(None, None, rng)
     return(json.dumps(res))\

@app.route("/api/sotaspots/summits/<string:code_prefix>")
def SOTASpotsSummit(code_prefix):
     mode = request.args.get('mode')
     rng = request.args.get('range')
     res = sotaspots(code_prefix, None, mode, rng)
     return(json.dumps(res))

@app.route("/api/sotaspots/continent/<string:continent>")
def SOTASpotsContinent(continent):
     mode = request.args.get('mode')
     rng = request.args.get('range')
     res = sotaspots(None , mode, continent.split(','), rng)
     return(json.dumps(res))

@app.route("/api/sotaspots")
def SOTASpots():
     mode = request.args.get('mode')
     rng = request.args.get('range')
     res = sotaspots(None, mode, None, rng)
     return(json.dumps(res))

if __name__ == "__main__":
     app.run()
