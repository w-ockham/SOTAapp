import json
import maidenhead as mh
import re
import requests
import sqlite3
import urllib
from areacode import get_areacode

endpoint = {
    'geocode':
    'https://msearch.gsi.go.jp/address-search/AddressSearch',

    'revgeocode':
    'https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress',

    'elevation':
    'https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php',

    'radiousage':
    'https://www.tele.soumu.go.jp/musen/list?ST=1&OW=AT&OF=2&DA=0&SC=0&DC=1&MA=',

    'mapcode':
    'https://www.drivenippon.com/mapcode/app/dn/navicon_start.php',
}

def lookup_muniCode(m):
    conn = sqlite3.connect('database/munitable.db')
    cur = conn.cursor()

    try:
        query = 'select * from muni where muniCd = ?'
        cur.execute(query, (m, ))
        r = cur.fetchone()
        if r:
            (_, pref, city, jcc, wdcd, jcc_text, jcg, jcg_text, hamlog) = r
            ty = 'JCC'
            city = re.sub(r'(.+)\(.+\)', r'\1', city)
            jcc_text = re.sub(r'(.+)\(.+\)', r'\1', jcc_text)
            if jcg != '':
                city = jcg_text + city
                ty = 'JCG'
        else:
            raise Exception

        conn.close()

        if ty == 'JCC':
            if wdcd == '':
                res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                       'jcc': jcc, 'jcc_text': jcc_text
                    }
            else:
                res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                       'jcc': jcc, 'ward': wdcd, 'jcc_text': city
                    }
        else:
            res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                   'jcg': jcg, 'jcg_text': jcg_text, 'hamlog':hamlog
                   }

        return res

    except Exception as err:
        conn.close()
        return {}

def lookup_jcc_jcg(q):
    conn = sqlite3.connect('database/munitable.db')
    cur = conn.cursor()

    try:
        m = re.match('\d+', q, re.A)
        if m:
            query = 'select * from muni where JCCCd like ? or JCGCd like ?'
            cur.execute(query, ('%'+ q + '%', '%'+ q + '%',))
        else:
            query = 'select * from muni where City like ? or JCC_text like ? or JCG_text like ?'
            cur.execute(query, ('%'+ q + '%', '%'+ q + '%','%'+ q + '%',))

        rslt = []
        res = cur.fetchall()
        for i in res:
            (_, pref, city, jcc, wdcd, jcc_text, jcg, jcg_text, hamlog) = i
            ty = 'JCC'
            city = re.sub(r'(.+)\(.+\)', r'\1', city)
            jcc_text = re.sub(r'(.+)\(.+\)', r'\1', jcc_text)
            if jcg != '':
                city = pref + jcg_text + city
                code_t = 'JCG#' + jcg + hamlog
                title = jcg_text
            else:
                city = pref + city
                if wdcd != '':
                    code_t = 'JCC#' + wdcd
                else:
                    code_t = 'JCC#' + jcc
                title = jcc_text
            rslt.append({
                'type':'Feature',
                'properties':{
                    'title': title,
                    'code': code_t,
                    'address': city}})
        conn.close()
        return rslt

    except Exception as err:
        print(err)
        conn.close()
        return []

def addr2coord(addr):
    try:
        if not addr:
            raise Exception
        gsi_uri = endpoint['geocode'] + '?q=' + urllib.parse.quote(addr)
        r_get = requests.get(gsi_uri)
        if r_get.status_code == 200:
            res = r_get.json()
            lnglat = res[0]['geometry']['coordinates']
            gl = mh.to_maiden(float(lnglat[1]), float(lnglat[0]),precision=4)
            return (lnglat , gl)
    except Exception as err:
        return ([0,0], '')

def radio_station_qth(callsign, reverse = True):
    try:
        if not callsign:
            raise Exception
        usage_uri = endpoint['radiousage'] + callsign.upper()
        r_get = requests.get(usage_uri)
        if r_get.status_code == 200:
            res = r_get.json()
            if res['musenInformation']['totalCount'] != '0':
                rslt = []
                for st in res['musen']:
                    addr = st['listInfo']['tdfkCd']
                    (lnglat,gl) = addr2coord(addr)
                    if code:
                        res = gsi_rev_geocoder(lnglat[1], lnglat[0], False)
                        rslt.append({ 'callsign':callsign.upper() , 'coordinates': lnglat , 'maidenhead':gl, 'addr' :res}) 
                    else:
                        rslt.append({ 'callsign':callsign.upper() , 'coordinates': lnglat , 'maidenhead':gl, 'addr': addr })
                return { 'stations': rslt , 'errors': 'OK'}
            else:
                return { 'errors': 'Station not found'}
    except Exception as err:
        print(err)
        return {'errors': 'Parameter out of range'}

