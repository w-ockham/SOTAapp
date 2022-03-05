import pyproj
import sqlite3
import maidenhead as mh
import re
from gsi_geocoder import gsi_rev_geocoder

grs80 = pyproj.Geod(ellps='GRS80')


def searchParkLoc(selat, nwlat, nwlng, selng, level):
    conn = sqlite3.connect('database/jaffpota.db')
    cur = conn.cursor()
    query = 'select * from jaffpota where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?) and (level >= ?)'
    cur.execute(query, (selat, nwlat, nwlng, selng, level))
    res = []
    for r in cur.fetchall():
        (pota, jaff, name, loc, locid, ty, lv, name_k, lat ,lng) = r
        res.append({
            'pota': pota,
            'jaff': jaff,
            'name': name,
            'location': loc,
            'locid':locid.split(','),
            'type': ty,
            'lv':lv,
            'name_k':name_k,
            'lat': lat,
            'lon': lng
            })
    return res

def searchParkId(parkid,isName = False):
    conn = sqlite3.connect('database/jaffpota.db')
    cur = conn.cursor()
    if isName:
        query = f"select * from jaffpota where namek like '%{parkid}%'"
    else:
        query = f"select * from jaffpota where pota like '%{parkid}%' or jaff like '%{parkid}%'"
    cur.execute(query)
    res = []
    for r in cur.fetchall():
        (pota, jaff, name, loc, locid, ty, lv, name_k, lat ,lng) = r
        code = None
        if pota != '':
            code = pota
        if code and jaff != '':
            code += '/' + jaff
        elif jaff != '':
            code = jaff
        res.append({
            'code': code,
            'pota': pota,
            'jaff': jaff,
            'name': name,
            'location': loc,
            'locid':locid.split(','),
            'type': ty,
            'lv':lv,
            'name_k':name_k,
            'lat': lat,
            'lon': lng
            })
    conn.close()
    return res

def jaffpota_parks(options):
    parkid = options['parkid']
    if not parkid:
        nwlat, nwlng = float(options['lat']), float(options['lon'])
        selat, selng = float(options['lat2']), float(options['lon2'])
        res = searchParkLoc(selat, nwlat, nwlng, selng, int(options['size']))
    else:
        res = searchParkId(parkid.upper())

    return res

def searchSummitId(refid,isName = False):
    conn = sqlite3.connect('database/summits.db')
    cur = conn.cursor()
    if isName:
        query = f"select * from summits where assoc like 'Japan%' and name_k like '%{refid}%' "
    else:
        query = f"select * from summits where assoc like 'Japan%' and code like '%{refid}%' "
    cur.execute(query)
    res = []
    for r in cur.fetchall():
        (summit, lat, lng, pts, bonus, elev, name, name_k, desc, desc_k, _, _, actcnt, lastact, lastcall) =r
        res.append({
            'code': summit,
            'name': name,
            'name_k':name_k,
            'lat': lat,
            'lon': lng
            })
    conn.close()
    return res

def sotajaffpota_ref(options):
    refid = options['refid']
    if not refid:
        return {'counts':0, 'reference':[]}

    refid = refid.upper()
    msota = re.search(r'\w\w-\d+', refid)
    mpota = re.search(r'\d\d\d\d', refid)

    if 'JA-' in refid or 'JAFF-' in refid or mpota:
        res = searchParkId(refid)
    elif msota:
        res = searchSummitId(refid)
    elif refid.isascii():
        
        res  = searchParkId(refid)
        res += searchSummitId(refid)
    else:
        res  = searchParkId(refid, True)
        res += searchSummitId(refid, True)

    return {'counts': len(res), 'reference': res }

def make_response(worldwide, flag, slist):
    res = []

    if (flag & 0x02) == 2:
        return({'totalCount': len(slist)})

    gsifl = (flag & 0x01) == 1
    
    for r in slist:
        if not r:
            return res
        else:
            (summit_id, lat, lng, pts, bonus, elev, name, name_k, desc, desc_k, _, _, actcnt, lastact, lastcall) = r
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
                'bonus': bonus,
                'elev': elev,
                'name':name,
                'name_k':name_k,
                'desc': desc_k,
                'actcnt': actcnt,
                'lastact': lastact,
                'lastcall': lastcall,
                'gsi_info': gsi
            })

    return res


def sotasummit_region(worldwide, options):

    conn = sqlite3.connect('database/summits.db')
    cur = conn.cursor()

    try:
        if not options['flag']:
            gsifl = 1
        else:
            gsifl = int(options['flag'])
            
        code = options['code']
        name = options['name']

        if code:
            query = 'select * from summits where code like ?'
            cur.execute(query, ('%' + code.upper() + '%', ))
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
            m = re.match(r'"(.+)"',name)
            if m:
                arg = m.group(1)
            else:
                arg = '%' + name + '%'
            cur.execute(query, (arg, ))
            r = cur.fetchall()
            print(arg)
            print(len(r))
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
                
            query = 'select * from summits where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?) and (alt > ?)'
            cur.execute(query, (selat, nwlat, nwlng, selng, elev))
            slist = []
            res = make_response(worldwide, gsifl, cur.fetchall())
            conn.close()
            
            if options['park']:
                park = searchParkLoc(selat, nwlat, nwlng, selng, int(options['park']))
            else:
                park = []
                
            if res:
                return {'errors': 'OK', 'summits': res, 'parks':park}
            else:
                if park:
                    return {'errors': 'OK', 'summits': [], 'parks':park}
                else:
                    return {'errors': 'No summits.'}

    except Exception as err:
        conn.close()
        print('Error:')
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
        if '/' in codep or '-' in codep:
            if codep.startswith('JA'):
                options['code'] = ambg
                return sotasummit_region(False, options)
            else:
                options['code'] = ambg
                return sotasummit_region(True, options)
        else:
            s = ambg.replace('"','')
            if s.encode('utf-8').isalnum():
                options['name'] = ambg
                return sotasummit_region(True, options)
            else:
                options['name'] = ambg
                return sotasummit_region(False, options)
        

if __name__ == "__main__":
    options = {
        'ambg': 'a',
        'code': None,
        'name': None,
        'flag':'0',
        #        'lat':'35.754976', 'lon':'138.232899',
        #       'lat2':'34.754976', 'lon2':'139.232899',
        #        'lat2':None, 'lon2':'140.232899',
        'lat2':'34.0',
        'lat':'36.0',
        'lon':'133.0',
        'lon2':'134.0',
        'elevation':None,
        #        'range':'100',
        'park':'2',
        'refid':'武甲'
    }
    #    print(searchParkId('JAFF-0196'))
    #    print(searchParkId('JA-0014'))
    #    print(searchParkLoc('34.0','36.0','133.0','134.0',0))
    print(sotajaffpota_ref(options))
    #    print(sotasummit('ww', 'HB/GR-088', None))
    #    print(sotasummit('ja', None, None, '35.754976', '138.232899'))
    #    print(sotasummit('WW', None, None, '35.754976', '138.232899'))
    #    print(sotasummit('ww', None, None, '45.8325', '6.8644', '3'))
    #    print(sotasummit('ja', None, '槍'))
    #    print(sotasummit('ww', None, 'Gun'))
    #    print(sotasummit('ja', options))
