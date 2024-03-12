import sqlite3
import re
from datetime import datetime, timezone


def spottimeline(options):
    db = sqlite3.connect('mdspots.db')
    cur = db.cursor()

    now = int(datetime.utcnow().strftime("%s"))

    if options['period']:
        period = int(options['period'])
    else:
        period = 3

    timefrom = now - period * 3600

    if options['region']:
        regs = options['region'].split(',')
        subq = " and (" + ' or '.join(f"region ='{r}'" for r in regs) +")"
    else:
        subq = " "

    if options['program']:
        r = options['program']
        subq += f"and prog = '{r}' "

    if options['bycall']:
        query = f"select distinct prog,callsign from mdspots2"\
            f" where utc > {timefrom}" + subq + "order by ref"
    else:
        query = f"select distinct prog,ref from mdspots2"\
            f" where utc > {timefrom}" + subq + "order by ref"

    spots = {}
    for (prog, v) in cur.execute(query):
        spots.setdefault(prog, {})
        spots[prog].setdefault(v, [])

    query = f"select * from mdspots2"\
        f" where utc > {timefrom}" + subq + "and tweeted=1 order by utc"

    for e in cur.execute(query):
        (utc, _, prog, call, ref, name, freq, rawfreq,
         mode, loc, _, comment, spotter, _) = e
        tstr = datetime.fromtimestamp(utc).isoformat() + 'Z'

        if options['bycall']:
            spots[prog][call].append(
                (tstr, ref, rawfreq, mode.upper(), comment, spotter))
        else:
            spots[prog][ref].append(
                (tstr, call, rawfreq, mode.upper(), comment, spotter))
    db.close()
    return spots


if __name__ == "__main__":
    options = {
        'program': 'pota',
        'region': 'JA',
        'period': 24,
        'bycall': None,
    }
    print(spottimeline(options))
