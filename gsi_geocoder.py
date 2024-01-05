import json
import maidenhead as mh
import os
import re
import requests
import sqlite3
import urllib
import toml

from areacode import get_areacode

class GeoCoder:
    def __init__(self, **args):
        self.endpoint = {
            'geocode':
            'https://msearch.gsi.go.jp/address-search/AddressSearch',

            'revgeocode':
            'https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress',
            'yahoorev':
            'https://map.yahooapis.jp/geoapi/V1/reverseGeoCoder',

            'elevation':
            'https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php',

            'radiousage':
            'https://www.tele.soumu.go.jp/musen/list?ST=1&OW=AT&OF=2&DA=0&SC=0&DC=1&MA=',

            'mapcode_denso':
            'https://www.drivenippon.com/mapcode/app/dn/navicon_start.php',

            'mapcode':
            'https://saibara.sakura.ne.jp/map/convgeo.cgi',

        }

        self.basedir = args.get('basedir', '.')
        self.conn = None

        with open(self.basedir + '/search_config.toml') as f:
            config = toml.load(f)

        self.config = config['GEOCODER']

        self.conn = sqlite3.connect(
            self.config['dbdir'] + self.config['database'],
            isolation_level='IMMEDIATE', timeout=3000)
        
    def __del__(self):
        if self.conn:
            self.conn.close()
            

    def lookup_muniCode(self, m, addr):
        cur = self.conn.cursor()
        if not addr:
            addr = ''
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
                if int(m) == 22135 and not (r'三方原町' in addr):
                    wdcd = '180209'
                    city = re.sub(r'中央区', r'浜名区', city)
            else:
                raise Exception
            if ty == 'JCC':
                if wdcd == '':
                    res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                           'jcc': jcc, 'jcc_text': jcc_text,
                           }
                else:
                    res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                           'jcc': jcc, 'ward': wdcd, 'jcc_text': city
                           }
            else:
                res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                       'jcg': jcg, 'jcg_text': jcg_text, 'hamlog': hamlog
                       }
            return res

        except Exception as err:
            print(f"Error muniCd lookup:{err}")
            return {}


    def lookup_jcc_jcg(self, q):
        cur = conn.cursor()
        try:
            m = re.match('\d+', q, re.A)
            if m:
                query = 'select * from muni where JCCCd like ? or JCGCd like ?'
                cur.execute(query, ('%' + q + '%', '%' + q + '%',))
            else:
                query = 'select * from muni where City like ? or JCC_text like ? or JCG_text like ?'
                cur.execute(query, ('%' + q + '%', '%' + q + '%', '%' + q + '%',))

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
                    'type': 'Feature',
                    'properties': {
                        'title': title,
                        'code': code_t,
                        'address': city}})
            return rslt
        except Exception as err:
            print(err)
            return []

    def addr2coord(self, addr):
        try:
            if not addr:
                raise Exception
            gsi_uri = self.endpoint['geocode'] + '?q=' + urllib.parse.quote(addr)
            r_get = requests.get(gsi_uri)
            if r_get.status_code == 200:
                res = r_get.json()
                lnglat = res[0]['geometry']['coordinates']
                gl = mh.to_maiden(float(lnglat[1]), float(lnglat[0]), precision=4)
                return (lnglat, gl)
            else:
                raise Exception
        except Exception as err:
            return ([0, 0], '')


    def radio_station_qth(self, callsign, reverse=True):
        try:
            if not callsign:
                raise Exception
            usage_uri = self.endpoint['radiousage'] + callsign.upper()
            r_get = requests.get(usage_uri)
            if r_get.status_code == 200:
                res = r_get.json()
                if res['musenInformation']['totalCount'] != '0':
                    rslt = []
                    for st in res['musen']:
                        addr = st['listInfo']['tdfkCd']
                        (lnglat, gl) = self.addr2coord(addr)
                        if reverse:
                            res = self.gsi_rev_geocoder(lnglat[1], lnglat[0], False)
                            rslt.append({'callsign': callsign.upper(
                            ), 'coordinates': lnglat, 'maidenhead': gl, 'addr': res})
                        else:
                            rslt.append({'callsign': callsign.upper(
                            ), 'coordinates': lnglat, 'maidenhead': gl, 'addr': addr})
                    return {'stations': rslt, 'errors': 'OK'}
                else:
                    return {'errors': 'Station not found'}
            else:
                raise Exception
        except Exception as err:
            print(err)
            return {'errors': 'Parameter out of range'}


    def lookup_mapcode_municode(self, lat, lng, muni, addr):
        if muni:
            r = self.lookup_muniCode(str(int(muni)), addr)
            if 'pref' in r:
                r['areacode'] = get_areacode(r['pref'])[:1]
            r['mapcode'] = self.get_mapcode(lat, lng)
            r['maidenhead'] = mh.to_maiden(float(lat), float(lng), precision=4)
            r['errors'] = 'OK'
            return r
        else:
            print(f"Error invalid muniCd: municd={muni} addr={addr}")
            return {'errors': 'Invalid muniCode',
                    'maidenhead': mh.to_maiden(float(lat), float(lng), precision=4)
                    }
        
    def gsi_rev_geocoder(self, lat, lng):
        try:
            if not lat or not lng:
                return {'errors': 'Parameter out of range.'}

            appid =  'appid=' + self.config['client_id'] +'&output=json'
            pos = 'lat=' + str(lat) + '&lon=' + str(lng)
        
            rev_uri = self.endpoint['yahoorev'] + '?' + appid + '&'+ pos
            elev_uri = self.endpoint['elevation'] +'?' +  pos + '&outtype=JSON'

            gl = mh.to_maiden(float(lat), float(lng), precision=4)
            mapcode= self.get_mapcode(lat, lng)

            r_get = requests.get(rev_uri)
            if r_get.status_code == 200:
                res = r_get.json()
                if res:
                    res = res['Feature'][0]['Property']
                    municd = res['AddressElement'][1]['Code']
                    pref = res['AddressElement'][0]['Name']
                    addr = res['AddressElement'][2]['Name']
                    muni = str(int(municd))
                    r = self.lookup_muniCode(muni, addr)
                    if r:
                        r['addr1'] = addr
                        r['areacode'] = get_areacode(pref)
                        r['maidenhead'] = gl
                        r['mapcode'] = mapcode 
                        r['errors'] = 'OK'
                    else:
                        r['addr1'] = 'Unknown'
                        r['maidenhead'] = gl
                        r['mapcode'] = mapcode 
                        r['errors'] = 'OUTSIDE_JA'
                    return r
            else:
                raise Exception
        except Exception as err:
            print(f"Error: RevGecode status={err}")
            return {'errors': 'OUTISIDE_JA',
                    'maidenhead': gl,
                    'mapcode': mapcode}


    def get_mapcode_denso(self, lat, lng):
        try:
            if not lat or not lng:
                raise Exception
            pos = {'lat': str(lat), 'lng': str(lng)}
            r_get = requests.post(self.endpoint['mapcode_denso'], data=pos)
            if r_get.status_code == 200:
                for m in re.finditer(r'.+id="mapcode">(.+)<', r_get.text, re.MULTILINE):
                    return m.group(1)
            raise Exception
        except Exception as err:
            print(err)
            return ''

        
    def get_mapcode(self, lat, lng):
        try:
            if not lat or not lng:
                raise Exception
            pos = {'t': 'wgsdeg', 'wgs_lat': str(lat), 'wgs_lon': str(lng)}
            r_get = requests.post(self.endpoint['mapcode'], data=pos)
            if r_get.status_code == 200:
                for m in re.finditer(r'.+name="mapcode" value="([0-9 *]+)"', r_get.text, re.MULTILINE):
                    return m.group(1)
            raise Exception
        except Exception as err:
            print(err)
            return ''

        
    def gsi_rev_geocoder_list(self, coords, elev):
        res = []
        for latlng in coords:
            res.append(self.gsi_rev_geocoder(latlng[0], latlng[1], elev))
        return res

    def sota_to_geojson(self, x):
        return ({'geometry': {
            'coordinates': [float(x['lat']), float(x['lon'])],
            'type': 'Point'},
                 'type': 'Feature',
                 'properties': {
                     'code': x['code'],
                     'title': x['name_j'],
                     'point': x['pts'],
                     'elevation': float(x['elev']),
                     'address': x['desc_j']}})

    def gsi_geocoder(self, query, elev, revquery):
        try:
            m = re.match(r'(\w|\d|/|-)+', query, re.A)
            if m:
                m = re.match(r'\d+', query, re.A)
                if m:
                    return self.lookup_jcc_jcg(query)
                else:
                    res = sotasummit('JA', query, None)
                    if res.get('summits'):
                        return (list(map(self.sota_to_geojson,
                                        list(res['summits']))))
                    else:
                        return ([])
            else:
                res = sotasummit('JA', None, query)
                if res.get('summits'):
                    res1 = list(map(sota_to_geojson, list(res['summits'])))
                else:
                    res1 = []
                res2 = self.lookup_jcc_jcg(query)

            if revquery:
                geo_uri = self.endpoint['geocode'] + '?q=' + query
                r_get = requests.get(geo_uri)
                if r_get.status_code == 200:
                    res = r_get.json()
                    if len(res) < 10:
                        for r in res:
                            rev = gsi_rev_geocoder(r['geometry']['coordinates'][1],
                                                   r['geometry']['coordinates'][0], True)
                            r['properties'].update(address=rev)
                    return (res1 + res2 + res)
                else:
                    raise Exception
            else:
                return (res1 + res2)

        except Exception as err:
            return {'errors': 'parameter out of range'}


    def gsi_geocoder_vue(self, query, elev, revquery):
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
                'elevation': elev
            })
        return (rslt)

    def gsi_check(self, lat, lng):
        pos = 'lat=' + str(lat) + '&lon=' + str(lng)
        rev_uri = self.endpoint['revgeocode'] + '?' + pos
        r_get = requests.get(rev_uri)
        if r_get.status_code == 200:
            res = r_get.json()
            return res
        else:
            return r_get.text
            
if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    geocoder = GeoCoder(basedir=basedir)
    print(geocoder.get_mapcode(35.656158618253926, 139.6459883257073)) 
    print(geocoder.gsi_rev_geocoder(35.595247, 139.517828))
    print(geocoder.gsi_rev_geocoder(34.845261, 137.584448))
    print(geocoder.gsi_check(34.845261, 137.584448))
    #print(geocoder.lookup_mapcode_municode(35.594, 139.517, 14137, ''))
    # print(gsi_rev_geocoder(43.804832, 142.879944, True, True))
   
    #print(geocoder.radio_station_qth('jl1nie'))
#    print(gsi_rev_geocoder_list([
#       ['55.754976', '138.232899'],
#        ['35.754976', '138.232899']], True))
#    data = gsi_geocoder_vue('aa', True, False)
#    print(json.dumps(data, ensure_ascii=False, indent=2))
# data = gsi_geocoder_vue('JA/NN-001', True, False)
# print(json.dumps(data, ensure_ascii=False, indent=2))
