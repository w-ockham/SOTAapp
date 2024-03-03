from datetime import datetime, timezone, timedelta
from geojson import LineString, Feature, FeatureCollection
import json
import sqlite3

ssid_table = ['7', '9', '6', '5', '8']


def aprs_track_stations(rg, region=None):
    try:
        conn = sqlite3.connect('database/aprslog2.db')
        cur = conn.cursor()
        res = []
        if not rg:
            rg = 24
        now = int(datetime.utcnow().timestamp())
        if not region:
            query = 'select distinct operator from aprslog where time > ?'
            cur.execute(query, (now - int(rg) * 3600,))
        else:
            query = 'select distinct operator from aprslog where time > ? and summit like ?'
            cur.execute(query, (now - int(rg) * 3600, region + '%',))

        for station in cur.fetchall():
            res += station
        return ({'stations': res})
    except Exception as err:
        return {'errors': 'parameter out of range'}


def aprs_track_tracks(oper, rg, region = None):
    try:
        conn = sqlite3.connect('database/aprslog2.db')
        conn2 = sqlite3.connect('database/alert2.db')
        cur = conn.cursor()
        cur2 = conn2.cursor()
        
        if not rg:
            rg = '24'

        spot_window = 8
        
        if not oper:
            stns = aprs_track_stations(rg, region)
        else:
            stns = {'stations': [oper[0:16]]}

        res = []

        now = int(datetime.utcnow().timestamp())
        
        for op in stns['stations']:
            tracks = {}
            last_seen = {}
            distance = {}
            summit = {}
            query = 'select time, summit, spot_freq, spot_mode, spot_comment from spots where operator = ? and time > ?'
            cur2.execute(query, (op, now - spot_window * 3600))
            spot = cur2.fetchone()
            if spot:
                (utctime, spot_summit, spot_freq, spot_mode, spot_comment) = spot
                JST = timezone(timedelta(hours=+9), 'JST')
                dt = datetime.fromtimestamp(utctime).replace(tzinfo=timezone.utc).astimezone(tz=JST)
                spot_time = dt.isoformat()
            else:
                (spot_time, spot_summit, spot_freq, spot_mode, spot_comment) = (None, None, None, None, None)
                
            for s in ssid_table:
                tracks[s] = []
                last_seen[s] = 0
                distance[s] = 0
                summit[s] = ""

            query = 'select time,lat,lng,dist,summit,state from aprslog where operator = ? and time > ?'
            cur.execute(query, (op, now - int(rg) * 3600))
            for (t, lat, lng, dist, sm, st) in cur.fetchall():
                ssid = ssid_table[int(st) // 10]
                tracks[ssid] += [(float(lat), float(lng))]
                last = int(t)
                if last > last_seen[ssid]:
                    last_seen[ssid] = last
                    distance[ssid] = dist
                    summit[ssid] = sm

            for id in tracks.keys():
                if tracks[id]:
                    t = datetime.fromtimestamp(last_seen[id])
                    f = Feature(geometry=LineString(tracks[id]),
                                properties={'callsign': op,
                                            'ssid': id,
                                            'lastseen': t.isoformat()+'Z',
                                            'distance': distance[id],
                                            'summit': summit[id],
                                            'spot_summit': spot_summit,
                                            'spot_time': spot_time,
                                            'spot_freq': spot_freq,
                                            'spot_mode': spot_mode,
                                            'spot_comment': spot_comment,
                                            })
                    res += (f,)

        cur.close()
        cur2.close()
        conn.close()
        conn2.close()
        
        return({'tracks': res})
    except Exception as err:
        return {'errors': f'parameter out of range {err}'}
