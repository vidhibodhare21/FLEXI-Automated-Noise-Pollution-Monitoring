import numpy as np
from scipy.io import wavfile
from config import CAL_OFFSET


def clean_audio(audio):
    if not isinstance(audio, tuple) or len(audio) != 2:
        raise ValueError("audio must be a (sample_rate, array) pair")
    sr, x = audio
    if not sr or int(sr) < 1000: raise ValueError("invalid sample rate")
    x = np.asarray(x)
    if x.size == 0: raise ValueError("audio is empty")
    if x.ndim > 1: x = x.mean(axis=1)
    if np.issubdtype(x.dtype, np.integer): x = x.astype(np.float64) / max(abs(np.iinfo(x.dtype).min), np.iinfo(x.dtype).max)
    else: x = x.astype(np.float64)
    x = np.clip(x, -1, 1)
    if len(x) < sr * .5: raise ValueError("audio must be at least 0.5 seconds")
    return int(sr), x[: int(sr * 30)]


def a_weight(freq):
    f2 = np.asarray(freq, dtype=float) ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        ra = (12194**2 * f2**2) / ((f2 + 20.6**2) * np.sqrt((f2 + 107.7**2) * (f2 + 737.9**2)) * (f2 + 12194**2))
        a = 20 * np.log10(ra) + 2.0
    return np.where(np.isfinite(a), a, -100.0)


def analyze_audio(audio):
    sr, x = clean_audio(audio)
    x = x - x.mean()
    n = len(x); freq = np.fft.rfftfreq(n, 1 / sr); spec = np.abs(np.fft.rfft(x)) ** 2
    weighted = spec * 10 ** (a_weight(freq) / 10)
    rms = np.sqrt(np.sum(weighted) / max(n * n, 1))
    level = float(20 * np.log10(max(rms, 1e-12)) + CAL_OFFSET)
    total = float(spec.sum()) or 1.0
    dom = float(freq[np.argmax(spec[1:]) + 1]) if len(spec) > 1 else 0.0
    centroid = float((freq * spec).sum() / total)
    bands = [float(spec[freq < 250].sum()/total), float(spec[(freq >= 250)&(freq <= 2000)].sum()/total), float(spec[freq > 2000].sum()/total)]
    source = classify(dom, centroid, bands, level)
    return {"db": round(level, 1), "dominant_hz": round(dom, 1), "centroid_hz": round(centroid, 1), "bands": bands, "source": source, "freq": freq, "spectrum": 10*np.log10(spec + 1e-12)}


def classify(dom, centroid, bands, level=None):
    low, mid, high = bands
    if level is not None and level < 45: return "Ambient/quiet"
    if centroid < 180 and low > .55: return "Traffic/engine"
    if dom < 500 and low > .35: return "Machinery/construction"
    if mid > .55 and 200 < centroid < 1800: return "Speech/crowd"
    if dom > 300 and high + mid > .65: return "Music/loudspeaker"
    return "Ambient/quiet"


def wav_audio(data):
    import io
    return clean_audio(wavfile.read(io.BytesIO(data)))
