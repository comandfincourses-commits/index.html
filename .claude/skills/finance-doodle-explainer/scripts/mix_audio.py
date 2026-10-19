#!/usr/bin/env python3
"""Mix voice + background music (ducked under speech) + cartoon SFX synced to the storyboard.

    python mix_audio.py WORK_DIR [--music PATH|generated|none] [--music-db -24] [--sfx-db -20] [--no-sfx]

Inputs : WORK_DIR/voice.wav, WORK_DIR/resolved_storyboard.json (written by render.cjs)
Output : WORK_DIR/mix.wav (48 kHz stereo, float)

SFX are synthesised here (no licensing issues): pop, whoosh, ding, boom, tick.
'generated' music is a light ukulele-style loop synthesised with Karplus-Strong — fine for drafts;
for production use a royalty-free track (e.g. YouTube Audio Library) via --music path.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

SR = 48000


def decode(path, channels=1):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", str(channels), "-ar", str(SR), "-"],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"Cannot decode {path}: {r.stderr.decode()[-500:]}")
    a = np.frombuffer(r.stdout, dtype=np.float32).copy()
    return a.reshape(-1, channels) if channels > 1 else a


def db(x):
    return 10 ** (x / 20)


# ---------------- SFX synthesis ----------------
def env(n, attack, decay):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t * decay)
    return e


def sfx_pop():
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    f = 950 * np.exp(-t * 18) + 260
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 38)
    s += np.random.default_rng(1).normal(0, 1, n) * env(n, 0.0005, 260) * 0.25
    return s * 0.9


def sfx_whoosh():
    n = int(0.42 * SR)
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 1, n)
    t = np.arange(n) / SR
    out = np.zeros(n)
    y = 0.0
    for i in range(n):  # time-varying one-pole low-pass: brighter in the middle
        a = 0.04 + 0.22 * np.sin(np.pi * t[i] / t[-1])
        y += a * (noise[i] - y)
        out[i] = y
    e = np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 2
    return out * e * 1.6


def sfx_ding():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1318.5 * t) + 0.45 * np.sin(2 * np.pi * 2637 * t) + 0.2 * np.sin(2 * np.pi * 3951 * t))
    return s * env(n, 0.002, 5.5) * 0.45


def sfx_boom():
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = 90 * np.exp(-t * 4) + 38
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 7)
    s += np.random.default_rng(3).normal(0, 1, n) * env(n, 0.001, 45) * 0.3
    return s


def sfx_tick():
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2200 * t) * env(n, 0.0005, 180) * 0.6


SFX = {"pop": sfx_pop, "whoosh": sfx_whoosh, "ding": sfx_ding, "boom": sfx_boom, "tick": sfx_tick}
AUTO = {"pop": "pop", "drop": "pop", "grow": "pop", "slide-left": "whoosh", "slide-right": "whoosh",
        "slide-up": "whoosh", "slide-down": "whoosh"}


def sfx_events(story):
    ev = []
    for sc in story["scenes"]:
        if isinstance(sc.get("camera"), (str, dict)):
            cam = sc["camera"] if isinstance(sc["camera"], str) else sc["camera"].get("type")
            if cam == "punch":
                ev.append((sc["start"], "whoosh", 1.0))
        if sc.get("sfx"):
            ev.append((sc["start"], sc["sfx"], 1.0))
        for el in sc.get("elements", []):
            t = sc["start"] + float(el.get("at", 0))
            if t >= sc["end"]:
                continue
            kind = el.get("sfx")
            if kind is None:
                if el.get("type") in ("text", "label", "arrow", "line", "table", "linechart"):
                    continue
                kind = AUTO.get(el.get("in", "pop"))
            if not kind or kind == "none":
                continue
            ev.append((t, kind, float(el.get("sfx_gain", 1.0))))
            if el.get("type") == "counter":
                ev.append((t + float(el.get("countDur", 1.4)), "ding", 0.8))
            if el.get("type") == "title" and el.get("sfx") is None:
                ev[-1] = (t, "boom", 0.9)
    ev.sort()
    # rate-limit: no two SFX within 0.16 s; keep the first
    kept, last = [], -9
    for t, k, g in ev:
        if t - last >= 0.16:
            kept.append((t, k, g))
            last = t
    return kept


# ---------------- generated music ----------------
def pluck(freq, dur, rng):
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * env(n, 0.002, 2.2)


def generated_music(total):
    rng = np.random.default_rng(7)
    bpm = 100
    beat = 60 / bpm
    note = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    chords = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]  # C Am F G
    bar = 4 * beat
    loop = np.zeros(int(4 * bar * SR) + SR)
    cache = {}
    for ci, ch in enumerate(chords):
        b0 = ci * bar
        pattern = [0, 2, 1, 3, 2, 1, 3, 2]
        for k, idx in enumerate(pattern):
            m = ch[idx]
            if m not in cache:
                cache[m] = pluck(note(m), 1.2, rng)
            s = int((b0 + k * beat / 2) * SR)
            seg = cache[m] * (0.9 if k % 2 == 0 else 0.6)
            loop[s:s + len(seg)] += seg[:len(loop) - s]
        # soft bass
        n = int(bar * SR)
        t = np.arange(n) / SR
        bass = np.sin(2 * np.pi * note(ch[0] - 24) * t) * env(n, 0.01, 1.5) * 0.5
        s = int(b0 * SR)
        loop[s:s + n] += bass
        # light shaker on off-beats
        for k in range(8):
            s = int((b0 + k * beat / 2 + beat / 4) * SR)
            nn = int(0.05 * SR)
            loop[s:s + nn] += rng.normal(0, 1, nn) * env(nn, 0.001, 90) * 0.06
    loop = loop[:int(4 * bar * SR)]
    reps = int(np.ceil(total * SR / len(loop)))
    m = np.tile(loop, reps)[:int(total * SR)]
    return m / (np.max(np.abs(m)) + 1e-9) * 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--music", default=None, help="path to a music file, 'generated', or 'none'")
    ap.add_argument("--music-db", type=float, default=None, help="music level vs voice (default -22)")
    ap.add_argument("--sfx-db", type=float, default=None, help="SFX level (default -17)")
    ap.add_argument("--no-sfx", action="store_true")
    a = ap.parse_args()

    story = json.load(open(os.path.join(a.workdir, "resolved_storyboard.json")))
    meta = story.get("meta", {})
    voice_path = story.get("audio") or os.path.join(a.workdir, "voice.wav")
    voice = decode(voice_path)
    total = max(len(voice) / SR, story["duration"]) + 0.5
    n = int(total * SR)
    v = np.zeros(n)
    v[:len(voice)] = voice

    music_opt = a.music if a.music is not None else meta.get("music", "generated")
    music_db = a.music_db if a.music_db is not None else meta.get("music_db", -22)
    sfx_db = a.sfx_db if a.sfx_db is not None else meta.get("sfx_db", -17)

    music = np.zeros(n)
    if music_opt and music_opt != "none":
        if music_opt == "generated":
            music = generated_music(total)
        else:
            mp = music_opt if os.path.isabs(music_opt) else os.path.join(a.workdir, music_opt)
            m = decode(mp)
            m = np.tile(m, int(np.ceil(n / len(m))))[:n]
            music = m
        # level: music RMS = (voice RMS while speaking) x music_db
        voiced = v[np.abs(v) > 0.01]
        v_rms = np.sqrt(np.mean(voiced ** 2)) if len(voiced) else 0.1
        music = music / (np.sqrt(np.mean(music ** 2)) + 1e-9) * v_rms * db(music_db)
        # fade in/out
        fi, fo = int(1.0 * SR), int(2.5 * SR)
        music[:fi] *= np.linspace(0, 1, fi)
        music[-fo:] *= np.linspace(1, 0, fo)
        # ducking from voice envelope
        hop = int(0.02 * SR)
        frames = len(v) // hop
        rms = np.sqrt(np.mean(v[:frames * hop].reshape(frames, hop) ** 2, axis=1) + 1e-12)
        speaking = (20 * np.log10(rms) > -38).astype(float)
        g = np.ones(frames)
        cur = 1.0
        for i in range(frames):
            target = 0.55 if speaking[i] else 1.0
            coef = 0.35 if target < cur else 0.04  # fast attack, slow release
            cur += coef * (target - cur)
            g[i] = cur
        gain = np.repeat(g, hop)
        gain = np.pad(gain, (0, n - len(gain)), constant_values=1.0)
        music = music * gain

    sfx = np.zeros(n)
    if not a.no_sfx and meta.get("sfx", True):
        cache = {}
        events = sfx_events(story)
        for t, k, gmul in events:
            if k not in SFX:
                continue
            if k not in cache:
                cache[k] = SFX[k]()
            s = cache[k]
            i = int(t * SR)
            if i >= n:
                continue
            sfx[i:i + len(s)] += s[:n - i] * gmul
        voiced = v[np.abs(v) > 0.01]
        v_peak = np.percentile(np.abs(voiced), 99) if len(voiced) else 0.5
        sfx *= v_peak * db(sfx_db + 6)
        print(f"SFX events: {len(events)}")

    mix = v + music + sfx
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    # subtle stereo: music/sfx slightly wider than voice
    left = v + music * 0.95 + sfx * 0.9
    right = v + music * 1.0 + sfx * 1.0
    st = np.stack([left, right], axis=1).astype(np.float32)
    st *= 0.98 / max(1e-9, np.max(np.abs(st)))
    raw = os.path.join(a.workdir, ".mix_raw.f32")
    st.tofile(raw)
    out = os.path.join(a.workdir, "mix.wav")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw,
                        "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), out], capture_output=True, text=True)
    os.remove(raw)
    if r.returncode != 0:
        sys.exit(r.stderr)
    print(f"mix.wav written ({total:.1f}s, music={music_opt}, music_db={music_db}, sfx_db={sfx_db})")


if __name__ == "__main__":
    main()
