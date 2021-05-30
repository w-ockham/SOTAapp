import json
import maidenhead as mh
import re
import requests
import sqlite3

gsi_endpoint = {
    'geocode':
    'https://msearch.gsi.go.jp/address-search/AddressSearch',

    'revgeocode':
    'https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress',

    'elevation':
    'https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php'
}


def lookup_muniCode(m):
    conn = sqlite3.connect('database/munitable.db')
    cur = conn.cursor()

    try:
        query = 'select * from muni where muniCd = ?'
        cur.execute(query, (m, ))
        r = cur.fetchone()
        if r:
            (_, pref, city, jcc, jcc_text, jcg, jcg_text) = r
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
            res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                   'jcc': jcc, 'jcc_text': jcc_text
                   }
        else:
            res = {'pref': pref, 'addr2': city, 'addr1': '', 'type': ty,
                   'jcg': jcg, 'jcg_text': jcg_text
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
            (_, pref, city, jcc, jcc_text, jcg, jcg_text) = i
            ty = 'JCC'
            city = re.sub(r'(.+)\(.+\)', r'\1', city)
            jcc_text = re.sub(r'(.+)\(.+\)', r'\1', jcc_text)
            if jcg != '':
                city = pref + jcg_text + city
                code_t = 'JCG#' + jcg
                title = jcg_text
            else:
                city = pref + city
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


def gsi_rev_geocoder(lat, lng, elev):
    try:
        if not lat or not lng:
            raise Exception
        pos = '?lat=' + str(lat) + '&lon=' + str(lng)
        rev_uri = gsi_endpoint['revgeocode'] + pos
        elev_uri = gsi_endpoint['elevation'] + pos + '&outtype=JSON'

        gl = mh.to_maiden(float(lat), float(lng),precision=4)
        
        r_get = requests.get(rev_uri)
        if r_get.status_code == 200:
            res = r_get.json()
            if res:
                muni = str(int(res['results']['muniCd']))
                r = lookup_muniCode(muni)
                r['addr1'] = res['results']['lv01Nm']
            else:
                return {'errors': 'OUTSIDE_JA', 'maidenhead':gl}
            if elev:
                r_get = requests.get(elev_uri)
                if r_get.status_code == 200:
                    res = r_get.json()
                    if res:
                        r['elevation'] = res['elevation']
                        r['hsrc'] = res['hsrc']
            r['maidenhead'] = gl
            r['errors'] = 'OK'
            return r
        else:
            raise Exception
    except Exception as err:
        return {'errors': 'parameter out of range'}


def gsi_rev_geocoder_list(coords, elev):
#    try:
        res = []
        for latlng in coords:
            res.append(gsi_rev_geocoder(latlng[0], latlng[1], elev))

        return res
#    except Exception as err:
#        return {'errors': 'parameter out of range'}

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

from sotasummit import sotasummit

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
                geo_uri = gsi_endpoint['geocode'] + '?q=' + query
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
   print(gsi_rev_geocoder_list([
       ['35.754976', '138.232899'],
        ['35.754976', '138.232899']], True))
#    data = gsi_geocoder_vue('aa', True, False)
#    print(json.dumps(data, ensure_ascii=False, indent=2))
#data = gsi_geocoder_vue('JA/NN-001', True, False)
#print(json.dumps(data, ensure_ascii=False, indent=2))
