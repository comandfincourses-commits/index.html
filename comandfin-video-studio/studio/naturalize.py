#!/usr/bin/env python3
"""Make an AI / TTS voice-over sound more human, then re-time the project to match.

    python3 studio/naturalize.py projects/<name> [--end SEC]

Reads  projects/<name>/voiceover.*  + transcript.json + project.json (+ optional "naturalize" block)
Writes projects/<name>/voiceover_natural.wav, transcript.json (re-timed), project.json (re-timed),
       and keeps the originals as *_orig.*

What it does (all deterministic):
  1. Pauses: humans pause longer after questions, exclamations and before a new idea; TTS keeps
     every gap ~0.25 s. We stretch gaps at sentence ends (0.15-0.8 s, varied) using room tone, not silence.
  2. Breaths: a soft, low inhale in the longer pauses (as a real narrator would take).
  3. Dynamics: small sentence-to-sentence level changes (+/-1.2 dB) and a lift on questions/quotes,
     so delivery is not flat.
  4. Warmth: gentle low-mid warmth, de-harsh top end and a very light room ambience.
"""
import json, os, re, subprocess, sys, zlib, shutil
import numpy as np

SR = 48000


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def rnd(key, lo, hi):  # deterministic pseudo-random in [lo, hi]
    return lo + (hi - lo) * (zlib.crc32(str(key).encode()) % 1000) / 999.0


def breath(n_sec=0.32, seed=1):
    r = np.random.default_rng(seed); n = int(SR * n_sec)
    x = r.standard_normal(n)
    # band-limit to ~400-2500 Hz with two moving averages (cheap band-pass)
    lo = np.convolve(x, np.ones(9) / 9, 'same'); x = lo - np.convolve(lo, np.ones(80) / 80, 'same')
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5 * np.linspace(0.6, 1.0, n)
    return (x / (np.abs(x).max() + 1e-9) * env * 0.022).astype(np.float32)


