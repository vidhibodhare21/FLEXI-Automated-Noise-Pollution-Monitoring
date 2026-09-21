---
title: Automated Noise Pollution Monitoring
sdk: docker
app_port: 7860
---

# Automated Noise Pollution Monitoring

A college mini project that monitors four Indian noise-zone categories, analyzes uploaded/microphone audio, and uses a rule-based autonomous agent to create alerts, escalation records and reports. Limits follow India's Noise Pollution (Regulation and Control) Rules, 2000: Industrial 75/70, Commercial 65/55, Residential 55/45 and Silence zone 50/40 dB(A), day/night.

## Run locally

Requires Python 3.10 or newer.

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Linux/macOS:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:7860. API documentation is at `/docs`; useful checks are `/health`, `/stats`, `/alerts`, and `/report`.

## Docker and deployment

```sh
docker build -t noise-monitor .
docker run -p 7860:7860 noise-monitor
```

For Hugging Face Spaces, create a Docker Space and upload this repository; the front matter above declares Docker and port 7860. Render can use the Dockerfile with port 7860. Set `DB_PATH` to a persistent mounted path in production. Free-tier disks are often ephemeral, so the app automatically reseeds its demo history when empty.

For Vercel, import the GitHub repository; Vercel automatically detects the FastAPI `app` instance in `app.py`. The lightweight `requirements.txt` keeps the serverless bundle small; Docker installs `requirements-dashboard.txt` for the full Gradio dashboard. The hosted `/` page is a browser dashboard backed by the monitoring API; `/docs` exposes the API documentation. The app automatically uses `/tmp/noise.db` and disables `SIM` and `AUTO_AGENT` when Vercel sets `VERCEL=1`. Vercel functions are request-driven, so background threads and SQLite storage are ephemeral.

## Environment variables

| Variable | Default | Purpose |
|---|---:|---|
| `PORT` | `7860` | HTTP server port |
| `DB_PATH` | `noise.db` beside the code | SQLite database location |
| `SIM` | `1` | Start the built-in sensor simulator |
| `AUTO_AGENT` | `1` | Run the agent periodically |
| `AGENT_INTERVAL` | `60` | Agent interval in seconds |
| `CAL_OFFSET` | `94` | Approximate microphone calibration offset |
| `WEBHOOK_URL` | unset | Optional escalation webhook |

## Known limits

- Phone-microphone dB(A) values are indicative only and cannot be used as legal-grade measurements.
- The `/analyze` endpoint accepts WAV uploads up to 20 MB; the browser UI also limits analysis to the first 30 seconds.

## Notes and choices

- `SIM=1` starts four generic sensor nodes and seeds 24 hours of half-hour readings. Set it to `0` to use only API/audio readings.
- Phone-microphone dB(A) values are approximate, calibrated with `CAL_OFFSET`, and are not legal-grade measurements.
- Audio accepts mono/stereo integer or float arrays in the UI, requires at least 0.5 seconds, and caps processing at 30 seconds. The HTTP endpoint accepts WAV uploads.
- The agent is deterministic and works without internet. A webhook is only contacted when `WEBHOOK_URL` is configured.
- `huggingface-hub` is pinned for stable compatibility with the selected Gradio release.

## API examples

```sh
curl http://localhost:7860/health
curl -X POST http://localhost:7860/readings -H "content-type: application/json" -d '{"zone":"Green Park","db":62}'
curl -X POST http://localhost:7860/agent/run
```
# FLEXI-Automated-Noise-Pollution-Monitoring
