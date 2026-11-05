#!/usr/bin/env python3
"""Align a written script (e.g. Hinglish) to its voice-over and write transcript.json with timed words.

    python3 studio/align_script.py projects/<name> [script.txt] [audio]

Use this when ASR can't transcribe the language well. Sections are split on the script's
<break time="..."/> tags and anchored to the longest pauses in the audio; inside a section,
sentence boundaries snap to real pauses and words are spread by length (see transcribe.word_times).
"""
import json, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcribe import word_times, SR, FPS  # noqa: E402

pdir = os.path.abspath(sys.argv[1])
script = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else os.path.join(pdir, 'script.txt')
P = json.load(open(os.path.join(pdir, 'project.json'))) if os.path.exists(os.path.join(pdir, 'project.json')) else {}
audio = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') and not sys.argv[2].startswith('--') else os.path.join(pdir, P.get('audio', 'voiceover.mp3'))
a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', audio, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32).copy()
dur = len(a) / SR

raw = open(script, encoding='utf-8').read()
sections = [re.sub(r'\s+', ' ', s).strip() for s in re.split(r'<break[^>]*>', raw)]
sections = [s for s in sections if s]

# pauses
hop = int(0.01 * SR); e = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop])
quiet = e < max(1e-4, np.percentile(e, 50) * 0.08)
runs, i = [], 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        runs.append((i / 100, j / 100)); i = j
    else: i += 1
speech_start = next((r[1] for r in runs if r[0] <= 0.01), 0.0)
speech_end = next((r[0] for r in reversed(runs) if r[1] >= dur - 0.02), dur)
inner = [r for r in runs if r[0] > speech_start + 0.1 and r[1] < speech_end - 0.1]

# choose section anchors: for k sections we need k-1 boundaries; pick long pauses closest to char-proportional estimates
lens = np.array([len(s) for s in sections], float)
est = speech_start + (speech_end - speech_start) * np.cumsum(lens)[:-1] / lens.sum()
long_p = sorted([r for r in inner if r[1] - r[0] >= 0.6], key=lambda r: r[0])
bounds, prev = [], speech_start
for k, t in enumerate(est):
    cand = [r for r in long_p if (r[0] + r[1]) / 2 > prev + 1.0]
    if not cand: bounds.append(t); prev = t; continue
    # prefer the longest pause within a window around the estimate, else the nearest
    win = [r for r in cand if abs((r[0] + r[1]) / 2 - t) < 25]
    best = max(win, key=lambda r: (r[1] - r[0]) - abs((r[0] + r[1]) / 2 - t) * 0.02) if win else min(cand, key=lambda r: abs((r[0] + r[1]) / 2 - t))
    bounds.append(best); prev = (best[0] + best[1]) / 2
starts = [speech_start] + [b[1] if isinstance(b, tuple) else b for b in bounds]
ends = [b[0] if isinstance(b, tuple) else b for b in bounds] + [speech_end]
if '--anchors' in sys.argv:   # explicit section start times (e.g. from an ASR pass); snap to the nearest pause
    anc = [float(x) for x in sys.argv[sys.argv.index('--anchors') + 1].split(',')]
    assert len(anc) == len(sections) - 1, f'need {len(sections)-1} anchors, got {len(anc)}'
    pz = [r for r in runs if r[1] - r[0] >= 0.1]
    starts, ends = [speech_start], []
    for t in anc:
        near = [r for r in pz if r[0] - 0.2 <= t <= r[1] + 1.5] or [min(pz, key=lambda r: abs(r[1] - t))]
        r = min(near, key=lambda r: abs(r[1] - t)); ends.append(r[0]); starts.append(r[1])
    ends.append(speech_end)

segs = []
for sec, s0, s1 in zip(sections, starts, ends):
    words = word_times(sec, a, s0, s1)
    segs.append({'start': round(s0, 2), 'end': round(s1, 2), 'text': sec, 'words': words})
    print(f'[{s0:7.2f} – {s1:7.2f}] {sec[:90]}')

hp = SR // FPS; r = np.sqrt(np.convolve(a ** 2, np.ones(hp) / hp, 'same')[::hp])
out = {'audio': os.path.basename(audio), 'duration': round(dur, 2), 'segments': segs, 'aligned_from_script': True,
       'envelope': [round(float(v), 3) for v in np.clip(r / (np.percentile(r, 98) + 1e-9), 0, 1)]}
json.dump(out, open(os.path.join(pdir, 'transcript.json'), 'w'), ensure_ascii=False)
with open(os.path.join(pdir, 'transcript.txt'), 'w') as f:
    for s in segs: f.write(f"[{s['start']:7.2f} – {s['end']:7.2f}] {s['text']}\n")
print(f'{len(segs)} sections aligned, {sum(len(s["words"]) for s in segs)} words')
