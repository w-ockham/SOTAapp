from datetime import datetime, timezone
import sqlite3
import time

def make_response(slist,spotp):
    res = []
    for r in slist:
        if not r:
            return res
        else:
            if spotp:
                (time, call, sm, sm_info, lat, lng, freq, mode,  cmmt,p ) = r
                t = datetime.fromtimestamp(int(time))
                res.append({
                    'timeStamp': t.isoformat(),
                    'activatorCallsign': call,
                    'summitCode': sm,
                    'summitDetails': sm_info,
                    'lat': float(lat),
                    'lon': float(lng),
                    'frequency':freq,
                    'mode': mode,
                    'comments': cmmt,
                    'poster': p
                })

            else:
                (time, call, sm, sm_info, lat, lng, freq, cmmt,p ) = r
                t = datetime.fromtimestamp(int(time))
                res.append({
                    'dateActivated': t.isoformat(),
                    'activatingCallsign': call,
                    'summitCode': sm,
                    'summitDetails': sm_info,
                    'lat': float(lat),
                    'lon': float(lng),
                    'frequency':freq,
                    'comments': cmmt,
                    'poster': p
                })
    return res

def sotaalerts(code_prefix, r):

    conn = sqlite3.connect('alert.db')
    cur = conn.cursor()

    if not r:
        rng = 16
    else:
        rng = int(r)
        if rng > 16:
            rng = 16
        
    now = int(datetime.utcnow().timestamp())
    
    try:
        if code_prefix :
            code_prefix = code_prefix[0:3]
            query = 'select time, callsign, summit, summit_info, lat_dest, lng_dest,alert_freq,alert_comment, poster  from alerts where time >= ? and time < ?and summit like ?'
            cur.execute(query, (now, now + int(rng)* 3600, code_prefix + '%', ))
        else:
            query = 'select time, callsign, summit, summit_info, lat_dest, lng_dest,alert_freq,alert_comment, poster  from alerts where time >= ? and time < ?'
            cur.execute(query, (now, now + int(rng)* 3600, ))
        r = cur.fetchall()
        res =  make_response(r, False)
        conn.close();
        if res:
            return {'errors': 'OK', 'alerts': res}
        else:
            return {'errors': 'No alerts.'}
    except Exception as err:
        print(err)
        conn.close()
        return {'errors': 'parameter out of range'}

def sotaspots(code_prefix,mode, r):

    conn = sqlite3.connect('alert.db')
    cur = conn.cursor()

    if not r:
        rng = 24
    else:
        rng = int(r)
        if rng > 24:
            rng = 24

    now = int(datetime.utcnow().timestamp())        
    
    try:
        if code_prefix :
            code_prefix = code_prefix[0:3]
            if mode == None:
                query = 'select time, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ? and summit like ?'
                cur.execute(query, (now - int(rng)*3600, code_prefix + '%', ))
            else:
                query = 'select time, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ? and summit like ? and UPPER(spot_mode) = UPPER(?)'
                cur.execute(query, (now - int(rng)*3600, code_prefix + '%', mode, ))
        else:
            if mode == None:
                query = 'select time, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ?'
                cur.execute(query, (now - int(rng)*3600, ))
            else:
                query = 'select time, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ? and UPPER(spot_mode) = UPPER(?)'
                cur.execute(query, (now - int(rng)*3600, mode, ))
            

        r = cur.fetchall()
        res =  make_response(r, True)
        conn.close();
        if res:
            return {'errors': 'OK', 'spots': res}
        else:
            return {'errors': 'No spots.'}

    except Exception as err:
        print(err)
        conn.close()
        return {'errors': 'parameter out of range'}

    
if __name__ == "__main__":
    print(sotaalerts('W','24'))
    print(sotaalerts('JA',None))
    print(sotaspots('JA',None,'24'))
    print(sotaspots('JA','ssb','24'))
    print(sotaspots(None,'ssb','24'))
