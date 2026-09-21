# Architecture

```text
sim.py sensor nodes ─┐
                    ├─> FastAPI routes ─> dsp.py ─> db.py (SQLite)
Gradio mic/upload ──┘                         │
                                               v
                                      agent.py tools/actions
                                               │
                                               v
                                  Gradio dashboard, alerts, report
```

`app.py` creates one FastAPI application, installs API routes, then mounts the Gradio interface at `/`. Startup creates the database, seeds historical simulator data, and optionally starts the simulator and periodic agent threads. The standalone `python sim.py --url http://localhost:7860` mode sends the same sensor readings through the HTTP API.

The agent examines a zone's latest readings, compares the latest level with its current day/night limit, checks three-reading persistence, compares two windows for trend, and counts existing alerts. It derives `none`, `low`, `medium`, `high`, or `critical`, writes each reasoning/action record to SQLite, and escalates high/critical incidents. A webhook is optional and never required for the demo.

Audio is normalised to mono float samples, A-weighted in `dsp.py`, and capped at 30 seconds. The HTTP route accepts WAV uploads up to 20 MB and rejects invalid or shorter-than-0.5-second clips with a 422 response.
