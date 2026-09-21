from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
import numpy as np
from config import ZONES, zone_limit
from db import add_reading, readings, alerts, actions
from dsp import analyze_audio, wav_audio
from agent import run_agent, generate_report

router = APIRouter()

class Reading(BaseModel):
    zone: str
    db: float = Field(ge=0, le=180)
    source: Optional[str] = "Unknown"
    ts: Optional[str] = None

def valid_zone(zone):
    if zone not in ZONES: raise HTTPException(422, "unknown zone")
    return zone

def analyze(audio, zone, hour=None):
    valid_zone(zone)
    try: data = analyze_audio(audio)
    except ValueError as e: raise HTTPException(422, str(e))
    limit = zone_limit(zone, hour)
    data.pop("freq"); data.pop("spectrum")
    data.update({"zone": zone, "limit": limit, "verdict": "VIOLATION" if data["db"] > limit else "PASS"})
    add_reading(zone, data["db"], data["source"])
    return data

@router.get("/health")
def health(): return {"status": "ok"}

@router.post("/readings")
def post_reading(item: Reading):
    valid_zone(item.zone)
    if item.ts:
        try: datetime.fromisoformat(item.ts)
        except ValueError: raise HTTPException(422, "ts must be ISO-8601")
    return add_reading(item.zone, item.db, item.source or "Unknown", item.ts)

@router.get("/readings")
def get_readings(zone: Optional[str] = None, limit: int = 100):
    if zone: valid_zone(zone)
    return readings(zone, limit)

@router.post("/analyze")
async def post_analyze(file: UploadFile = File(...), zone: str = Form(...), hour: Optional[int] = Form(None)):
    if not file.filename.lower().endswith(".wav"): raise HTTPException(422, "upload a WAV file")
    if hour is not None and not 0 <= hour <= 23: raise HTTPException(422, "hour must be 0 to 23")
    data = await file.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024: raise HTTPException(413, "audio file must be 20 MB or smaller")
    try: audio = wav_audio(data)
    except Exception as e: raise HTTPException(422, f"invalid WAV file: {e}")
    return analyze(audio, zone, hour)

@router.get("/alerts")
def get_alerts(): return alerts()

@router.get("/stats")
def stats():
    out = {}
    for z in ZONES:
        rs = readings(z, 1000); vals = np.array([r["db"] for r in rs], dtype=float); lim = zone_limit(z)
        out[z] = {"average": round(float(vals.mean()),1) if len(vals) else None, "max": round(float(vals.max()),1) if len(vals) else None, "leq": round(float(10*np.log10(np.mean(10**(vals/10)))),1) if len(vals) else None, "percent_above": round(float(100*np.mean(vals>lim)),1) if len(vals) else 0, "limit": lim}
    return out

@router.post("/agent/run")
def agent_run(): return run_agent()

@router.get("/agent/log")
def agent_log(): return actions()

@router.get("/report")
def report(zone: Optional[str] = None):
    if zone: valid_zone(zone)
    return {"markdown": generate_report(zone)}
