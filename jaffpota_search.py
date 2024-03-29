import csv
from datetime import datetime, timezone
import io
import json
import os
import pyproj
import time
import toml
import uuid
import secrets
import sqlite3
from spottimeline import spottimeline


class JAFFPOTASearch:
    def __init__(self, **args):
        self.basedir = args.get('basedir', '.')
        self.conn = None

        with open(self.basedir + '/search_config.toml') as f:
            config = toml.load(f)

        self.config = config['JAFFPOTA']

        self.grs80 = pyproj.Geod(ellps='GRS80')
        
        self.conn = sqlite3.connect(
            self.config['dbdir'] + self.config['database'],
            isolation_level='IMMEDIATE', timeout=3000)

        cur = self.conn.cursor()
        q = 'create table if not exists potauser(uuid text,time int, primary key(uuid))'
        cur.execute(q)
        q = 'create index if not exists potauser_idx on potauser(uuid, time)'
        cur.execute(q)
        q = 'create table if not exists mqttuser(uuid text,time int, primary key(uuid))'
        cur.execute(q)
        q = 'create index if not exists mqttuser_idx on mqttuser(uuid, time)'
        cur.execute(q)
        q = 'create table if not exists potalog(uuid text,ref text,type int,hasc txt,date text,qso int, attempt int,activate int)'
        cur.execute(q)
        q = 'create index if not exists potalog_idx on potalog(uuid, ref, type)'
        cur.execute(q)
        q = 'create table if not exists potashare(key int,time int,uuid_act text, uuid_hunt text)'
        cur.execute(q)
        self.conn.commit()

    def toOldRef(ref):
        return ref.replace('JP-','JA-')

    def toNewRef(ref):
        return ref.replace('JA-','JP-')
    
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

    def check_uuid(self, id, enable_mqtt):
        cur = self.conn.cursor()
        now = int(datetime.utcnow().timestamp())
        d = datetime.fromtimestamp(now).strftime('%Y-%m-%d')

        time = now - int(self.config['expire_log']*3600*24)
        q = 'select uuid from potauser where time < ?'
        cur.execute(q, (time,))
        for (e,) in cur.fetchall():
            q2 = 'delete from potalog where uuid = ?'
            cur.execute(q2, (e,))

        q = 'delete from potauser where time < ?'
        cur.execute(q, (time,))

        q = 'delete from mqttuser where time < ?'
        cur.execute(q, (time,))

        q = 'select time from potauser where uuid = ?'
        cur.execute(q, (str(id),))
        r = cur.fetchall()

        if len(r) == 0:
            res = {'errors': 'No such LogID'}
        else:
            time = r[0][0]
            create_d = datetime.fromtimestamp(time).strftime('%Y-%m-%d')
            time_e = time + int(self.config['expire_log']*3600*24)
            expire_d = datetime.fromtimestamp(time_e).strftime('%Y-%m-%d')
            res = {'errors': 'OK', 'uuid': id,
                   'create': create_d, 'expire': expire_d}
            if enable_mqtt:
                q = 'insert or replace into mqttuser(uuid, time) values(?, ?)'
                print(cur.execute(q, (str(id), time,)))
            else:
                q = 'delete from mqttuser where uuid = ?'
                cur.execute(q, (str(id),))

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
            q = 'delete from mqttuser where uuid = ?'
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

    def clear_old_key(self, now):
        cur = self.conn.cursor()
        q = 'delete from potashare where time < ?'
        cur.execute(q, (now,))
        self.conn.commit()

    def export_uuid(self, uuid_act, uuid_hunt):
        now = int(datetime.utcnow().timestamp())
        self.clear_old_key(now)

        cur = self.conn.cursor()

        for uuid in [uuid_act, uuid_hunt]:
            if uuid != 'undefined' and uuid != 'null':
                q = 'select count(*) from potauser where uuid =?'
                cur.execute(q, (uuid,))
                r = cur.fetchone()
                if r[0] == 0:
                    return {'errors': 'No such uuid', 'uuid': uuid}
        rc = 0
        while rc < 10:
            sharekey = secrets.randbelow(1000000)
            q = 'select count(*) from potashare where key = ?'
            cur.execute(q, (sharekey,))
            r = cur.fetchone()
            if r[0] == 0:
                break
            rc += 1

        if rc >= 10:
            return {'errors': 'Key conflict error'}

        time_e = now + int(self.config['expire_key'])

        q = 'insert into potashare(key, time, uuid_act, uuid_hunt) values(?, ?, ?, ?)'
        cur.execute(q, (sharekey, time_e, uuid_act, uuid_hunt,))

        self.conn.commit()

        keystr = str(sharekey).zfill(6)
        return {'errors': 'OK', 'sharekey': keystr}

    def import_uuid(self, keystr):

        now = int(datetime.utcnow().timestamp())
        self.clear_old_key(now)

        if not keystr.isdigit():
            return {'errors': 'No such share key'}

        sharekey = int(keystr)
        cur = self.conn.cursor()
        q = 'select * from potashare where key = ?'
        cur.execute(q, (sharekey,))
        r = cur.fetchone()

        if r == None:
            return {'errors': 'No such share key'}
        else:
            (_, _, uuid_act, uuid_hunt) = r
            return {'errors': 'OK', 'uuid_act': uuid_act, 'uuid_hunt': uuid_hunt}

    def search_log(self, logid, refid):
        cur = self.conn.cursor()
        q = 'select * from potalog where uuid = ? and ref = ?'
        cur.execute(q, (logid, refid,))
        r = cur.fetchall()

        if len(r) == 0:
            return {'errors': 'No references were found'}
        else:
            q = 'select locid from jaffpota where pota = ?'
            cur.execute(q, (refid,))
            r = cur.fetchone()
            if r:
                return {'errors': 'OK', 'counts': len(r), 'locid': r[0].split(',')}
            else:
                return {'errors': 'No references were found'}


    def search_logs(self, logid, js):
        cur = self.conn.cursor()
        logs = {}
        for ref in js['refids']:
            q = 'select * from potalog where uuid = ? and ref = ?'
            cur.execute(q, (logid, ref,))
            r = cur.fetchall()

            if len(r) != 0:
                q = 'select locid from jaffpota where pota = ?'
                cur.execute(q, (ref,))
                r = cur.fetchone()
                logs[ref] = r[0].split(',')

        return {'errors': 'OK', 'logs': logs}

    def spots(self, options):
        spots = spottimeline(options)
        logs = {}
        for prog in spots:
            if prog == 'pota' and options['logid'] and not options['bycall']:
                for ref in spots[prog]:
                    locid = self.search_log(options['logid'], ref)
                    if 'locid' in locid:
                        logs[ref] = locid['locid']

        return {'errors': 'OK', 'spots': spots, 'logs': logs}

    def stat_db(self):
        cur = self.conn.cursor()
        cur2 = self.conn.cursor()

        now = int(datetime.utcnow().timestamp())
        expire_before = now - int(self.config['expire_log']*3600*24)

        q = 'select count(*) from potauser'
        cur.execute(q)
        user = cur.fetchone()

        q = 'select count(*) from potauser where time < ?'
        cur.execute(q, (expire_before,))
        expire = cur.fetchone()

        q = 'select count(*) from potalog'
        cur.execute(q)
        log = cur.fetchone()

        q = 'select * from potauser'
        cur.execute(q)

        logerror = 0
        (uuid_l, longest) = (None, 0)

        for (uuid, _) in cur.fetchall():
            q = 'select count(*) from potalog where uuid = ?'
            cur2.execute(q, (uuid,))
            r = cur2.fetchone()
            if r[0] == 0:
                logerror += 1
            else:
                if r[0] > longest:
                    uuid_l = uuid
                    longest = r[0]

        start = time.perf_counter()
        res = self.jaffpota_parks(
            {
                'lat': '46.0',
                'lat2': '20.0',
                'lon': '120.0',
                'lon2': '150.0',
                'parkarea': 0
            })
        end = time.perf_counter()
        t1 = end - start

        start = time.perf_counter()
        res = self.jaffpota_parks(
            {
                'lat': '46.0',
                'lat2': '20.0',
                'lon': '120.0',
                'lon2': '150.0',
                'logid': uuid_l,
                'parkarea': 0
            })
        end = time.perf_counter()

        t2 = end - start
        t1 = round((t2 - t1)*1000, 2)
        t2 = round(t2*1000, 2)

        q = 'select min(time) from potauser'
        cur.execute(q)
        epoch = cur.fetchone()
        hist = []
        hc = 0
        for t in range(now, epoch[0], -3600*24):
            q = 'select uuid from potauser where time <= ?'
            cur.execute(q, (t,))
            lc = 0
            uc = 0
            for (uuid,) in cur.fetchall():
                q = 'select count(*) from potalog where uuid = ?'
                cur.execute(q, (str(uuid),))
                l = cur.fetchone()
                lc = lc + l[0]
                uc += 1
            tstr = datetime.fromtimestamp(t).isoformat() + 'Z'
            hist.append({'time': tstr, 'users': uc, 'logs': lc})
            hc += 1
            if hc >= 14:
                break
        if __name__ == "__main__":
            return {'errors': 'OK', 'log_uploaded': user[0], 'log_entries': log[0], 'log_expired': expire[0], 'log_error': logerror, 'longest_uuid': uuid_l, 'longest_entry': longest, 'query_elapsed_ms': t2, 'query_perf_degrade_ms': t1, 'log_history': hist}
        else:
            return {'errors': 'OK', 'log_uploaded': user[0], 'log_entries': log[0], 'log_expired': expire[0], 'log_error': logerror, 'longest_entry': longest, 'query_elapsed_ms': t2, 'query_perf_degrade_ms': t1, 'log_history': hist}

    def upload_log(self, actid, huntid, fd):
        with io.TextIOWrapper(fd, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            activation_log = 0
            cur = self.conn.cursor()
            lc = 0

            try:
                for row in reader:
                    if lc == 0:
                        if row[2] != 'HASC':
                            raise Exception
                        rlen = len(row)
                        if not (rlen in [7, 9]):
                            raise Exception

                        if rlen == 9:
                            activation_log = 1
                            logtype = 'ACT'
                            (id, d) = self.update_uuid(actid)

                        elif rlen == 7:
                            activation_log = 0
                            logtype = 'HUNT'
                            (id, d) = self.update_uuid(huntid)

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
                if lc == 0:
                    raise Exception
            except Exception as e:
                return {'errors': 'CSV Format Error'}

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

        try:
            if not parkid:
                lat, lon = float(lat), float(lon)
                if options.get('srange', None):
                    rng = int(options['srange'])
                    nwlng, nwlat, _ = self.grs80.fwd(lon, lat, -45.0, rng)
                    selng, selat, _ = self.grs80.fwd(lon, lat, 135.0, rng)
                else:
                    nwlat, nwlng = lat, lon
                    selat, selng = float(lat2), float(lon2)
                    
                res = self.searchParkLoc(selat, nwlat, nwlng, selng,
                                         parkarea=parkarea, logid=logid)
            else:
                res = self.searchParkId(parkid.upper(), logid=logid)

            return {'errors': 'OK', 'parks': res}
        
        except Exception as err:
            print('Error:')
            print(err)
            return {'errors': 'parameter out of range'}

    def command(self, req):
        command = req.args.get('command', '').upper()

        if command == 'CHECK':
            logid = req.args.get('logid', None)
            enable_mqtt = req.args.get('mqtt', None)
            return self.check_uuid(logid, enable_mqtt)

        elif command == 'DELETE':
            logid = req.args.get('logid', None)
            return self.delete_uuid(logid)

        elif command == 'UPLOAD':
            logid_act = req.args.get('logid_act', None)
            logid_hunt = req.args.get('logid_hunt', None)
            file = req.files['uploadfile']
            return self.upload_log(logid_act, logid_hunt, file)

        elif command == 'EXPORT':
            logid_act = req.args.get('logid_act', None)
            logid_hunt = req.args.get('logid_hunt', None)
            return self.export_uuid(logid_act, logid_hunt)

        elif command == 'IMPORT':
            sharekey = req.args.get('sharekey', None)
            return self.import_uuid(sharekey)

        elif command == 'SEARCH':
            logid = req.args.get('logid', None)
            refid = req.args.get('refid', None)
            return self.search_log(logid, refid)

        elif command == 'LOGSEARCH':
            logid = req.args.get('logid', None)
            return self.search_logs(logid, req.json)

        elif command == 'SPOTS':
            options = {
                'program': req.args.get('program', None),
                'period': req.args.get('period', None),
                'region': req.args.get('region', None),
                'bycall': req.args.get('bycall', 0),
                'logid': req.args.get('logid', None)
            }
            return self.spots(options)

        elif command == 'STAT':
            return self.stat_db()

        return {'errors': 'Unknown command: ' + command}


if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    potalog = JAFFPOTASearch(basedir=basedir)

    t_start = time.perf_counter()
    res = potalog.jaffpota_parks(
        {
            'lat': '40.0',
            'lat2': '30.0',
            'lon': '120.0',
            'lon2': '150.0',
            'parkarea': 0
        })
    t_end = time.perf_counter()
    print(t_end - t_start)
    print(len(res))
    for e in res['parks']:
        if e['pota'] == 'JA-0014':
            print(e)

    stat = potalog.stat_db()
    refids = {'refids': ['JA-0014', 'JA-0024', 'JA-1215', 'JA-2051']}
    print(potalog.search_logs(stat['longest_uuid'], refids))
    options = {'logid': stat['longest_uuid'], 'period': '12',
               'region': 'JA', 'program': None, 'bycall': 0}
    print(json.dumps(potalog.spots(options)))

    nie_hunter = 'dcb8165b-db08-4b35-bf2e-da4a4433dcf3'
    print(potalog.check_uuid(nie_hunter, 0))
    print(potalog.check_uuid(stat['longest_uuid'], True))
