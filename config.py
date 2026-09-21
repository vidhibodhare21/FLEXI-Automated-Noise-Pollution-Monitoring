import os
from pathlib import Path

LIMITS = {
    "Industrial": (75.0, 70.0),
    "Commercial": (65.0, 55.0),
    "Residential": (55.0, 45.0),
    "Silence zone": (50.0, 40.0),
}
ZONES = {
    "North Works": "Industrial",
    "Market Square": "Commercial",
    "Green Park": "Residential",
    "City Hospital": "Silence zone",
}
ON_VERCEL = os.getenv("VERCEL") == "1"
DB_PATH = os.getenv("DB_PATH") or ("/tmp/noise.db" if ON_VERCEL else str(Path(__file__).with_name("noise.db")))
PORT = int(os.getenv("PORT") or "7860")
SIM = os.getenv("SIM", "0" if ON_VERCEL else "1") == "1"
AUTO_AGENT = os.getenv("AUTO_AGENT", "0" if ON_VERCEL else "1") == "1"
AGENT_INTERVAL = int(os.getenv("AGENT_INTERVAL") or "60")
CAL_OFFSET = float(os.getenv("CAL_OFFSET") or "94")


def zone_limit(zone, hour=None):
    from datetime import datetime
    category = ZONES.get(zone, zone)
    if category not in LIMITS:
        raise ValueError("unknown zone")
    hour = datetime.now().hour if hour is None else int(hour)
    return LIMITS[category][0 if 6 <= hour < 22 else 1]
