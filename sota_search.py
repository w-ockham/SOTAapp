import maidenhead as mh
import os
import pyproj
import re
import sqlite3
import toml

from gsi_geocoder import gsi_rev_geocoder


class SOTASearch:

    def __init__(self, **args):
        self.basedir = args.get('basedir', '.')
        self.jaffpota = args.get('jaffpota', None)

        self.conn = None
        with open(self.basedir + '/search_config.toml') as f:
            config = toml.load(f)

        self.config = config['SOTA']

        self.conn = sqlite3.connect(
            self.config['dbdir'] + self.config['database'])

        self.grs80 = pyproj.Geod(ellps='GRS80')

    def __del__(self):
        if self.conn:
            self.conn.close()

    def searchSummitId(self, refid, isName=False):
        cur = self.conn.cursor()
        if isName:
            query = f"select * from summits where assoc like 'Japan%' and name_k like ? "
        else:
            query = f"select * from summits where assoc like 'Japan%' and code like ? "
        cur.execute(query, ('%'+refid+'%',))
        res = []
        for r in cur.fetchall():
            (summit, lat, lng, pts, bonus, elev, name, name_k,
             desc, desc_k, _, _, actcnt, lastact, lastcall) = r
            res.append({
                'code': summit,
                'name': name,
                'name_k': name_k,
                'lat': lat,
                'lon': lng
            })

        return res

    def make_response(self, slist, gsiRev=False):
        res = []

        if gsiRev:
            if len(slist) > 10:
                gsiRev = False

        for r in slist:
            if not r:
                return res
            else:
                (summit_id, lat, lng, pts, bonus, elev, name, name_k,
                 desc, desc_k, _, _, actcnt, lastact, lastcall) = r
                if (gsiRev):
                    gsi = gsi_rev_geocoder(lat, lng, True)
                else:
                    gsi = None
                gl = mh.to_maiden(float(lat), float(lng), precision=4)
                res.append({
                    'code': summit_id,
                    'lat': lat,
                    'lon': lng,
                    'maidenhead': gl,
                    'pts': pts,
                    'bonus': bonus,
                    'elev': elev,
                    'name': name,
                    'name_k': name_k,
                    'desc': desc_k,
                    'actcnt': actcnt,
                    'lastact': lastact,
                    'lastcall': lastcall,
                    'gsi_info': gsi
                })

        return res

    def sotasummit_region(self, options, isWW=True):

        cur = self.conn.cursor()

        try:
            code = options.get('code', None)
            name = options.get('name', None)
            gsiRev = options.get('revgeo', None)

            if code:
                query = 'select * from summits where code like ?'
                cur.execute(query, ('%' + code.upper() + '%', ))
                r = cur.fetchall()
                res = self.make_response(r, gsiRev=gsiRev)
                if res:
                    return {'errors': 'OK', 'summits': res}
                else:
                    return {'errors': 'No such summit.'}
            elif name:
                if isWW:
                    query = 'select * from summits where name like ?'
                else:
                    query = 'select * from summits where name_k like ?'
                m = re.match(r'"(.+)"', name)
                if m:
                    arg = m.group(1)
                else:
                    arg = '%' + name + '%'
                cur.execute(query, (arg, ))
                r = cur.fetchall()
                res = self.make_response(r, gsiRev=gsiRev)
                if res:
                    return {'errors': 'OK', 'summits': res}
                else:
                    return {'errors': 'No such summit.'}
            else:
                if not options['lat'] or not options['lon']:
                    raise Exception
                else:
                    lat, lng = float(options['lat']), float(options['lon'])

                if options['lat2'] and options['lon2']:
                    nwlat, nwlng = lat, lng
                    selat, selng = float(
                        options['lat2']), float(options['lon2'])
                else:
                    if not options['range']:
                        if not options['srange']:
                            rng = 10000
                        else:
                            rng = int(options['srange'])
                    else:
                        rng = int(options['range']) * 1000
                        if rng > 30000:
                            rng = 30000
                    nwlng, nwlat, _ = self.grs80.fwd(lng, lat, -45.0, rng)
                    selng, selat, _ = self.grs80.fwd(lng, lat, 135.0, rng)

                if options['elevation']:
                    elev = int(options['elevation'])
                else:
                    elev = 0

                query = 'select * from summits where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?) and (alt > ?)'
                cur.execute(query, (selat, nwlat, nwlng, selng, elev))
                res = self.make_response(cur.fetchall(), gsiRev=gsiRev)
                if res:
                    return {'errors': 'OK', 'summits': res}
                else:
                    return {'errors': 'No summits.'}

        except Exception as err:
            print('Error:')
            print(err)
            return {'errors': 'parameter out of range'}

    def sotasummit(self, path, options):
        p = path.upper()
        if p == 'JA':
            return self.sotasummit_region(options, isWW=False)
        elif p == 'WW':
            return self.sotasummit_region(options)
        else:
            ambg = options['ambg']
            if not ambg:
                return {'errors': 'ambg parameter not found'}
            codep = ambg.upper()
            if '/' in codep or '-' in codep:
                if codep.startswith('JA'):
                    options['code'] = ambg
                    return sotasummit_region(False, options)
                else:
                    options['code'] = ambg
                    return sotasummit_region(True, options)
            else:
                s = ambg.replace('"', '')
                if s.encode('utf-8').isalnum():
                    options['name'] = ambg
                    return sotasummit_region(True, options)
                else:
                    options['name'] = ambg
                    return sotasummit_region(False, options)


if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    sota = SOTASearch(basedir=basedir)

    options = {
        'code': None,
        'name': None,
        'flag': '0',
        'lat2': None,
        'lat': '35.918529',
        'lon': '138.522105',
        'lon2': None,
        'revgeo': True,
        'elevation': None,
        'range': None,
        'srange': '300',
    }

    res = sota.sotasummit('ww', options)
    print(res)

    options = {
        'code': None,
        'name': None,
        'elevation': None,
        'reverse': '0',
        'lat': '35.754976', 'lon': '138.232899',
        'lat2': '34.754976', 'lon2': '139.232899',
    }

    res = sota.sotasummit('ja', options)
    print(res)
