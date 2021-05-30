import pyproj
import sqlite3
import maidenhead as mh
from gsi_geocoder import gsi_rev_geocoder

grs80 = pyproj.Geod(ellps='GRS80')

def make_response(worldwide, flag, slist):
    res = []

    if (flag & 0x02) == 2:
        return({'totalCount': len(slist)})

    gsifl = (flag & 0x01) == 1
    
    for r in slist:
        if not r:
            return res
        else:
            if worldwide:
                (summit_id, lat, lng, pts, elev, name, desc) = r
                gl = mh.to_maiden(float(lat), float(lng),precision=4)
                res.append({
                    'code': summit_id,
                    'lat': lat,
                    'lon': lng,
                    'maidenhead:':gl,
                    'pts': pts,
                    'elev': elev,
                    'name': name,
                    'desc': desc
                })

            else:
                (summit_id, lat, lng, pts, elev, name, desc, name_k, desc_k) = r
                if (gsifl):
                    gsi = gsi_rev_geocoder(lat, lng, True)
                else:
                    gsi = None
                gl = mh.to_maiden(float(lat), float(lng),precision=4)
                res.append({
                    'code': summit_id,
                    'lat': lat,
                    'lon': lng,
                    'maidenhead':gl,
                    'pts': pts,
                    'elev': elev,
                    'name': name_k,
                    'desc': desc_k,
                    'gsi_info': gsi
                })

    return res


def sotasummit_region(worldwide, options):

    if worldwide:
        conn = sqlite3.connect('database/dx_summits.db')
    else:
        conn = sqlite3.connect('database/ja_summits.db')

    cur = conn.cursor()

    try:
        if not options['flag']:
            gsifl = 1
        else:
            gsifl = int(options['flag'])
            
        code = options['code']
        name = options['name']

        if code:
            if worldwide:
                query = 'select * from summits where code like ?'
            else:
                query = 'select * from summits where code like ?'
            print("exec")
            cur.execute(query, ('%' + code.upper() + '%', ))
            print("done")
            r = cur.fetchall()
            res = make_response(worldwide, gsifl, r)
            conn.close()
            if res:
                return {'errors': 'OK', 'summits': res}
            else:
                return {'errors': 'No such summit.'}
        elif name:
            if worldwide:
                query = 'select * from summits where name like ?'
            else:
                query = 'select * from summits where name_k like ?'
            cur.execute(query, ('%' + name + '%', ))
            r = cur.fetchall()
            res = make_response(worldwide, gsifl, r)
            conn.close()
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
                nwlat, nwlng = lat , lng
                selat, selng = float(options['lat2']), float(options['lon2'])
            else:
                if not options['range']:
                    rng = 10000
                else:
                    rng = int(options['range']) * 1000

                if rng > 30000:
                    rng = 30000
                    
                nwlng, nwlat, _ = grs80.fwd(lng, lat, -45.0, rng)
                selng, selat, _ = grs80.fwd(lng, lat, 135.0, rng)

            if options['elevation']:
                elev = int(options['elevation'])
            else:
                elev = 0
                
            if worldwide:
                query = 'select * from summits where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?) and (alt > ?)'
            else:
                query = 'select * from summits where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?) and (alt > ?)'

            cur.execute(query, (selat, nwlat, nwlng, selng, elev))
            slist = []
            res = make_response(worldwide, gsifl, cur.fetchall())
            conn.close()
            if res:
                return {'errors': 'OK', 'summits': res}
            else:
                return {'errors': 'No summits.'}

    except Exception as err:
        conn.close()
        print(err)
        return {'errors': 'parameter out of range'}


def sotasummit(path, options):
    p = path.upper()
    if p == 'JA':
        return sotasummit_region(False, options)
    elif p == 'WW':
        return sotasummit_region(True, options)
    else:
        ambg = options['ambg']
        if not ambg:
            return {'errors': 'ambg parameter not found'}
        codep = ambg.upper()
        if '/' in codep:
            if codep.startswith('JA'):
                options['code'] = ambg
                return sotasummit_region(False, options)
            else:
                options['code'] = ambg
                return sotasummit_region(True, options)
        else:
            if ambg.encode('utf-8').isalnum():
                options['name'] = ambg
                return sotasummit_region(True, options)
            else:
                options['name'] = ambg
                return sotasummit_region(False, options)
        

if __name__ == "__main__":
    options = {
        'ambg': '仏',
        'code': None,
        'name': None,
        'flag':'0',
        'lat':'35.754976', 'lon':'138.232899',
        #'lat2':'34.754976', 'lon2':'140.232899',
        'lat2':None, 'lon2':'140.232899',
        'elevation':'2300',
        'range':'10'}
    
    print(sotasummit('all', options))
#    print(sotasummit('ww', 'HB/GR-088', None))
#    print(sotasummit('ja', None, None, '35.754976', '138.232899'))
#    print(sotasummit('WW', None, None, '35.754976', '138.232899'))
#    print(sotasummit('ww', None, None, '45.8325', '6.8644', '3'))
#    print(sotasummit('ja', None, '槍'))
#    print(sotasummit('ww', None, 'Gun'))
#    print(sotasummit('ja', options))
