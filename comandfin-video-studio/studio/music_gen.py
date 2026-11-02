#!/usr/bin/env python3
"""Generate an original, royalty-free ambient corporate music bed (no samples, pure synthesis).

    python3 studio/music_gen.py assets/music_library/comandfin_bed_calm.m4a [seconds] [bpm]

Am7 – Fmaj7 – Cmaj7 – G(add9), warm pad + soft electric-piano plucks + gentle sub pulse.
Designed to sit ~20 dB under narration (make.py ducks it further under speech).
"""
import subprocess, sys
import numpy as np

SR = 48000
out = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 150; bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 84
beat = 60 / bpm; bar = 4 * beat
n = int(dur * SR); t = np.arange(n) / SR
mid = lambda m: 440 * 2 ** ((m - 69) / 12)
prog = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 55, 59, 64], [43, 50, 55, 59, 62]]   # Am7, Fmaj7, Cmaj7, G(add9)
bass = [45, 41, 36, 43]
L = np.zeros(n); R = np.zeros(n)

def adsr(length, a, d, s, r):
    e = np.ones(length) * s; A, D, Rl = int(a * SR), int(d * SR), int(r * SR)
    e[:A] = np.linspace(0, 1, max(A, 1))[:len(e[:A])]; e[A:A + D] = np.linspace(1, s, max(D, 1))[:len(e[A:A + D])]
    if Rl: e[-Rl:] *= np.linspace(1, 0, Rl)
    return e

chord_len = 2 * bar
for c in range(int(np.ceil(dur / chord_len))):
    ch = prog[c % 4]; s0 = int(c * chord_len * SR); ln = min(int((chord_len + 1.5) * SR), n - s0)
    if ln <= 0: break
    tt = np.arange(ln) / SR; env = adsr(ln, 1.2, 1.0, 0.75, 1.6)
    for k, m in enumerate(ch):                       # pad: two slightly detuned partials per note
        f = mid(m + 12)
        v = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * 1.002 * tt) + 0.5 * np.sin(2 * np.pi * f * 1.004 * tt)) * env * 0.045
        pan = 0.3 + 0.4 * (k / max(1, len(ch) - 1))
        L[s0:s0 + ln] += v * (1 - pan); R[s0:s0 + ln] += v * pan
    # sub pulse on beats 1 and 3
    for b in range(0, 8, 2):
        p0 = s0 + int(b * beat * SR); pl = min(int(beat * 1.8 * SR), n - p0)
        if pl <= 0: continue
        tp = np.arange(pl) / SR; v = np.sin(2 * np.pi * mid(bass[c % 4]) * tp) * np.exp(-tp * 2.2) * 0.09
        L[p0:p0 + pl] += v; R[p0:p0 + pl] += v
    # electric-piano plucks: arpeggio on 8ths, with gentle variation
    arp = [ch[0] + 24, ch[2] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 24, ch[1] + 12, ch[3] + 24, ch[2] + 12]
    for q in range(16):
        if (c * 16 + q) % 7 == 5: continue           # leave some gaps so it breathes
        p0 = s0 + int(q * beat / 2 * SR); pl = min(int(1.2 * SR), n - p0)
        if pl <= 0: continue
        tp = np.arange(pl) / SR; f = mid(arp[q % 8])
        v = (np.sin(2 * np.pi * f * tp) + 0.25 * np.sin(2 * np.pi * 3 * f * tp) * np.exp(-tp * 9)) * np.exp(-tp * 3.2) * 0.035 * (0.8 + 0.2 * ((q * 7) % 3) / 2)
        pan = 0.25 if q % 2 else 0.75
        L[p0:p0 + pl] += v * (1 - pan); R[p0:p0 + pl] += v * pan

x = np.stack([L, R], 1)
fade = int(2.5 * SR); x[:fade] *= np.linspace(0, 1, fade)[:, None]; x[-fade:] *= np.linspace(1, 0, fade)[:, None]
x = x / (np.abs(x).max() + 1e-9) * 0.6
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-',
                '-af', 'lowpass=f=7000,aecho=0.8:0.7:60|110:0.25|0.15,loudnorm=I=-20:TP=-3', '-ar', '48000', out],
               input=x.astype(np.float32).tobytes(), check=True)
print('music bed ->', out)
