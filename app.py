import os
import tempfile
import threading
import time
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
import gradio_client.utils as client_utils
from config import PORT, SIM, AUTO_AGENT, AGENT_INTERVAL
from db import init_db
from sim import seed, run
from agent import run_agent
from api import router

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "noise-monitor-mpl"))

schema_type = client_utils._json_schema_to_python_type


def safe_schema_type(schema, defs):
    if isinstance(schema, bool):
        return "Any"
    return schema_type(schema, defs)


client_utils._json_schema_to_python_type = safe_schema_type

@asynccontextmanager
async def life(application):
    init_db(); seed()
    if SIM: threading.Thread(target=run, daemon=True).start()
    if AUTO_AGENT:
        def loop():
            while True: time.sleep(AGENT_INTERVAL); run_agent()
        threading.Thread(target=loop, daemon=True).start()
    yield

from ui import make_ui
import gradio as gr

app = FastAPI(title="Noise Pollution Monitoring", lifespan=life)
init_db()
app.include_router(router)

app = gr.mount_gradio_app(app, make_ui(), path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
