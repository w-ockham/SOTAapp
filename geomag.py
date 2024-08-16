import datetime
import fcntl
import json
import os
import re
import requests
import pickle
import urllib

dbname = 'database/geomag.pkl'

geomagdb = {
    'LastUpdate': 0,
    'Date': '',
    'Ap': 0,
    'Kp':[]
}

endpoint = {
    'noaa':
    'https://services.swpc.noaa.gov/text/daily-geomagnetic-indices.txt'
}

def utc_now():
    return int(datetime.datetime.utcnow().strftime("%s"))

def update_geomagdb(ep, db):
    global geomagdb
    
    now = utc_now()
    with open(db, mode='rb') as f:
        geomagdb = pickle.load(f)
    
    if (now - geomagdb['LastUpdate']) < 600:
        return geomagdb
    
    geomagdb['LastUpdate'] = now
    
    r_get = requests.get(ep)
   
    if r_get.status_code != 200:
        print('Not Found:'+ep)
        return geomagdb

    lines = r_get.text.splitlines()[-2:]
    dt = list(map(lambda x: x[0:10],lines))
    aps = list(map(lambda x: x[60:62],lines))
    kps = list(map(lambda x: x[63:],lines))

    if aps[1] == '-1':
        geomagdb['Date'] = dt[0].replace(' ','')
        geomagdb['Ap'] = int(aps[0])
        data = kps[0].split()
    else:
        geomagdb['Date'] = dt[1].replace(' ','')
        geomagdb['Ap'] = int(aps[1])
        data = kps[1].split()

    geomagdb['Kp'] = []

    for kp in data:
        lastkp = int(float(kp))
        if lastkp >= 0:
            geomagdb['Kp'] = [ lastkp ] + geomagdb['Kp']

    with open(db, mode='wb') as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            pickle.dump(geomagdb, f)
        except IOError:
            return geomagdb
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
    return geomagdb
    
def create_geomagdb(ep, db):
    with open(db, mode='wb') as f:
        pickle.dump(geomagdb, f)
    update_geomagdb(ep, db)
    
def kp_indicies():
    ep = endpoint['noaa']
    if not os.path.isfile(dbname):
        create_geomagdb(ep, dbname)

    return update_geomagdb(ep, dbname)
    
if __name__ == "__main__":
    print(kp_indicies())
