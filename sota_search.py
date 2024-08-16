import maidenhead as mh
import os
import pyproj
import re
import sqlite3
import toml


class SOTASearch:
    ja_pref_table = [
        ('JA/NI', '0', '新潟県', '本州支部'),
        ('JA/NN', '0', '長野県', '本州支部'),
        ('JA/TK', '1', '東京都', '本州支部'),
        ('JA/KN', '1', '神奈川県', '本州支部'),
        ('JA/CB', '1', '千葉県', '本州支部'),
        ('JA/ST', '1', '埼玉県', '本州支部'),
        ('JA/IB', '1', '茨城県', '本州支部'),
        ('JA/TG', '1', '栃木県', '本州支部'),
        ('JA/GM', '1', '群馬県', '本州支部'),
        ('JA/YN', '1', '山梨県', '本州支部'),
        ('JA/SO', '2', '静岡県', '本州支部'),
        ('JA/GF', '2', '岐阜県', '本州支部'),
        ('JA/AC', '2', '愛知県', '本州支部'),
        ('JA/ME', '2', '三重県', '本州支部'),
        ('JA/KT', '3', '京都府', '本州支部'),
        ('JA/SI', '3', '滋賀県', '本州支部'),
        ('JA/NR', '3', '奈良県', '本州支部'),
        ('JA/OS', '3', '大阪府', '本州支部'),
        ('JA/WK', '3', '和歌山県', '本州支部'),
        ('JA/HG', '3', '兵庫県', '本州支部'),
        ('JA/OY', '4', '岡山県', '本州支部'),
        ('JA/SN', '4', '島根県', '本州支部'),
        ('JA/YG', '4', '山口県', '本州支部'),
        ('JA/TT', '4', '鳥取県', '本州支部'),
        ('JA/HS', '4', '広島県', '本州支部'),
        ('JA5/KA', '5', '香川県', '四国支部'),
        ('JA5/TS', '5', '徳島県', '四国支部'),
        ('JA5/EH', '5', '愛媛県', '四国支部'),
        ('JA5/KC', '5', '高知県', '四国支部'),
        ('JA6/FO', '6', '福岡県', '九州支部'),
        ('JA6/SG', '6', '佐賀県', '九州支部'),
        ('JA6/NS', '6', '長崎県', '九州支部'),
        ('JA6/KM', '6', '熊本県', '九州支部'),
        ('JA6/OT', '6', '大分県', '九州支部'),
        ('JA6/MZ', '6', '宮崎県', '九州支部'),
        ('JA6/KG', '6', '鹿児島', '九州支部'),
        ('JA6/ON', '6', '沖縄県', '九州支部'),
        ('JA/AM', '7', '青森県', '本州支部'),
        ('JA/IT', '7', '岩手県', '本州支部'),
        ('JA/AT', '7', '秋田県', '本州支部'),
        ('JA/YM', '7', '山形県', '本州支部'),
        ('JA/MG', '7', '宮城県', '本州支部'),
        ('JA/FS', '7', '福島県', '本州支部'),
        ('JA8/SY', '8', '宗谷支庁', '北海道支部'),
        ('JA8/RM', '8', '留萌支庁', '北海道支部'),
        ('JA8/KK', '8', '上川支庁', '北海道支部'),
        ('JA8/OH', '8', 'オホーツク支庁', '北海道支部'),
        ('JA8/SC', '8', '空知支庁', '北海道支部'),
        ('JA8/IS', '8', '石狩支庁', '北海道支部'),
        ('JA8/NM', '8', '根室支庁', '北海道支部'),
        ('JA8/SB', '8', '後志支庁', '北海道支部'),
        ('JA8/TC', '8', '十勝支庁', '北海道支部'),
        ('JA8/KR', '8', '釧路支庁', '北海道支部'),
        ('JA8/HD', '8', '日高支庁', '北海道支部'),
        ('JA8/IR', '8', '胆振支庁', '北海道支部'),
        ('JA8/HY', '8', '檜山支庁', '北海道支部'),
        ('JA8/OM', '8', '渡島支庁', '北海道支部'),
        ('JA/TY', '9', '富山県', '本州支部'),
        ('JA/FI', '9', '福井県', '本州支部'),
        ('JA/IK', '9', '石川県', '本州支部'),
    ]

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

        self.ja_prefecture = {}
        self.ja_association = {}

        self.max_response = 5

        for r in self.ja_pref_table:
            (prfx, area, pref, assoc) = r
            self.ja_prefecture[pref] = (prfx, area)

            areadata = self.ja_prefecture.get(area, None)
            if areadata:
                self.ja_prefecture[area] = self.ja_prefecture[area] + \
                    [(prfx, pref)]
            else:
                self.ja_prefecture[area] = [(prfx, pref)]

            assocdata = self.ja_association.get(assoc, None)
            if assocdata:
                self.ja_association[assoc] = self.ja_association[assoc] + \
                    [(prfx, pref)]
            else:
                self.ja_association[assoc] = [(prfx, pref)]

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

    def make_response(self, slist, flag, isKana=False, isBrief=False):
        res = []

        if (flag & 0x02) == 2:
            return ({'totalCount': len(slist)})

        for r in slist:
            if not r:
                break
            else:
                (summit_id, lat, lng, pts, bonus, elev, name, name_k,
                 desc, desc_k, _, _, actcnt, lastact, lastcall) = r
                gl = mh.to_maiden(float(lat), float(lng), precision=4)
                if isKana:
                    if isBrief:
                        res.append({
                            '山岳ID': summit_id,
                            '標高(m)': elev,
                            '名前': name_k,
                        })

                    else:
                        res.append({
                            '山岳ID': summit_id,
                            '緯度': lat,
                            '経度': lng,
                            'グリッドロケータ': gl,
                            'ポイント': pts,
                            '冬季ボーナスポイント': bonus,
                            '標高(m)': elev,
                            '名前': name_k,
                            '所在地': desc_k,
                            'アクティベーションされた回数': actcnt,
                            '最後にアクティベーションされた日': lastact,
                            '最後にアクティベーションした局': lastcall,
                        })
                else:
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
                        'gsi_info': None,
                    })
        return res

    def sotasummit_region(self, options, isWW=True):

        cur = self.conn.cursor()

        try:
            if not options.get('flag'):
                gsifl = 1
            else:
                gsifl = int(options['flag'])

            code = options.get('code', None)
            name = options.get('name', None)
            sort = options.get('sorted', None)

            if code:
                query = 'select * from summits where code like ?'
                cur.execute(query, ('%' + code.upper() + '%', ))
                r = cur.fetchall()
                res = self.make_response(r, gsifl)
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
                res = self.make_response(r, gsifl)
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
                res = self.make_response(cur.fetchall(), gsifl)

                if sort:
                    for r in res:
                        az, _, dist = self.grs80.inv(
                            lng, lat, r['lon'], r['lat'])
                        r['dist'] = int(dist)
                        r['azmt'] = int(az)
                    res.sort(key=lambda x: x['dist'])
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
                    return self.sotasummit_region(options, False)
                else:
                    options['code'] = ambg
                    return self.sotasummit_region(options, True)
            else:
                s = ambg.replace('"', '')
                if s.encode('utf-8').isalnum():
                    options['name'] = ambg
                    return self.sotasummit_region(options, True)
                else:
                    options['name'] = ambg
                    return self.sotasummit_region(options, False)

    def summits_info_by_refid(self, refids):
        cur = self.conn.cursor()
        qstr = 'select * from summits where code = ?'
        summits = list(set(re.findall(r"[a-zA-Z0-9]+/[a-zA-Z]+-\d+", refids)))
        res = []

        for code in summits:
            cur.execute(qstr, (code.upper(), ))
            r = cur.fetchall()
            res.append(self.make_response(r, 1, True)[0])

        return {'summit_info': res}

    def summits_info_by_name(self, name):
        cur = self.conn.cursor()
        qstr = 'select * from summits where name_k like ?'

        cur.execute(qstr, ("%" + name + "%", ))
        r = cur.fetchall()
        res = self.make_response(r, 1, True)

        return {'summit_info': res}

    def find_pref(self, pref):
        prfx = self.ja_prefecture.get(pref, None)
        if not prfx:
            prfx = self.ja_prefecture.get(pref + '県', None)
            if not prfx:
                prfx = self.ja_prefecture.get(pref + '府', None)
                if not prfx:
                    prfx = self.ja_prefecture.get(pref + '都', None)
                    if not prfx:
                        prfx = self.ja_prefecture.get(pref + '支庁', None)
                        if not prfx:
                            prfx = ('', '')
        return prfx

    def summits_info_by_location(self, pref, countOnly=False, alt_high = 10000, alt_low = 0):
        if pref.isdigit():
            return self.summits_info_by_area(pref, countOnly, alt_high, alt_low)
        else:
            (prfx, _) = self.find_pref(pref)
            if not prfx:
                return self.summits_info_by_assoc(pref, countOnly, alt_high, alt_low)
            else:
                cur = self.conn.cursor()
                qstr = 'select * from summits where code like ? and alt > ? and alt < ?'
                if alt_high != 10000 and alt_low == 0:
                    qstr += ' ORDER BY alt ASC'
                else:
                    qstr += ' ORDER BY alt DESC'
                cur.execute(qstr, ("%" + prfx + "%", alt_low, alt_high, ))
                r = cur.fetchall()
                res = self.make_response(r, 1, True, True)
                l = min(len(res), self.max_response)
                if countOnly:
                    return {'summits': len(res)}
                else:
                    return {'summits': len(res), 'count': l, 'summit_info': res[:l]}

    def summits_info_by_area(self, area, countOnly=False, alt_high = 10000, alt_low = 0):
        cur = self.conn.cursor()
        qstr = 'select * from summits where code like ? and alt > ? and alt < ?'
        if alt_high != 10000 and alt_low == 0:
            qstr += ' ORDER BY alt ASC'
        else:
            qstr += ' ORDER BY alt DESC'
        prfxs = self.ja_prefecture.get(area, None)

        if prfxs:
            rslt = []
            for prfx in prfxs:
                (p, _) = prfx
                cur.execute(qstr, ("%" + p + "%", alt_low, alt_high,))
                r = cur.fetchall()
                rslt = rslt + self.make_response(r, 1, True, True)
            rslt = sorted(rslt, key = lambda r: r['標高(m)'], reverse = False if 'ASC' in qstr else True)                                                
            l = min(len(rslt), self.max_response)
            if countOnly:
                return {'summits': len(res)}
            else:
                return {'summits': len(res), 'count': l, 'summit_info': rslt[:l]}
        else:
            return {'summits': 0, 'count': 0,  'summit_info': []}

    def summits_info_by_assoc(self, assoc, countOnly=False, alt_high = 10000, alt_low = 0):
        cur = self.conn.cursor()
        qstr = 'select * from summits where code like ? and alt > ? and alt < ?'
        if alt_high != 10000 and alt_low == 0:
            qstr += ' ORDER BY alt ASC'
        else:
            qstr += ' ORDER BY alt DESC'
        assocs = self.ja_association.get(assoc, None)
        if not assocs:
            assocs = self.ja_association.get(assoc + '支部', None)

        if assocs:
            rslt = []
            for a in assocs:
                (p, _) = a
                cur.execute(qstr, ("%" + p + "%", alt_low, alt_high))
                r = cur.fetchall()
                rslt = rslt + self.make_response(r, 1, True, True)
            rslt = sorted(rslt, key = lambda r: r['標高(m)'], reverse = False if 'ASC' in qstr else True)                                                
            l = min(len(rslt), self.max_response)
            if countOnly:
                return {'summits': len(rslt)}
            else:
                return {'summits': len(rslt), 'count': l, 'summit_info': rslt[:l]}
        else:
            return {'summits':0, 'count': 0, 'summit_info': []}


if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    sota = SOTASearch(basedir=basedir)

    options = {
        'code': None,
        'name': None,
        'flag': 2,
        'lat2': None,
        'lat': '35.918529',
        'lon': '138.522105',
        'lon2': None,
        'revgeo': True,
        'elevation': None,
        'range': None,
        'srange': '300',
    }

    # res = sota.sotasummit('ww', options)
    # print(res)

    options = {
        'code': None,
        'name': None,
        'elevation': None,
        'reverse': '0',
        'lat': '35.754976', 'lon': '138.232899',
        'lat2': '34.754976', 'lon2': '139.232899',
    }

    # res = sota.sotasummit('ja', options)
    # print(res)

    query = "JA/TT-001でアクティベーション可能ですが、JA/TT-001以外にJA/SO-001についてもおしえて"
    res = sota.summits_info_by_refid(query)
    print(res)
    query = "静岡"
    res = sota.summits_count_by_pref(query)
    print(res)
    query = "0"
    res = sota.summits_count_by_pref(query)
    print(res)
    query = "本州"
    res = sota.summits_count_by_pref(query)
    print(res)
