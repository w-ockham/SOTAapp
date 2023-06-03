import csv
from datetime import datetime, timezone
import io
import os
import time
import toml
import uuid
import sqlite3


class JAFFPOTASearch:
    def __init__(self, **args):
        self.basedir = args.get('basedir', '.')
        self.conn = None

        with open(self.basedir + '/search_config.toml') as f:
            config = toml.load(f)

        self.config = config['JAFFPOTA']

        self.conn = sqlite3.connect(
            self.config['dbdir'] + self.config['database'],
            isolation_level='IMMEDIATE',timeout=3000)

        cur = self.conn.cursor()
        q = 'create table if not exists potauser(uuid text,time int, primary key(uuid))'
        cur.execute(q)
        q = 'create index if not exists potauser_idx on potauser(uuid, time)'
        cur.execute(q)
        q = 'create table if not exists potalog(uuid text,ref text,type int,hasc txt,date text,qso int, attempt int,activate int)'
        cur.execute(q)
        q = 'create index if not exists potalog_idx on potalog(uuid, ref, type)'
        cur.execute(q)
        self.conn.commit()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def drop_database(self):
        cur = self.conn.cursor()
        q = 'drop table potauser'
        cur.execute(q)
        q = 'drop table potalog'
        cur.execute(q)
        self.conn.commit()

    def check_uuid(self, id):
        cur = self.conn.cursor()
        now = int(datetime.utcnow().timestamp())
        d = datetime.fromtimestamp(now).strftime('%Y-%m-%d')

        time = now - int(self.config['expire']*3600*24)
        q = 'select uuid from potauser where time < ?'
        cur.execute(q, (time,))
        for (e,) in cur.fetchall():
            q2 = 'delete from potalog where uuid = ?'
            cur.execute(q2, (e,))

        q = 'delete from potauser where time < ?'
        cur.execute(q, (time,))

        q = 'select time from potauser where uuid = ?'
        cur.execute(q, (str(id),))
        r = cur.fetchall()

        if len(r) == 0:
            res = {'errors': 'No such LogID'}
        else:
            time = r[0][0]
            create_d = datetime.fromtimestamp(time).strftime('%Y-%m-%d')
            time_e = time + int(self.config['expire']*3600*24)
            expire_d = datetime.fromtimestamp(time_e).strftime('%Y-%m-%d')
            res = {'errors': 'OK', 'uuid': id,
                   'create': create_d, 'expire': expire_d}
        self.conn.commit()
        return res

    def delete_uuid(self, id):
        cur = self.conn.cursor()
        q = 'select time from potauser where uuid = ?'
        cur.execute(q, (id,))
        r = cur.fetchall()

        if len(r) == 0:
            res = {'errors': 'No such uuid', 'uuid': id}
        else:
            q = 'delete from potalog where uuid = ?'
            cur.execute(q, (id,))
            q = 'delete from potauser where uuid = ?'
            cur.execute(q, (id,))
            res = {'errors': 'OK', 'uuid': id}

        self.conn.commit()
        return res

    def update_uuid(self, id):
        cur = self.conn.cursor()

        now = int(datetime.utcnow().timestamp())
        d = datetime.fromtimestamp(now).strftime('%Y-%m-%d')
        q = 'select time from potauser where uuid = ?'
        cur.execute(q, (id,))
        r = cur.fetchall()

        if len(r) == 0:
            id = str(uuid.uuid4())
            q = 'insert into potauser(uuid, time) values(?, ?)'
            cur.execute(q, (id, now,))
        else:
            q = 'delete from potalog where uuid = ?'
            cur.execute(q, (id,))
            q = 'update potauser set time = ? where uuid = ?'
            cur.execute(q, (now, id,))

        self.conn.commit()
        return (id, d)

    def upload_log(self, actid, huntid, fd):
        with io.TextIOWrapper(fd, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            activation_log = 0
            cur = self.conn.cursor()
            lc = 0
            
            for row in reader:
                if lc == 0:
                    if len(row) == 9:
                        activation_log = 1
                        logtype = 'ACT'
                        (id, d) = self.update_uuid(actid)
                    
                    elif len(row) == 7:
                        activation_log = 0
                        logtype = 'HUNT'
                        (id, d) = self.update_uuid(huntid)
                        
                    else:
                        return {'errors': 'CSV Format Error'}

                    if row[2] != 'HASC':
                        return {'errors': 'CSV Format Error'}
                    lc += 1
                else:
                    q = 'insert into potalog(uuid, ref, type, hasc, date, qso, attempt, activate) values(?, ?, ?, ?, ?, ?, ?, ?)'
                    ref = row[3]
                    logty = activation_log
                    hasc = row[2]
                    date = row[5]

                    if activation_log == 1:
                        attempt = int(row[6])
                        activate = int(row[7])
                        qso = int(row[8])
                    else:
                        attempt = 0
                        activate = 0
                        qso = int(row[6])

                    cur.execute(q, (id, ref, logty, hasc,
                                    date, qso, attempt, activate,))
                    lc += 1

            self.conn.commit()
            return {'errors': 'OK', 'uuid': id, 'date': d, 'logtype': logtype, 'entry': lc}

    def searchParkLoc(self, selat, nwlat, nwlng, selng, **args):
        cur = self.conn.cursor()

        level = args.get('parkarea', 0)
        uuid = args.get('logid', None)

        res = []

        if uuid:
            query = 'select * from jaffpota left outer join potalog on jaffpota.pota = potalog.ref and potalog.uuid = ? where (jaffpota.lat > ?) and (jaffpota.lat < ?) and (jaffpota.lng > ?) and (jaffpota.lng < ?) and (jaffpota.level >= ?)'
            cur.execute(query, (uuid, selat, nwlat, nwlng, selng, level))
            for r in cur.fetchall():
                (pota, jaff, name, loc, locid, ty, lv, name_k, lat,
                 lng, _, _, _, loc2, first, qsos, attempt, actcount) = r
                res.append({
                    'pota': pota,
                    'jaff': jaff,
                    'name': name,
                    'location': loc,
                    'locid': locid.split(','),
                    'type': ty,
                    'lv': lv,
                    'name_k': name_k,
                    'lat': lat,
                    'lon': lng,
                    'date': first,
                    'QSOs': qsos,
                    'attempt': attempt,
                    'activate': actcount,
                })
        else:
            query = 'select * from jaffpota where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?) and (level >= ?)'
            cur.execute(query, (selat, nwlat, nwlng, selng, level))
            for r in cur.fetchall():
                (pota, jaff, name, loc, locid, ty, lv, name_k, lat, lng) = r
                res.append({
                    'pota': pota,
                    'jaff': jaff,
                    'name': name,
                    'location': loc,
                    'locid': locid.split(','),
                    'type': ty,
                    'lv': lv,
                    'name_k': name_k,
                    'lat': lat,
                    'lon': lng
                })

        return res

    def searchParkId(self, parkid, isName=False, logid=None):
        cur = self.conn.cursor()
        cur2 = self.conn.cursor()

        parkid = '%'+parkid+'%'
        if isName:
            query = 'select * from jaffpota where namek like ?'
            cur.execute(query, (parkid,))
        else:
            query = 'select * from jaffpota where pota like ? or jaff like ?'
            cur.execute(query, (parkid, parkid,))
        res = []
        for r in cur.fetchall():
            (pota, jaff, name, loc, locid, ty, lv, name_k, lat, lng) = r
            code = None
            if pota:
                code = pota
            if code and jaff:
                code += '/' + jaff
            elif jaff:
                code = jaff

            if logid:
                query = 'select * from potalog where uuid = ? and ref = ?'
                cur2.execute(query, (logid, pota,))
                first = ''
                qsos = 0
                attempt = 0
                actcount = 0
                for e in cur2.fetchall():
                    (_, _, ty, _, first, qsos, attempt, actcount) = e
                res.append({
                    'code': code,
                    'pota': pota,
                    'jaff': jaff,
                    'name': name,
                    'location': loc,
                    'locid': locid.split(','),
                    'type': ty,
                    'lv': lv,
                    'name_k': name_k,
                    'lat': lat,
                    'lon': lng,
                    'date': first,
                    'QSOs': qsos,
                    'attempt': attempt,
                    'activate': actcount,
                })
            else:
                res.append({
                    'code': code,
                    'pota': pota,
                    'jaff': jaff,
                    'name': name,
                    'location': loc,
                    'locid': locid.split(','),
                    'type': ty,
                    'lv': lv,
                    'name_k': name_k,
                    'lat': lat,
                    'lon': lng,
                })
        return res

    def jaffpota_parks(self, options):
        parkid = options.get('parkid', None)
        lat = options.get('lat', 45)
        lon = options.get('lon', 120)
        lat2 = options.get('lat2', 30)
        lon2 = options.get('lon2', 150)
        parkarea = options.get('parkarea', 0)
        logid = options.get('logid', None)

        if not parkid:
            nwlat, nwlng = float(lat), float(lon)
            selat, selng = float(lat2), float(lon2)
            res = self.searchParkLoc(selat, nwlat, nwlng, selng,
                                     parkarea=parkarea, logid=logid)
        else:
            res = self.searchParkId(parkid.upper(), logid=logid)

        return {'errors': 'OK', 'parks': res}


if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    potalog = JAFFPOTASearch(basedir=basedir)
    potalog.drop_database()

    potalog = JAFFPOTASearch(basedir=basedir)

    with open(basedir + '/activator_parks.csv') as f:
        res1 = potalog.upload_log(None, f)
    print(res1)

    with open(basedir + '/activator_parks.csv') as f:
        res2 = potalog.upload_log(res1['uuid'], f)
    print(res2)

    with open(basedir + '/hunter_parks.csv') as f:
        res3 = potalog.upload_log(None, f)
    print(res3)

    t_start = time.perf_counter()
    res = potalog.jaffpota_parks(
        {
            'lat': '40.0',
            'lat2': '30.0',
            'lon': '120.0',
            'lon2': '150.0',
            'logid': res1['uuid'],
            'parkarea': 0
        })
    t_end = time.perf_counter()
    print(t_end - t_start)
    print(len(res))
    for e in res['parks']:
        if e['pota'] == 'JA-0014':
            print(e)

    t_start = time.perf_counter()
    res = potalog.searchParkLoc('30.0', '40.0', '120.0', '150.0',
                                logid=res3['uuid'],
                                parkarea=0)
    t_end = time.perf_counter()
    print(t_end - t_start)
    print(len(res))
    for e in res:
        if e['pota'] == 'JA-0014':
            print(e)

    t_start = time.perf_counter()
    res = potalog.searchParkLoc('30.0', '40.0', '120.0', '150.0',
                                parkarea=0)
    t_end = time.perf_counter()
    print(t_end - t_start)
    print(len(res))
    for e in res:
        if e['pota'] == 'JA-0014':
            print(e)

    print(potalog.searchParkId('JA-0014', logid=res2['uuid']))
    print(potalog.searchParkId('JA-0014', logid=res3['uuid']))
