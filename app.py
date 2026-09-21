import os
import tempfile
import threading
import time
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from config import PORT, SIM, AUTO_AGENT, AGENT_INTERVAL
from config import ON_VERCEL
from db import init_db

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "noise-monitor-mpl"))
boot_error = None

try:
    from sim import seed, run
    from agent import run_agent
    from api import router
except Exception as error:
    if not ON_VERCEL: raise
    boot_error = f"{type(error).__name__}: {error}"

@asynccontextmanager
async def life(application):
    if boot_error:
        yield
        return
    init_db(); seed()
    if SIM: threading.Thread(target=run, daemon=True).start()
    if AUTO_AGENT:
        def loop():
            while True: time.sleep(AGENT_INTERVAL); run_agent()
        threading.Thread(target=loop, daemon=True).start()
    yield

app = FastAPI(title="Noise Pollution Monitoring", lifespan=life)
if not boot_error:
    init_db()
    app.include_router(router)

if ON_VERCEL:
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def home():
        if boot_error:
            return HTMLResponse(f"<h1>Deployment setup error</h1><pre>{boot_error}</pre>", status_code=500)
        return """<main style='font-family:system-ui;max-width:700px;margin:60px auto'>
        <h1>Automated Noise Pollution Monitoring</h1>
        <p>This serverless deployment exposes the monitoring API.</p>
        <p><a href='/docs'>Open API documentation</a> · <a href='/health'>Health check</a> · <a href='/stats'>Live statistics</a></p>
        <p>For the full live-simulator Gradio dashboard, run the Docker or local deployment described in the README.</p></main>"""
else:
    import gradio_client.utils as client_utils
    from ui import make_ui
    import gradio as gr

    schema_type = client_utils._json_schema_to_python_type

    def safe_schema_type(schema, defs):
        if isinstance(schema, bool): return "Any"
        return schema_type(schema, defs)

    client_utils._json_schema_to_python_type = safe_schema_type
    app = gr.mount_gradio_app(app, make_ui(), path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
