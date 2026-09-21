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
        return """<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Noise Pollution Monitoring</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#e8eef7;background:#0b1220}
*{box-sizing:border-box}body{margin:0}.wrap{max-width:1180px;margin:auto;padding:32px 20px}
.hero{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:26px}
h1{margin:0;font-size:clamp(28px,4vw,46px);letter-spacing:-1px}.muted{color:#91a0b5}
.links a{color:#79b8ff;text-decoration:none;margin-left:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:#121d30;border:1px solid #253653;border-radius:16px;padding:20px;box-shadow:0 8px 30px #0002}
.zone{display:flex;justify-content:space-between;align-items:center}.db{font-size:30px;font-weight:700;margin:12px 0 4px}.pill{border-radius:999px;padding:5px 10px;font-size:12px;font-weight:700}.pass{background:#123d35;color:#67e8c6}.violation{background:#54262d;color:#ff9ba7}
.section{margin-top:22px}.section h2{font-size:20px;margin:0 0 12px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:11px;border-bottom:1px solid #253653;font-size:14px}th{color:#91a0b5}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}.tabs button{background:#17243a;color:#b9c8dc}.tabs button.selected{background:#3687f5;color:#fff}.hidden{display:none}.formgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:16px 0}.formgrid label{display:grid;gap:7px;color:#b9c8dc;font-size:14px}input,select{width:100%;background:#0b1220;color:#e8eef7;border:1px solid #385071;border-radius:8px;padding:10px}button{background:#3687f5;color:#fff;border:0;border-radius:9px;padding:10px 14px;font-weight:700;cursor:pointer}button:disabled{opacity:.5}.notice{padding:14px;border-radius:10px;background:#17243a;color:#b9c8dc;white-space:pre-wrap}.empty{color:#91a0b5}
@media(max-width:680px){.hero{display:block}.links{margin-top:14px}.links a{margin:0 12px 0 0}}
</style></head><body><main class="wrap">
<header class="hero"><div><div class="muted">FLEXI · LIVE OPERATIONS</div><h1>Automated Noise Pollution Monitoring</h1><p class="muted">Sensor simulator or WAV analysis → FastAPI → DSP → SQLite → autonomous agent.</p></div>
<nav class="links"><a href="/docs">API docs</a><a href="/health">Health</a></nav></header>
<nav class="tabs"><button data-tab="live">Live Dashboard</button><button data-tab="audio">Analyze Audio</button><button data-tab="agent-tab">Alerts &amp; Agent</button><button data-tab="report-tab">Report</button><button data-tab="about">About</button></nav>
<section id="live" class="panel"><section id="zones" class="grid"><div class="card empty">Loading zone readings…</div></section>
<section class="section card"><div class="zone"><h2>Recent dB(A) readings</h2><button id="refresh">Refresh</button></div><div style="overflow:auto"><table><thead><tr><th>Time</th><th>Zone</th><th>Level</th><th>Source</th></tr></thead><tbody id="readings"><tr><td colspan="4" class="empty">Loading…</td></tr></tbody></table></div></section></section>
<section id="audio" class="panel card hidden"><h2>Analyze Audio</h2><p class="muted">Upload a WAV recording to estimate dB(A), dominant frequency, source type and pass/violation status.</p><div class="formgrid"><label>WAV file<input id="audio-file" type="file" accept="audio/wav,.wav"></label><label>Zone<select id="audio-zone"><option>North Works</option><option>Market Square</option><option>Green Park</option><option>City Hospital</option></select></label><label>Time mode<select id="audio-mode"><option>Auto</option><option>Manual</option></select></label><label>Manual hour<input id="audio-hour" type="number" min="0" max="23" value="12"></label></div><button id="analyze">Analyze recording</button><div id="analysis-result" class="notice" style="margin-top:16px">Choose a WAV file to begin.</div></section>
<section id="agent-tab" class="panel card hidden"><div class="zone"><div><h2>Alerts &amp; Agent</h2><p class="muted">Run the monitoring agent against the latest readings and inspect recorded alerts.</p></div><button id="agent">Run agent now</button></div><p id="agent-result" class="muted"></p><div id="alerts" class="notice">Loading alerts…</div></section>
<section id="report-tab" class="panel card hidden"><h2>Generate Report</h2><div class="formgrid"><label>Zone<select id="report-zone"><option value="">All zones</option><option>North Works</option><option>Market Square</option><option>Green Park</option><option>City Hospital</option></select></label></div><button id="report">Generate report</button><pre id="report-result" class="notice" style="margin-top:16px;white-space:pre-wrap">Click Generate report to create an operational summary.</pre></section>
<section id="about" class="panel card hidden"><h2>About this project</h2><p>The FLEXI monitoring workflow accepts simulator or microphone/WAV readings, applies DSP-based dB(A) and source analysis, stores readings in SQLite, checks zone limits, and lets an autonomous agent produce alerts, actions and reports.</p><p class="muted">The hosted page is publicly available through Vercel. API endpoints remain available under <a href="/docs">/docs</a>.</p></section>
<script>
const $=s=>document.querySelector(s); const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.panel').forEach(p=>p.classList.add('hidden')); $('#'+b.dataset.tab).classList.remove('hidden'); document.querySelectorAll('[data-tab]').forEach(x=>x.classList.remove('selected')); b.classList.add('selected'); if(b.dataset.tab==='agent-tab') loadAlerts();});
document.querySelector('[data-tab="live"]').click();
async function load(){try{const [stats,rs]=await Promise.all([fetch('/stats').then(r=>r.json()),fetch('/readings?limit=20').then(r=>r.json())]);$('#zones').innerHTML=Object.entries(stats).map(([z,x])=>{const bad=x.max!=null&&x.max>x.limit;return `<article class="card"><div class="zone"><b>${esc(z)}</b><span class="pill ${bad?'violation':'pass'}">${bad?'VIOLATION':'PASS'}</span></div><div class="db">${x.average??'—'} <small>dB(A)</small></div><div class="muted">Limit ${x.limit} · Max ${x.max??'—'} · ${x.percent_above}% above limit</div></article>`}).join('');$('#readings').innerHTML=rs.length?rs.map(x=>`<tr><td>${esc(x.ts)}</td><td>${esc(x.zone)}</td><td>${Number(x.db).toFixed(1)} dB(A)</td><td>${esc(x.source)}</td></tr>`).join(''):'<tr><td colspan="4" class="empty">No readings yet</td></tr>'}catch(e){$('#zones').innerHTML=`<div class="notice">Unable to load dashboard data: ${esc(e.message)}</div>`}}
async function loadAlerts(){try{const as=await fetch('/alerts').then(r=>r.json());$('#alerts').innerHTML=as.length?as.slice(0,12).map(x=>`<div><b>${esc(x.severity)}</b> · ${esc(x.zone)} — ${esc(x.message)} <span class="muted">(${esc(x.ts)})</span></div>`).join(''):'<span class="empty">No alerts recorded.</span>'}catch(e){$('#alerts').textContent=e.message}}
$('#refresh').onclick=load; $('#agent').onclick=async()=>{$('#agent').disabled=true;try{const r=await fetch('/agent/run',{method:'POST'});$('#agent-result').textContent=r.ok?'Agent run completed.':'Agent request failed.';await loadAlerts();await load()}finally{$('#agent').disabled=false}};
$('#analyze').onclick=async()=>{const f=$('#audio-file').files[0];if(!f){$('#analysis-result').textContent='Please choose a WAV file.';return}const fd=new FormData();fd.append('file',f);fd.append('zone',$('#audio-zone').value);if($('#audio-mode').value==='Manual')fd.append('hour',$('#audio-hour').value);$('#analyze').disabled=true;$('#analysis-result').textContent='Analyzing recording…';try{const r=await fetch('/analyze',{method:'POST',body:fd});const x=await r.json();if(!r.ok)throw Error(x.detail||'Analysis failed');$('#analysis-result').textContent=`${x.db} dB(A) · ${x.dominant_hz} Hz · ${x.source} · limit ${x.limit} · ${x.verdict}`}catch(e){$('#analysis-result').textContent=e.message}finally{$('#analyze').disabled=false}};
$('#report').onclick=async()=>{const z=$('#report-zone').value;$('#report-result').textContent='Generating report…';const r=await fetch('/report'+(z?'?zone='+encodeURIComponent(z):''));const x=await r.json();$('#report-result').textContent=x.markdown||'No report available.'};load();loadAlerts();
</script></main></body></html>"""
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
