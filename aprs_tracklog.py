from datetime import datetime, timezone
from geojson import LineString, Feature, FeatureCollection
import json
import sqlite3
import time

ssid_table = ['7','9','6','5','8']

def aprs_track_stations(rg):
     try:
          conn = sqlite3.connect('aprslog.db')
          cur = conn.cursor()
          res = []
          if not rg:
               rg = 48
          now = int(datetime.utcnow().timestamp())
          query = 'select distinct operator from aprslog where time > ?'
          cur.execute(query, (now - int(rg)*3600,))
          for station in cur.fetchall():
               res += station
          return({'stations': res})
     except Exception as err:
          return {'errors':'parameter out of range'}
     
def aprs_track_tracks(oper, rg):
     try:
          conn = sqlite3.connect('aprslog.db')
          cur = conn.cursor()
          if not rg:
               rg = 48
          if not oper:
               stns = aprs_track_stations(rg)
          else:
               stns = {'stations': [oper[0:16]] }
               
          res = []
          for op in stns['stations']:
               tracks = {}
               for s in ssid_table:
                    tracks[s] = []
               
               query = 'select time,lat,lng,dist,summit,state from aprslog where operator = ?'
               cur.execute(query, (op,))
               last_seen = 0
               for (t,lat,lng,dist,sm,st) in cur.fetchall():
                    ssid = ssid_table[int(st)//10]
                    tracks[ssid] += [(float(lat),float(lng))]
                    now = int(t)
                    if now > last_seen:
                         last_seen = now
                         distance = dist
                         summit = sm
                         
               for id in tracks.keys():
                    if tracks[id]:
                         t = datetime.fromtimestamp(last_seen)
                         f = Feature(geometry=LineString(tracks[id]),
                                     properties={'callsign':op,
                                                 'ssid':id,
                                                 'lastseen':t.isoformat(),
                                                 'distance':distance,
                                                 'summit':summit,
                                     })
                         res += (f,)
          return({'tracks': res})
     except Exception as err:
          return {'errors':'parameter out of range'}

