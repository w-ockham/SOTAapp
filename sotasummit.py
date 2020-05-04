import pyproj
import sqlite3

grs80 = pyproj.Geod(ellps='GRS80')

def make_response(slist):
    res = []
    for r in slist:
        if not r:
            return res
        else:
            (summit_id, lat, lng, pts, elev, name, desc, name_k, desc_k ) = r
            res.append({
                'code': summit_id,
                'lat': lat,
                'lon': lng,
                'pts': pts,
                'elev': elev,
                'name': name,
                'desc': desc,
                'name_j': name_k,
                'desc_j': desc_k
            })
    return res
    
def sotasummit_ja(name, lat='35.474779', lng='139.162863', rng='20'):

    conn = sqlite3.connect('ja_summits.db')
    cur = conn.cursor()

    try:
        if name :
            query = 'select * from ja_summit where summit_id = ?'
            cur.execute(query, (name, ))
            r = cur.fetchone()
            res =  make_response([r])
            conn.close();
            if res:
                return {'errors': 'OK', 'summits': res}
            else:
                return {'errors': 'No such summit.'}
        else:
            if not lat or not lng:
                raise Exception
            else:
                lat, lng = float(lat), float(lng)

            if not rng:
                rng = 10000;
            else:
                rng = int(rng) * 1000
                
            if rng > 30000:
                rng = 30000

            nwlng, nwlat, _  = grs80.fwd(lng, lat, -45.0, rng)
            selng, selat, _  = grs80.fwd(lng, lat, 135.0, rng)

            query = 'select * from ja_summit where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?)'
            cur.execute(query, (selat, nwlat, nwlng, selng))
            slist = []
            res = make_response(cur.fetchall())
            conn.close()
            if res:
                return {'errors': 'OK', 'summits': res}
            else:
                return {'errors': 'No summits.'}

    except Exception as err:
        conn.close()
        return {'errors': 'parameter out of range'}

if __name__ == "__main__":
    print(sotasummit_ja('JA/NN-001'))
    print(sotasummit_ja(None))
    print(sotasummit_ja(None,'35.754976','138.232899'))
    print(sotasummit_ja(None,'35.754976','138.232899','1'))
