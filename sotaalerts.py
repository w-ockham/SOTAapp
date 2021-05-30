from datetime import datetime, timezone
from operator import itemgetter

import sqlite3
import time


def make_response(now, slist, continent, isspot):
    res = []
    if continent:
        conn = sqlite3.connect('database/association.db')
        cur = conn.cursor()
        continent = list(map(lambda x: x.upper(), continent))
    for r in slist:
        if not r:
            return res
        else:
            if isspot:
                (time, stn, call, sm, sm_info, lat, lng, freq, mode, cmmt, p) = r
                t = datetime.fromtimestamp(int(time))
                if continent:
                    q = 'select association,continent from associations where code = ?'
                    cur.execute(q, (sm,))
                    r = cur.fetchone()
                    if r:
                        (assc, ct) = r
                        if ct in continent:
                            res.append({
                                'timeStamp': t.isoformat(),
                                'unixtime': int(time),
                                'elapsedtime': now - int(time),
                                'activatorCallsign': call,
                                'station': stn,
                                'summitCode': sm,
                                'summitDetails': sm_info,
                                'association': assc,
                                'continent': ct,
                                'lat': float(lat),
                                'lon': float(lng),
                                'frequency': freq,
                                'mode': mode,
                                'comments': cmmt,
                                'poster': p
                            })
                else:
                    res.append({
                        'timeStamp': t.isoformat(),
                        'unixtime': int(time),
                        'elapsedtime': now - int(time),
                        'activatorCallsign': call,
                        'station': stn,
                        'summitCode': sm,
                        'summitDetails': sm_info,
                        'lat': float(lat),
                        'lon': float(lng),
                        'frequency': freq,
                        'mode': mode,
                        'comments': cmmt,
                        'poster': p
                    })

            else:
                (time, stn, call, sm, sm_info, lat, lng, freq, cmmt, p) = r
                t = datetime.fromtimestamp(int(time))
                if continent:
                    q = 'select association,continent from associations where code = ?'
                    cur.execute(q, (sm,))
                    r = cur.fetchone()
                    if r:
                        (assc, ct) = r
                        if ct in continent:
                            res.append({
                                'dateActivated': t.isoformat(),
                                'unixtime': int(time),
                                'activatingCallsign': call,
                                'station': stn,
                                'summitCode': sm,
                                'summitDetails': sm_info,
                                'association': assc,
                                'continent': ct,
                                'lat': float(lat),
                                'lon': float(lng),
                                'frequency': freq,
                                'comments': cmmt,
                                'poster': p
                            })
                else:
                    res.append({
                        'dateActivated': t.isoformat(),
                        'unixtime': int(time),
                        'activatingCallsign': call,
                        'station': stn,
                        'summitCode': sm,
                        'summitDetails': sm_info,
                        'lat': float(lat),
                        'lon': float(lng),
                        'frequency': freq,
                        'comments': cmmt,
                        'poster': p
                    })

    if continent:
        conn.close()
    return res


def sotaalerts(code_prefix, continent=[], fm='4', to='16'):

    conn = sqlite3.connect('database/alert.db')
    cur = conn.cursor()

    if not fm:
        fm = '4'

    if not to:
        to = '16'

    now = int(datetime.utcnow().timestamp())

    try:
        if code_prefix:
            code_prefix = code_prefix[0:3]
            query = 'select time, operator, callsign, summit, summit_info, lat_dest, lng_dest,alert_freq,alert_comment, poster  from alerts where time >= ? and time < ?and summit like ?'
            cur.execute(
                query,
                (now -
                 int(fm) *
                    3600,
                    now +
                    int(to) *
                    3600,
                    code_prefix +
                    '%',
                 ))
        else:
            query = 'select time, operator, callsign, summit, summit_info, lat_dest, lng_dest,alert_freq,alert_comment, poster  from alerts where time >= ? and time < ?'
            cur.execute(query, (now - int(fm) * 3600, now + int(to) * 3600, ))
        r = cur.fetchall()
        res = make_response(now, r, continent, False)
        conn.close()
        if res:
            return {'errors': 'OK', 'alerts': res}
        else:
            return {'errors': 'No alerts.'}
    except Exception as err:
        print(err)
        conn.close()
        return {'errors': 'parameter out of range'}


def sotaspots(code_prefix, mode, continent=[], r=None):

    conn = sqlite3.connect('database/alert.db')
    cur = conn.cursor()

    if not r:
        rng = 16
    else:
        rng = int(r)
        if rng > 48:
            rng = 48

    now = int(datetime.utcnow().timestamp())

    try:
        if code_prefix:
            code_prefix = code_prefix[0:3]
            if mode is None:
                query = 'select time, operator, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ? and summit like ?'
                cur.execute(
                    query, (now - int(rng) * 3600, code_prefix + '%', ))
            else:
                query = 'select time, operator, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ? and summit like ? and UPPER(spot_mode) = UPPER(?)'
                cur.execute(
                    query, (now - int(rng) * 3600, code_prefix + '%', mode, ))
        else:
            if mode is None:
                query = 'select time, operator, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ?'
                cur.execute(query, (now - int(rng) * 3600, ))
            else:
                query = 'select time, operator, callsign, summit, summit_info, lat, lng, spot_freq, spot_mode, spot_comment, poster from spots where time > ? and UPPER(spot_mode) = UPPER(?)'
                cur.execute(query, (now - int(rng) * 3600, mode, ))

        r = cur.fetchall()
        res = make_response(now, r, continent, True)
        conn.close()
        if res:
            return {'errors': 'OK', 'spots': res}
        else:
            return {'errors': 'No spots.'}

    except Exception as err:
        conn.close()
        return {'errors': 'parameter out of range'}


def sotaalerts_and_spots(code_prefix, continent, mode, fm, to):
    al = sotaalerts(code_prefix, continent, fm, to).get('alerts', [])
    spt = sotaspots(code_prefix, mode, continent, fm).get('spots', [])

    alerts = dict(list(
        map(lambda x: ((x['station'], x['summitCode']),
                       {'time': x['unixtime'], 'info': x}), al)))
    spots = dict(list(
        map(lambda x: ((x['station'], x['summitCode']),
                       {'time': x['unixtime'], 'info': x}), spt)))

    keys = set(list(alerts.keys()) + list(spots.keys()))

    res = []
    for k in keys:
        t = ''
        (op, sm) = k
        a = alerts.get(k, None)

        if a:
            t = a['time']
            al = a['info']
        else:
            al = None

        s = spots.get(k, None)
        if s:
            if t == '':
                t = s['time']
            st = s['info']
        else:
            st = None
        res.append({'station': op, 'summit': sm, 'unixtime': t,
                    'alerts': al, 'spots': st})

    return {'errors': 'OK',
            'alerts_spots': sorted(res, key=itemgetter('unixtime'))}


if __name__ == "__main__":
    #    print(sotaalerts('W',[],'24'))
    #    print(sotaspots(None ,None))
    #    print(sotaalerts('DM',['EU'],None))
    #    print(sotaalerts(None,['NA','EU'],None))
    #    print(sotaspots(None, None, ['NA','EU']))
    print(sotaalerts_and_spots(None, [], None, '4', '16'))
