import io
import numpy as np
from scipy.io.wavfile import write
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_post_reading():
    r = client.post("/readings", json={"zone":"Green Park", "db":61, "source":"test"})
    assert r.status_code == 200 and r.json()["db"] == 61

def test_analyze_wav():
    sr = 16000; t = np.arange(sr) / sr
    x = (0.12*np.sin(2*np.pi*440*t) + .01*np.random.default_rng(1).normal(size=sr)).astype(np.float32)
    b = io.BytesIO(); write(b, sr, x)
    r = client.post("/analyze", data={"zone":"Market Square"}, files={"file":("test.wav", b.getvalue(), "audio/wav")})
    assert r.status_code == 200 and r.json()["dominant_hz"] > 400

def test_agent_alert():
    client.post("/readings", json={"zone":"City Hospital", "db":90, "source":"Traffic/engine"})
    r = client.post("/agent/run")
    assert r.status_code == 200
    assert any(x["zone"] == "City Hospital" for x in client.get("/alerts").json())
