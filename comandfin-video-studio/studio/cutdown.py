#!/usr/bin/env python3
"""Cut a Short (or any new project) out of an existing project by joining time ranges of its voice-over.

    python3 studio/cutdown.py <src_project> <dst_project> START-END [START-END ...] [--format short]

Joins the audio ranges (short crossfades), and re-times the transcript, scenes, item cues and camera keyframes
onto the new timeline. Writes dst/voiceover.wav, transcript.json and a project.json you can then tweak.
"""
import copy, json, os, subprocess, sys
import numpy as np

SR = 48000
src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
fmt = sys.argv[sys.argv.index('--format') + 1] if '--format' in sys.argv else 'short'
ranges = [tuple(map(float, a.split('-'))) for a in sys.argv[3:] if '-' in a and a[0].isdigit()]
os.makedirs(dst, exist_ok=True)
P = json.load(open(f'{src}/project.json')); T = json.load(open(f'{src}/transcript.json'))
audio = os.path.join(src, P['audio'])
a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', audio, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)

# ---- audio ----
parts, offs, acc = [], [], 0.0
for s, e in ranges:
    seg = a[int(s * SR):int(e * SR)].copy(); f = int(0.04 * SR)
    seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
    parts.append(seg); offs.append(acc - s); acc += len(seg) / SR
    parts.append(np.zeros((int(0.25 * SR), 2), np.float32)); acc += 0.25          # a short breath between sections
y = np.concatenate(parts)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', f'{dst}/voiceover.wav'], input=y.tobytes(), check=True)

def where(t):
    for (s, e), o in zip(ranges, offs):
        if s - 1e-6 <= t <= e + 1e-6: return t + o
    return None
def clampmap(t, s, e, o): return min(max(t, s), e) + o

# ---- transcript ----
segs = []
for sg in T['segments']:
    ws = [dict(w, s=round(where(w['s']), 2), e=round(where(w['s']) + (w['e'] - w['s']), 2)) for w in sg['words'] if where(w['s']) is not None and where(w['e'] - 0.01) is not None]
    if ws: segs.append({'start': ws[0]['s'], 'end': ws[-1]['e'], 'text': ' '.join(w['w'] for w in ws), 'words': ws})
hp = SR // 25; r = np.sqrt(np.convolve(y.mean(1) ** 2, np.ones(hp) / hp, 'same')[::hp])
T2 = {'audio': 'voiceover.wav', 'duration': round(len(y) / SR, 2), 'segments': segs, 'envelope': [round(float(v), 3) for v in np.clip(r / (np.percentile(r, 98) + 1e-9), 0, 1)]}
json.dump(T2, open(f'{dst}/transcript.json', 'w'), ensure_ascii=False)

# ---- scenes ----
TIME_KEYS = ('at', 'a_at', 'note_at', 'end')
def shift(o, s, e, off):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k in TIME_KEYS and isinstance(v, (int, float)): o[k] = round(clampmap(v, s, e, off), 2)
            else: shift(v, s, e, off)
    elif isinstance(o, list):
        for v in o: shift(v, s, e, off)
rel = lambda p: os.path.relpath(os.path.join(src, p), dst) if isinstance(p, str) and not p.startswith(('/', 'http', 'file:')) else p
scenes = []
for (s, e), off in zip(ranges, offs):
    for sc in P['scenes']:
        if sc['end'] <= s or sc['start'] >= e: continue
        c = copy.deepcopy(sc); c.pop('chapter', None)
        st, en = max(sc['start'], s), min(sc['end'], e)
        body = {k: v for k, v in c.items() if k not in ('start', 'end')}
        shift(body, s, e, off)
        c = {'start': round(st + off, 2), 'end': round(en + off + (0.25 if en == e else 0), 2), **body}
        if c.get('photo'): c['photo'] = rel(c['photo'])
        for it in c.get('items', []) if isinstance(c.get('items'), list) else []:
            if isinstance(it, dict) and it.get('photo'): it['photo'] = rel(it['photo'])
        if c['type'] in ('cards',) and fmt == 'short': c['cols'] = min(c.get('cols', 2), 2)
        scenes.append(c)
P2 = {k: P[k] for k in ('theme', 'topic', 'music', 'title') if k in P}
if P2.get('music'): P2['music'] = rel(P2['music'])
P2.update({'format': fmt, 'audio': 'voiceover.wav', 'intro_mode': 'none', 'scenes': scenes, 'cta': [], 'end_segment': 'promo',
           'source': {'project': os.path.basename(src), 'ranges': ranges}})
json.dump(P2, open(f'{dst}/project.json', 'w'), indent=1, ensure_ascii=False)
print(f'{len(ranges)} ranges -> {T2["duration"]:.1f}s, {len(scenes)} scenes, {sum(len(s["words"]) for s in segs)} words -> {dst}')
print('offsets', [round(o, 2) for o in offs])
