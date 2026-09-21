import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from config import ZONES, zone_limit
from db import readings, alerts, actions
from api import analyze
from agent import run_agent, generate_report
from dsp import analyze_audio


def dashboard():
    rows = []
    fig = go.Figure()
    for z in ZONES:
        rs = list(reversed(readings(z, 80))); lim = zone_limit(z)
        latest = rs[-1]["db"] if rs else None
        rows.append([z, latest, lim, "VIOLATION" if latest and latest > lim else "PASS"])
        if rs:
            fig.add_scatter(x=[r["ts"] for r in rs], y=[r["db"] for r in rs], mode="lines", name=z)
            fig.add_hline(y=lim, line_dash="dot", annotation_text=f"{z} limit")
    fig.update_layout(title="Recent dB(A) readings", yaxis_title="dB(A)", height=420)
    return pd.DataFrame(rows, columns=["Zone", "Current dB(A)", "Limit", "Status"]), fig


def audio_ui(audio, zone, mode, hour):
    h = None if mode == "Auto" else int(hour)
    result = analyze(audio, zone, h)
    raw = analyze_audio(audio)
    fig = go.Figure(go.Scatter(x=raw["freq"], y=raw["spectrum"], mode="lines"))
    fig.update_layout(title="Spectrum", xaxis_title="Hz", yaxis_title="Power (dB)", height=360)
    text = f"{result['db']} dB(A) | {result['dominant_hz']} Hz | {result['source']} | limit {result['limit']} | {result['verdict']}"
    return text, fig


def agent_ui():
    run_agent()
    return pd.DataFrame(alerts(), columns=["id","zone","severity","message","ts","resolved"]), "\n".join(f"{x['ts']} | {x['zone']} | {x['step']}: {x['detail']}" for x in actions(100))


def report_ui(zone): return generate_report(None if zone == "All zones" else zone)


def make_ui():
    with gr.Blocks(title="Noise Pollution Monitoring") as demo:
        gr.Markdown("# Automated Noise Pollution Monitoring\nLive readings use the included simulator. Phone microphone results are approximate.")
        with gr.Tab("Live Dashboard"):
            table = gr.Dataframe(headers=["Zone", "Current dB(A)", "Limit", "Status"], interactive=False)
            chart = gr.Plot()
            demo.load(dashboard, outputs=[table, chart], every=5)
        with gr.Tab("Analyze Audio"):
            audio = gr.Audio(sources=["microphone", "upload"], type="numpy", label="WAV or microphone audio")
            zone = gr.Dropdown(list(ZONES), value=list(ZONES)[0], label="Zone")
            mode = gr.Radio(["Auto", "Manual"], value="Auto", label="Time of day")
            hour = gr.Slider(0, 23, value=12, step=1, label="Manual hour")
            go = gr.Button("Analyze")
            result = gr.Textbox(label="Result")
            spectrum = gr.Plot()
            go.click(audio_ui, [audio, zone, mode, hour], [result, spectrum])
        with gr.Tab("Alerts & Agent"):
            run = gr.Button("Run agent now")
            atable = gr.Dataframe(interactive=False)
            trace = gr.Textbox(lines=14, label="Agent trace")
            run.click(agent_ui, outputs=[atable, trace])
        with gr.Tab("Report"):
            rz = gr.Dropdown(["All zones", *ZONES], value="All zones", label="Zone")
            make = gr.Button("Generate report")
            report = gr.Markdown()
            make.click(report_ui, rz, report)
        with gr.Tab("About"):
            gr.Markdown("""## Workflow
Sensor simulator or microphone/upload → FastAPI → DSP dB(A) and source classifier → SQLite → autonomous agent → alerts, escalation and report.

The agent perceives recent readings, reasons about limit margin, persistence, trend and repeat alerts, selects a severity, then records actions through its tool functions.""")
    return demo
