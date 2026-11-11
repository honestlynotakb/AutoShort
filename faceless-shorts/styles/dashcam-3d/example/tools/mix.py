"""Dashcam 3D soundtrack: narration + vehicular sound effects + procedural rhythm bed, all made with numpy.
No samples, no AI audio, no downloads.
  python3 tools/mix.py [project=.]          → data/mix.wav (48 kHz stereo)
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

P = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
SR = 48000
rng = np.random.default_rng(11)
cj = json.loads((P / 'data/cues.json').read_text())
script = json.loads((P / 'script.json').read_text())
DUR = float(cj['duration'])
N = int(DUR * SR) + SR // 10

def lp(x, f, o=2): b, a = signal.butter(o, min(f, SR / 2 - 100) / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f0, f1, o=2): b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def db(x): return 10 ** (x / 20)
def tt(d): return np.arange(int(d * SR)) / SR
def env(n, a=0.005, r=None):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    rest = n - na; e[na:] = np.exp(-np.linspace(0, r or 5, rest)) if rest > 0 else 1; return e
def sweep(f0, f1, d, shape='exp'):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d) if shape == 'exp' else f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def noise(d): return rng.standard_normal(int(d * SR))

# Effects
def whoosh(d=0.38, **_):
    n = noise(d); lo, hi = lp(n, 500), lp(n, 2200)
    k = np.sin(np.pi * np.linspace(0, 1, len(n))); x = (lo * (1 - k) + hi * k) * k ** 1.5
    return x / (np.abs(x).max() + 1e-9) * 0.5

def pop(**_): x = sweep(560, 240, 0.11) * env(int(0.11 * SR), 0.002, 6); return lp(x, 3000) * 0.7
def thud(**_):
    d = 0.35; t = tt(d); x = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * env(len(t), 0.002, 7)
    return x * 0.9 + lp(noise(d), 220) * env(len(t), 0.001, 12) * 0.3

def engine_rev(d=1.2, **_):
    t = tt(d); f = 55 + 85 * np.sin(np.pi * t / d) ** 1.5
    rumble = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return lp(rumble + lp(noise(d), 300) * 0.5, 400) * env(len(t), 0.1, 3) * 0.7

def tire_screech(d=0.8, **_):
    n = bp(noise(d), 1600, 3800); e = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.8
    s = sweep(2200, 1800, d) * 0.25
    return (n * 0.75 + s) * e * 0.6

def gavel_hit(**_):
    t = tt(0.2); x = np.sin(2 * np.pi * 110 * t) * env(len(t), 0.001, 10) + bp(noise(0.2), 1200, 4000) * env(len(t), 0.001, 14) * 0.6
    return x * 0.9

def beep_record(**_):
    t = tt(0.14); return np.sin(2 * np.pi * 1760 * t) * env(len(t), 0.002, 8) * 0.4

def siren_distant(d=2.0, **_):
    t = tt(d); f = 650 + 200 * np.sin(2 * np.pi * 1.2 * t)
    return lp(np.sin(2 * np.pi * np.cumsum(f) / SR), 1200) * env(len(t), 0.1, 2) * 0.25

def yell(**_):
    d = 0.4; t = tt(d); f = 340 + 120 * np.sin(np.pi * t / d)
    return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.01, 5), 1800) * 0.5

FX = dict(
    whoosh=whoosh, pop=pop, thud=thud, engine_rev=engine_rev,
    tire_screech=tire_screech, gavel_hit=gavel_hit, beep_record=beep_record,
    siren_distant=siren_distant, yell=yell
)
LEVEL = dict(
    whoosh=-17, pop=-14, thud=-11, engine_rev=-16,
    tire_screech=-15, gavel_hit=-12, beep_record=-18,
    siren_distant=-22, yell=-16
)

def music_bed():
    bpm = 110; beat = 60 / bpm; bar = beat * 4
    chords = [[220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6]]
    x = np.zeros(N)
    nb = int(np.ceil(DUR / bar)) + 1
    for b in range(nb):
        ch = chords[b % 4]; st = int(b * bar * SR); n = int(bar * SR)
        if st >= N: break
        t = tt(bar); e = np.minimum(1, t / 0.4) * np.minimum(1, (bar - t) / 0.4)
        pad = sum(np.sin(2 * np.pi * f / 2 * t) + 0.25 * np.sin(2 * np.pi * f * t) for f in ch) * e * 0.12
        x[st:st + n] += pad[:max(0, min(n, N - st))]
        for k in range(8):
            f = ch[[0, 1, 2, 1, 2, 0, 1, 2][k]] * (2 if k % 4 == 2 else 1)
            ps = st + int(k * beat / 2 * SR); pn = int(0.4 * SR)
            if ps + pn >= N: continue
            pluck = (np.sin(2 * np.pi * f * tt(0.4)) + 0.3 * np.sin(4 * np.pi * f * tt(0.4))) * env(pn, 0.003, 8) * 0.15
            x[ps:ps + pn] += pluck
    return lp(x, 3500)

# Build mix
track = np.zeros(N)
for c in cj.get('cues', []):
    t_cue = float(c['t']); fn = FX.get(c['type'])
    if not fn: continue
    sig = fn(d=float(c.get('dur', 0.5)))
    gain = db(LEVEL.get(c['type'], -16)) * float(c.get('gain', 1.0))
    st = int(t_cue * SR); en = min(N, st + len(sig))
    if st < N and en > st: track[st:en] += sig[:en - st] * gain

# Add music
bed = music_bed() * db(-18)
track += bed

# Merge narration if exists
narr_p = P / 'data/narration.wav'
if narr_p.exists():
    nsr, narr = wavfile.read(narr_p)
    if narr.ndim > 1: narr = narr.mean(axis=1)
    narr = narr.astype(float) / (np.abs(narr).max() + 1e-9)
    # Ducking
    duck = np.ones(N)
    env_narr = np.minimum(1, np.abs(lp(narr, 50)) * 4)
    duck[:min(N, len(env_narr))] = 1.0 - env_narr[:min(N, len(env_narr))] * 0.45
    track *= duck
    track[:min(N, len(narr))] += narr[:min(N, len(narr))] * 0.9

# Normalize & write
track = np.clip(track / (np.abs(track).max() + 1e-9) * 0.95, -1.0, 1.0)
out = (track * 32767).astype(np.int16)
stereo = np.column_stack([out, out])
wavfile.write(P / 'data/mix.wav', SR, stereo)
print(f"data/mix.wav: {DUR:.2f} s")
