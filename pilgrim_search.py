import maidenhead as mh
import os
import pyproj
import re
import sqlite3
import toml

class PILGRIMSearch:

    def __init__(self, **args):
        self.basedir = args.get('basedir', '.')

        self.conn = None
        with open(self.basedir + '/search_config.toml') as f:
            config = toml.load(f)

        self.config = config['PILGRIM']

        self.conn = sqlite3.connect(
            self.config['dbdir'] + self.config['database'])

        self.grs80 = pyproj.Geod(ellps='GRS80')

    def __del__(self):
        if self.conn:
            self.conn.close()

    def make_response(self, tlist):
        res = []

        for t in tlist:
            if not t:
                return res
            else:
                (site_no, sacred, temple, reading, address, lat, lng) = t
                res.append({
                    'site_no': site_no,
                    'sacredplace': sacred,
                    'name': temple,
                    'reading': reading,
                    'address': address,
                    'lat': lat,
                    'lon': lng,
                })

        return res

    def search(self, options):

        cur = self.conn.cursor()

        try:
            site = options.get('site', None)
            name = options.get('name', None)

            if site:
                query = 'select * from pilgrim where site_no like ?'
                cur.execute(query, ('%' + site + '%', ))
                r = cur.fetchall()
                res = self.make_response(r)
                if res:
                    return {'errors': 'OK', 'temples': res}
                else:
                    return {'errors': 'No such temples.'}
            elif name:
                query = 'select * from pilgrim where temple_name like ? or reading like ?'
                arg = '%' + name + '%'
                cur.execute(query, (arg, arg, ))
                r = cur.fetchall()
                res = self.make_response(r)
                if res:
                    return {'errors': 'OK', 'temples': res}
                else:
                    return {'errors': 'No such temple.'}
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
                    raise Exception

                query = 'select * from pilgrim where (lat > ?) and (lat < ?) and (lng > ?) and (lng < ?)'
                cur.execute(query, (selat, nwlat, nwlng, selng))
                res = self.make_response(cur.fetchall())
                if res:
                    return {'errors': 'OK', 'temples': res}
                else:
                    return {'errors': 'No such temple.'}

        except Exception as err:
            print('Error:')
            print(err)
            return {'errors': 'parameter out of range'}


if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    pilgrim = PILGRIMSearch(basedir=basedir)

    options = {
        'site': '11',
        'name': '寺',
        'lat': '35.918529',
        'lon': '138.522105',
        'lon2': None,
    }

    res = pilgrim.search(options)
    print(res)
