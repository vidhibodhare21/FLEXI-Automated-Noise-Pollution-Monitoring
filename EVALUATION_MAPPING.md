# Evaluation mapping

| Rubric component | What was built | File(s) | Under-one-minute demo |
|---|---|---|---|
| Problem understanding and objectives | Four Indian zone limits with day/night handling | `config.py`, `README.md` | Open Live Dashboard and point to limits/status. |
| System architecture and workflow | Simulator/audio → API/DSP → SQLite → agent/UI | `docs/architecture.md`, `app.py` | Open About tab and `/docs`. |
| Agentic AI | Perceive, reason, severity decision, tool actions and trace | `agent.py`, `db.py` | Add a high reading, click Run agent now, view trace. |
| Implementation and working demo | One FastAPI process with simulator and mounted Gradio UI | `app.py`, `api.py`, `sim.py` | Run `python app.py`, visit `/health` and dashboard. |
| UI/UX | Dashboard, audio analysis, alerts, report and About tabs | `ui.py` | Record/upload audio and click Analyze. |
| Deployment readiness | Pinned dependencies, environment sample and Docker image | `Dockerfile`, `requirements.txt`, `.env.example` | Run the documented Docker command. |
| Testing | Health, reading, WAV analysis and agent-alert tests | `tests/test_basic.py` | Run `pytest -q`. |
| Documentation | Installation, safety caveat, deployment and architecture | `README.md`, `docs/architecture.md` | Read README run section and workflow diagram. |
