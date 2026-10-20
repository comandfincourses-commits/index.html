#!/usr/bin/env python3
"""Original background-music generator (royalty-free by construction: every note is synthesised here).

    python music_gen.py OUT.wav --duration 300 [--bpm 96] [--seed 3] [--style upbeat|calm]

An arranged track, not a loop: intro -> verse -> chorus -> verse' -> breakdown -> chorus' -> outro,
cycling with variations until the duration is filled. Instruments: Karplus-Strong pluck (ukulele/guitar),
FM electric piano pads, sub bass, soft kick/snare/shaker, and a pentatonic lead in the choruses.
Mixed soft and warm so it sits under a voice-over. Then: mix_audio.py WORK --music OUT.wav
"""
import argparse
import subprocess

import numpy as np

SR = 48000


def env(n, a, d, sustain=0.0, rel=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * (sustain + (1 - sustain) * np.exp(-t * d))
    if rel:
        r = int(rel * SR)
        if r < n:
            e[-r:] *= np.linspace(1, 0, r)
    return e


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


class Synth:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.cache = {}

    def pluck(self, m, dur, bright=0.5):
        key = ("p", m, round(dur, 2), bright)
        if key in self.cache:
            return self.cache[key]
        n = int(dur * SR)
        p = max(2, int(round(SR / midi(m))))
        buf = self.rng.uniform(-1, 1, p)
        # pre-filter the excitation for a softer, nylon-like attack
        buf = np.convolve(buf, np.ones(3) / 3, mode="same") * (0.6 + bright * 0.4)
        out = np.empty(n)
        idx = 0
        damp = 0.4985 + 0.0012 * bright
        for i in range(n):  # Karplus-Strong
            out[i] = buf[idx]
            nxt = (idx + 1) % p
            buf[idx] = damp * (buf[idx] + buf[nxt])
            idx = nxt
        out *= env(n, 0.002, 1.2, rel=0.05)
        self.cache[key] = out
        return out

    def epiano(self, m, dur):
        key = ("e", m, round(dur, 2))
        if key in self.cache:
            return self.cache[key]
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = midi(m)
        mod = np.sin(2 * np.pi * f * 1.0 * t) * 1.6 * np.exp(-t * 3)
        s = np.sin(2 * np.pi * f * t + mod) * env(n, 0.006, 1.6, sustain=0.25, rel=0.25)
        s += 0.25 * np.sin(2 * np.pi * f * 2 * t) * env(n, 0.003, 4, rel=0.2)
        self.cache[key] = s
        return s

    def bass(self, m, dur):
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = midi(m)
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)
        return np.tanh(1.4 * s) * env(n, 0.005, 2.0, sustain=0.5, rel=0.08)

    def lead(self, m, dur):
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = midi(m)
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.25)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        s = np.sin(ph) + 0.18 * np.sin(3 * ph) + 0.08 * np.sin(5 * ph)  # soft whistle/flute
        return s * env(n, 0.03, 1.0, sustain=0.6, rel=min(0.15, dur * 0.4))

    def kick(self):
        n = int(0.32 * SR)
        t = np.arange(n) / SR
        f = 48 + 90 * np.exp(-t * 32)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 11)

    def snare(self):
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        noise = self.rng.normal(0, 1, n)
        noise = noise - np.convolve(noise, np.ones(8) / 8, mode="same")  # high-pass-ish
        return 0.55 * noise * env(n, 0.001, 24) + 0.35 * np.sin(2 * np.pi * 190 * t) * env(n, 0.001, 30)

    def shaker(self):
        n = int(0.06 * SR)
        noise = self.rng.normal(0, 1, n)
        noise = noise - np.convolve(noise, np.ones(4) / 4, mode="same")
        return noise * env(n, 0.004, 70) * 0.5


# Chord progressions (C major family), each chord = (root midi, triad offsets)
MAJ, MIN = (0, 4, 7), (0, 3, 7)
PROG = {
    "verse": [(60, MAJ), (55, MAJ), (57, MIN), (53, MAJ)],     # C G Am F
    "verse2": [(57, MIN), (53, MAJ), (60, MAJ), (55, MAJ)],    # Am F C G
    "chorus": [(53, MAJ), (60, MAJ), (55, MAJ), (57, MIN)],    # F C G Am
    "break": [(53, MAJ), (55, MAJ), (52, MIN), (57, MIN)],     # F G Em Am
}
PENTA = [0, 2, 4, 7, 9]