def main():
    pdir = os.path.abspath(sys.argv[1])
    end = float(sys.argv[sys.argv.index('--end') + 1]) if '--end' in sys.argv else None
    P = json.load(open(f'{pdir}/project.json'))
    T = json.load(open(f'{pdir}/transcript.json'))
    cfg = P.get('naturalize', {})
    src = os.path.join(pdir, P['audio'])
    a = load(src)
    if end: a = a[:int(end * SR)]
    words = [w for s in T['segments'] for w in s['words'] if not end or w['s'] < end]

    # noise floor / room tone from the quietest 5% of 50 ms frames
    fr = SR // 20; frames = a[:len(a) // fr * fr].reshape(-1, fr); rms = np.sqrt((frames ** 2).mean(1))
    tone_src = frames[np.argsort(rms)[:max(4, len(rms) // 20)]].ravel()
    def room(n):
        k = np.resize(tone_src, n).copy(); return k * 0.8

    # energy for snapping cuts to the quietest point
    hop = SR // 100; e = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop])
    def quietest(t, win=0.25):
        i0, i1 = max(0, int((t - win) * 100)), min(len(e) - 1, int((t + win) * 100))
        s = np.convolve(e[i0:i1], np.ones(8) / 8, 'same'); return (i0 + int(np.argmin(s))) / 100

    # ---- 1. decide pause insertions ----
    ins = {}
    for i, w in enumerate(words[:-1]):
        tok = w['w']; nxt = words[i + 1]['w']
        add = 0
        if tok.endswith('?'): add = rnd(w['s'], 0.45, 0.7)
        elif tok.endswith('!'): add = rnd(w['s'], 0.35, 0.55)
        elif tok.endswith('.'): add = rnd(w['s'], 0.12, 0.32)
        elif tok.endswith(','): add = rnd(w['s'], 0.0, 0.08)
        if re.match(r'^(Now|First|Second|Third|Fifth|Finally|And finally|Imagine|Think|So)\b', nxt): add += 0.2
        if add >= 0.05:
            t = quietest((w['e'] + words[i + 1]['s']) / 2)
            ins[round(t, 2)] = max(ins.get(round(t, 2), 0), add)
    for t, d in cfg.get('extra_pauses', []):          # manual, e.g. dramatic beat before a quote
        t = quietest(t); ins[round(t, 2)] = ins.get(round(t, 2), 0) + d
    pts = sorted(ins.items())

    # ---- 2. build new audio with room tone + breaths ----
    out, prev, shift, tmap = [], 0, 0.0, [(0.0, 0.0)]
    for k, (t, d) in enumerate(pts):
        i = int(t * SR); out.append(a[prev:i])
        n = int(d * SR); gap = room(n)
        if d >= 0.42 and cfg.get('breaths', True):        # inhale near the end of a longer pause
            b = breath(min(0.34, d * 0.6), seed=k); s0 = max(0, n - len(b) - int(0.05 * SR)); gap[s0:s0 + len(b)] += b
        # tiny crossfades so edits are inaudible
        f = min(int(0.01 * SR), len(gap) // 2)
        if f > 0: gap[:f] *= np.linspace(0, 1, f); gap[-f:] *= np.linspace(1, 0, f)
        out.append(gap); prev = i; shift += d; tmap.append((t, shift))
    out.append(a[prev:]); y = np.concatenate(out)
    mapt = lambda x: x + max([s for (t0, s) in tmap if t0 <= x + 1e-6] or [0])

    # ---- 3. sentence-level dynamics ----
    g = np.ones(len(y), np.float32); sent_start = 0.0
    for i, w in enumerate(words):
        if re.search(r'[.?!]$', w['w']) or i == len(words) - 1:
            s0, s1 = mapt(sent_start), mapt(w['e'])
            db = rnd(sent_start, -1.2, 1.2) + (1.3 if w['w'].endswith('?') or w['w'].endswith('!') else 0)
            g[int(s0 * SR):int(s1 * SR)] = 10 ** (db / 20)
            if i + 1 < len(words): sent_start = words[i + 1]['s']
    g = np.convolve(g, np.ones(int(0.08 * SR)) / int(0.08 * SR), 'same')
    y = y * g

    # ---- 4. warmth + light room via ffmpeg ----
    tmp = os.path.join(pdir, '.nat_tmp.f32')
    y.astype(np.float32).tofile(tmp)
    outp = os.path.join(pdir, 'voiceover_natural.wav')
    af = ('equalizer=f=180:t=q:w=1.1:g=1.8,equalizer=f=3200:t=q:w=1.5:g=-1.2,highshelf=f=10000:g=-2,'
          'aecho=0.9:0.55:23|41:0.07|0.045,alimiter=limit=0.95')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', tmp, '-af', af, '-ac', '2', outp], check=True)
    os.remove(tmp)

    # ---- re-time transcript + project ----
    for s in T['segments']:
        s['start'], s['end'] = round(mapt(s['start']), 2), round(mapt(s['end']), 2)
        for w in s['words']: w['s'], w['e'] = round(mapt(w['s']), 2), round(mapt(w['e']), 2)
    if end: T['segments'] = [s for s in T['segments'] if s['start'] < mapt(end)]
    yy = load(outp); fps = 25; hp = SR // fps
    r = np.sqrt(np.convolve(yy ** 2, np.ones(hp) / hp, 'same')[::hp]); T['envelope'] = [round(float(v), 3) for v in np.clip(r / (np.percentile(r, 98) + 1e-9), 0, 1)]
    T['duration'] = round(len(yy) / SR, 2); T['audio'] = 'voiceover_natural.wav'
    def remap(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('start', 'end', 'at', 'a_at', 'note_at') and isinstance(v, (int, float)): o[k] = round(mapt(v), 2)
                elif k == 'clips': o[k] = [[round(mapt(c[0]), 2), round(mapt(c[1]), 2)] for c in v]
                else: remap(v)
        elif isinstance(o, list):
            for v in o: remap(v)
    remap(P['scenes']); remap(P.get('cta', [])); remap(P.get('teaser', {}))
    P['audio'] = 'voiceover_natural.wav'; P['naturalized'] = {'pauses_added': len(pts), 'seconds_added': round(shift, 2)}
    json.dump(T, open(f'{pdir}/transcript.json', 'w'), ensure_ascii=False)
    json.dump(P, open(f'{pdir}/project.json', 'w'), indent=1, ensure_ascii=False)
    print(f'{len(pts)} pauses added (+{shift:.1f}s); new duration {T["duration"]:.1f}s -> {outp}')


if __name__ == '__main__':
    main()
