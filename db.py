import sqlite3
from datetime import datetime
from config import DB_PATH


def con():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("pragma busy_timeout=30000")
    return c


def init_db():
    with con() as c:
        c.execute("pragma journal_mode=WAL")
        c.executescript("""
        create table if not exists readings (id integer primary key, zone text not null, db real not null, source text, ts text not null);
        create table if not exists alerts (id integer primary key, zone text not null, severity text not null, message text not null, ts text not null, resolved integer default 0);
        create table if not exists agent_actions (id integer primary key, zone text not null, step text not null, detail text not null, ts text not null);
        create table if not exists escalations (id integer primary key, zone text not null, severity text not null, message text not null, ts text not null);
        """)


def add_reading(zone, level, source="Unknown", ts=None):
    ts = ts or datetime.now().isoformat(timespec="seconds")
    with con() as c:
        c.execute("insert into readings(zone,db,source,ts) values(?,?,?,?)", (zone, float(level), source, ts))
    return {"zone": zone, "db": float(level), "source": source, "ts": ts}


def readings(zone=None, limit=100):
    q, vals = "select * from readings", []
    if zone:
        q += " where zone=?"; vals.append(zone)
    q += " order by ts desc limit ?"; vals.append(min(max(int(limit), 1), 1000))
    with con() as c: return [dict(x) for x in c.execute(q, vals)]


def add_alert(zone, severity, message):
    ts = datetime.now().isoformat(timespec="seconds")
    with con() as c: c.execute("insert into alerts(zone,severity,message,ts) values(?,?,?,?)", (zone, severity, message, ts))


def alerts(limit=200):
    with con() as c: return [dict(x) for x in c.execute("select * from alerts order by ts desc limit ?", (limit,))]


def action(zone, step, detail):
    ts = datetime.now().isoformat(timespec="seconds")
    with con() as c: c.execute("insert into agent_actions(zone,step,detail,ts) values(?,?,?,?)", (zone, step, detail, ts))


def actions(limit=200):
    with con() as c: return [dict(x) for x in c.execute("select * from agent_actions order by ts desc limit ?", (limit,))]


def count_readings():
    with con() as c: return c.execute("select count(*) from readings").fetchone()[0]


def add_escalation(zone, severity, message):
    with con() as c: c.execute("insert into escalations(zone,severity,message,ts) values(?,?,?,?)", (zone, severity, message, datetime.now().isoformat(timespec="seconds")))