def gsi_rev_geocoder(lat, lng, elev = False, mapcode = False):
    try:
        if not lat or not lng:
            raise Exception
        pos = '?lat=' + str(lat) + '&lon=' + str(lng)
        rev_uri = endpoint['revgeocode'] + pos
        elev_uri = endpoint['elevation'] + pos + '&outtype=JSON'

        gl = mh.to_maiden(float(lat), float(lng),precision=4)
        
        r_get = requests.get(rev_uri)
        if r_get.status_code == 200:
            res = r_get.json()
            if res:
                muni = str(int(res['results']['muniCd']))
                r = lookup_muniCode(muni)
                r['addr1'] = res['results']['lv01Nm']
                r['areacode'] = get_areacode(r['pref'])[:1]
            else:
                r = {'pref': '', 'addr2': '', 'addr1': '', 'type': 'JCC',
                     'jcc':':Unkown', 'jcc_text':''
                }
            r['maidenhead'] = gl

            if mapcode:
                r['mapcode'] = get_mapcode(lat, lng)
                
            if elev:
                r_get = requests.get(elev_uri)
                if r_get.status_code == 200:
                    res = r_get.json()
                    if res:
                        r['elevation'] = res['elevation']
                        r['hsrc'] = res['hsrc']
                        if r['elevation']=='-----':
                            r['errors'] = 'OUTSIDE_JA'
                        else:
                            r['errors'] = 'OK'
                        return r
                    raise Exception
            else:
                r['errors'] = 'OK'
                return r
        raise Exception
    except Exception as err:
        print(err)
        return {'errors': 'Parameter out of range'}

def get_mapcode(lat, lng):
    try:
        if not lat or not lng:
            raise Exception
        pos = {'lat' : str(lat) ,'lng': str(lng)}
        r_get = requests.post(endpoint['mapcode'], data=pos)
        if r_get.status_code == 200:
            for m in re.finditer(r'.+id="mapcode">(.+)<', r_get.text, re.MULTILINE):
                return m.group(1)

            return ''
        return ''
    except Exception as err:
        print(err)
        return ''

def gsi_rev_geocoder_list(coords, elev):
    res = []
    for latlng in coords:
        res.append(gsi_rev_geocoder(latlng[0], latlng[1], elev))
        
    return res

def sota_to_geojson(x):
    return ({'geometry':{
        'coordinates':[float(x['lat']),float(x['lon'])],
        'type': 'Point'},
            'type':'Feature',
            'properties':{
                'code': x['code'],
                'title': x['name_j'],
                'point': x['pts'],
                'elevation':float(x['elev']),
                'address':x['desc_j']}})

#from sotasummit import sotasummit

def gsi_geocoder(query, elev, revquery):
    try:
        m = re.match(r'(\w|\d|/|-)+', query, re.A)
        if m:
            m = re.match(r'\d+', query, re.A)
            if m:
                return lookup_jcc_jcg(query)
            else:
                res = sotasummit('JA', query, None)
                if res.get('summits'):
                    return(list(map(sota_to_geojson,
                                    list(res['summits']))))
                else:
                    return([])
        else:
            res = sotasummit('JA', None, query)
            if res.get('summits'):
                res1 = list(map(sota_to_geojson,list(res['summits'])))
            else:
                res1 = []
            res2 = lookup_jcc_jcg(query)

            if revquery:
                geo_uri = endpoint['geocode'] + '?q=' + query
                r_get = requests.get(geo_uri)
                if r_get.status_code == 200:
                    res = r_get.json()
                    if len(res) < 10:
                        for r in res:
                            rev = gsi_rev_geocoder(r['geometry']['coordinates'][1],
                                                   r['geometry']['coordinates'][0], True)
                            r['properties'].update(address=rev)
                    return(res1 + res2 + res)
                else:
                    raise Exception
            else:
                return(res1+ res2)

    except Exception as err:
        raise err
        return {'errors': 'parameter out of range'}

def gsi_geocoder_vue(query, elev, revquery):
    res = gsi_geocoder(query, elev, revquery)
    rslt = []
    for r in res:
        g = r.get('geometry')
        if g:
            pos = r['geometry']['coordinates']
            elev = r['properties']['elevation']
        else:
            pos = []
            elev = 0
            
        rslt.append({
            'code': r['properties']['code'],
            'title': r['properties']['title'],
            'address': r['properties']['address'],
            'position': pos,
            'elevation':elev
            })
    return(rslt)

if __name__ == "__main__":
    print(gsi_rev_geocoder(35.595247, 139.517828, True, True))
    print(gsi_rev_geocoder(43.804832, 142.879944, True, True))
#    print(radio_station_qth('jl1nie'))
#    print(gsi_rev_geocoder_list([
#       ['55.754976', '138.232899'],
#        ['35.754976', '138.232899']], True))
#    data = gsi_geocoder_vue('aa', True, False)
#    print(json.dumps(data, ensure_ascii=False, indent=2))
#data = gsi_geocoder_vue('JA/NN-001', True, False)
#print(json.dumps(data, ensure_ascii=False, indent=2))
