import argparse
import random
import time
from datetime import datetime, timedelta
import requests
from config import ZONES, zone_limit
from db import add_reading, count_readings


def level(zone):
    base = zone_limit(zone) - 7
    bump = random.choice([0, 0, 0, 4, 10, 18])
    return round(max(30, base + bump + random.uniform(-4, 4)), 1)


def seed():
    if count_readings(): return
    now = datetime.now()
    for z in ZONES:
        for i in range(48):
            ts = now - timedelta(minutes=30*(48-i))
            add_reading(z, level(z), "Sensor simulator", ts.isoformat(timespec="seconds"))


def tick():
    for z in ZONES: add_reading(z, level(z), "Sensor simulator")


def run(url=None):
    while True:
        if url:
            for z in ZONES: requests.post(url.rstrip("/")+"/readings", json={"zone":z,"db":level(z),"source":"Sensor simulator"}, timeout=5)
        else: tick()
        time.sleep(10)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--url", required=True); args = p.parse_args(); run(args.url)
