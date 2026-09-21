import os
import requests
from config import ZONES, zone_limit
from db import readings, alerts, add_alert, add_escalation, action


def get_recent_readings(zone, n=8): return list(reversed(readings(zone, n)))
def check_limit(zone): return zone_limit(zone)


def log_alert(zone, severity, message):
    add_alert(zone, severity, message)


def escalate(zone, severity, message):
    add_escalation(zone, severity, message)
    print(f"ESCALATION {zone}: {message}")
    url = os.getenv("WEBHOOK_URL")
    if url: requests.post(url, json={"zone": zone, "severity": severity, "message": message}, timeout=5)


def recommend_action(source):
    tips = {"Traffic/engine": "consider traffic diversion and no-idling checks", "Machinery/construction": "move noisy work to permitted hours", "Speech/crowd": "use crowd management and lower amplification", "Music/loudspeaker": "restrict loudspeaker volume and hours"}
    return tips.get(source, "continue monitoring")


TOOLS = {"get_recent_readings": get_recent_readings, "check_limit": check_limit, "log_alert": log_alert, "escalate": escalate, "recommend_action": recommend_action}


def severity(margin, persistent, trend, repeats):
    score = (2 if margin > 15 else 1 if margin > 5 else 0) + (1 if persistent else 0) + (1 if trend > 3 else 0) + (1 if repeats >= 2 else 0)
    return ["none", "low", "medium", "high", "critical"][min(score, 4)]


def run_zone(zone):
    rs = get_recent_readings(zone)
    if not rs: return None
    limit = check_limit(zone); vals = [r["db"] for r in rs]; latest = vals[-1]
    margin = latest - limit; persistent = len(vals) >= 3 and all(v > limit for v in vals[-3:])
    split = max(1, len(vals)//2); trend = sum(vals[-split:])/len(vals[-split:]) - sum(vals[:split])/len(vals[:split])
    repeats = sum(a["zone"] == zone for a in alerts(100))
    sev = severity(margin, persistent, trend, repeats) if margin > 0 else "none"
    why = f"{latest:.1f} dB(A), limit {limit:.0f}, margin {margin:+.1f}; persistent={persistent}, trend={trend:+.1f}"
    action(zone, "reason", why)
    if sev == "none": return {"zone": zone, "severity": sev, "reason": why}
    source = rs[-1].get("source") or "Unknown"
    msg = f"{sev.upper()} violation in {zone}: {why}. Action: {recommend_action(source)}."
    log_alert(zone, sev, msg); action(zone, "alert", msg)
    if sev in ("high", "critical"):
        try: escalate(zone, sev, msg); action(zone, "escalate", "escalation record created")
        except requests.RequestException: action(zone, "escalate", "webhook unavailable; escalation recorded locally")
    return {"zone": zone, "severity": sev, "reason": why, "message": msg}


def run_agent():
    return [x for x in (run_zone(z) for z in ZONES) if x]


def generate_report(zone=None):
    rs = readings(zone, 1000); title = zone or "All zones"
    if not rs: return f"# Noise report: {title}\n\nNo readings available."
    vals = [r["db"] for r in rs]; over = sum(r["db"] > zone_limit(r["zone"]) for r in rs)
    return f"# Noise report: {title}\n\nReadings: {len(rs)}  \nAverage: {sum(vals)/len(vals):.1f} dB(A)  \nMaximum: {max(vals):.1f} dB(A)  \nAbove applicable limit: {over} ({100*over/len(rs):.1f}%)\n\nGenerated automatically from stored sensor and audio readings."