def place(buf, sig, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def reverb(x, mix=0.18):
    out = x.copy()
    for d, g in ((0.0297, 0.5), (0.0371, 0.45), (0.0411, 0.42), (0.0437, 0.4)):
        k = int(d * SR)
        y = np.zeros_like(x)
        for start in range(0, 6):  # few feedback taps of a comb = cheap room tail
            off = k * (start + 1)
            if off >= len(x):
                break
            y[off:] += x[:-off] * (g ** (start + 1))
        out += y * mix / 2
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--bpm", type=float, default=96)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--style", default="upbeat", choices=["upbeat", "calm"])
    a = ap.parse_args()
    sy = Synth(a.seed)
    rng = np.random.default_rng(a.seed + 11)
    beat = 60 / a.bpm
    bar = 4 * beat
    total = a.duration + 3
    n = int(total * SR)
    L = {k: np.zeros(n) for k in ("pluck", "keys", "bass", "drums", "lead")}
    form = [("intro", "verse", 4), ("verse", "verse", 8), ("chorus", "chorus", 8), ("verse2", "verse2", 8),
            ("break", "break", 4), ("chorus2", "chorus", 8)]
    kick, snare, shak = sy.kick(), sy.snare(), sy.shaker()
    t0, cycle = 0.0, 0
    patterns = [[0, 1, 2, 1, 3, 2, 1, 2], [0, 2, 1, 2, 3, 1, 2, 1], [0, 1, 2, 3, 2, 1, 0, 2]]
    while t0 < total:
        for sec, prog_name, bars in form:
            prog = PROG[prog_name]
            full = sec in ("chorus", "chorus2")
            for b in range(bars):
                tb = t0 + b * bar
                if tb >= total:
                    break
                root, tri = prog[b % 4]
                notes = [root + o for o in tri] + [root + 12]
                # pluck arpeggio (8ths), pattern varies per section/cycle
                pat = patterns[(cycle + (1 if full else 0) + b // 4) % 3]
                for k, idx in enumerate(pat):
                    if sec == "intro" and k % 2:
                        continue
                    vel = (0.9 if k % 2 == 0 else 0.62) * (1.0 if full else 0.85)
                    place(L["pluck"], sy.pluck(notes[idx] + (12 if full and k in (3, 7) else 0), 1.0, 0.6 if full else 0.4),
                          tb + k * beat / 2 + rng.uniform(-0.006, 0.006), vel)
                # keys pad: whole-bar chord (not in intro)
                if sec != "intro":
                    for m in notes[:3]:
                        place(L["keys"], sy.epiano(m + 12, bar * 1.05), tb, 0.28 if sec != "break" else 0.4)
                # bass
                if sec not in ("intro", "break"):
                    place(L["bass"], sy.bass(root - 24, beat * 1.6), tb, 0.8)
                    place(L["bass"], sy.bass(root - 24 + (7 if b % 2 else 0), beat * 0.9), tb + 2.5 * beat, 0.6)
                # drums
                if sec not in ("intro", "break") and a.style == "upbeat":
                    for q in range(4):
                        if q in (0, 2):
                            place(L["drums"], kick, tb + q * beat, 0.5)
                        if q in (1, 3):
                            place(L["drums"], snare, tb + q * beat, 0.45 if full else 0.3)
                    for e8 in range(8):
                        place(L["drums"], shak, tb + e8 * beat / 2, 0.5 if e8 % 2 else 0.3)
                    if full and b % 2:
                        place(L["drums"], kick, tb + 3.5 * beat, 0.35)
                elif sec == "break" and b == bars - 1:
                    for s16 in range(8):  # small fill into the chorus
                        place(L["drums"], snare, tb + 2 * beat + s16 * beat / 4, 0.12 + 0.05 * s16)
                # lead melody in choruses: pentatonic phrase, call/response
                if full:
                    base = 72
                    rhythm = [(0, 1.0), (1.0, 0.5), (1.5, 0.5), (2.0, 1.5)] if b % 2 == 0 else [(0, 0.5), (0.5, 0.5), (1.0, 2.0)]
                    deg = int(rng.integers(0, 3))
                    for st_, du in rhythm:
                        deg = int(np.clip(deg + rng.choice([-1, 1, 1, 2]), 0, 6))
                        m = base + PENTA[deg % 5] + 12 * (deg // 5)
                        place(L["lead"], sy.lead(m, du * beat * 0.95), tb + st_ * beat, 0.22)
            t0 += bars * bar
            if t0 >= total:
                break
        cycle += 1

    mix = (L["pluck"] * 0.55 + L["keys"] * 0.5 + L["bass"] * 0.42 + L["drums"] * 0.5 + L["lead"] * 0.45)
    mix = reverb(mix, 0.22)
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.3) * 0.8
    mix = mix[: int(a.duration * SR)]
    fi, fo = int(2.0 * SR), int(4.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo)
    st = np.stack([mix, np.concatenate([np.zeros(int(0.012 * SR)), mix[:-int(0.012 * SR)]])], axis=1).astype(np.float32)
    raw = a.out + ".f32"
    st.tofile(raw)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw,
                    "-af", "highpass=f=35,lowpass=f=12000,loudnorm=I=-18:TP=-2", "-ar", str(SR), a.out], check=True)
    import os
    os.remove(raw)
    print(f"music written: {a.out} ({a.duration:.1f}s, {a.bpm} bpm, style={a.style})")


if __name__ == "__main__":
    main()
