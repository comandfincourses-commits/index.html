#!/usr/bin/env python3
"""Transcribe a voice-over into timed segments + approximate word timings + loudness envelope.

Usage:  python3 studio/transcribe.py projects/<name>/voiceover.(wav|mp3|m4a) [--lang en|hi]
Writes: projects/<name>/transcript.json  and  transcript.txt (human-readable, with timestamps)

Models (offline, downloaded once from GitHub releases of k2-fsa/sherpa-onnx):
  /opt/asr/sherpa-onnx-whisper-small/   Whisper small (multilingual, int8)
  /opt/asr/vad.onnx                     Silero VAD
"""
import json, os, re, subprocess, sys
import numpy as np
import sherpa_onnx

ASR = os.environ.get('ASR_DIR', '/opt/asr/sherpa-onnx-whisper-small')
VAD = os.environ.get('VAD_MODEL', '/opt/asr/vad.onnx')
SR = 16000
FPS = 25


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def vad_segments(a):
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = VAD
    cfg.silero_vad.min_silence_duration = 0.35
    cfg.silero_vad.min_speech_duration = 0.2
    cfg.silero_vad.max_speech_duration = 18
    cfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    win = cfg.silero_vad.window_size
    segs = []
    for i in range(0, len(a), win):
        vad.accept_waveform(a[i:i + win])
        while not vad.empty():
            s = vad.front; segs.append((s.start / SR, s.start / SR + len(s.samples) / SR)); vad.pop()
    vad.flush()
    while not vad.empty():
        s = vad.front; segs.append((s.start / SR, s.start / SR + len(s.samples) / SR)); vad.pop()
    return segs


def word_times(txt, a, st, en):
    """Approximate word timings. Sentences are anchored to real pauses found in the audio,
    then words inside each sentence are spread by character length."""
    seg = a[int(st * SR):int(en * SR)]
    hop = int(0.02 * SR)
    e = np.sqrt(np.convolve(seg ** 2, np.ones(hop) / hop, 'same')[::hop]) if len(seg) > hop else np.ones(1)
    quiet = e < max(1e-4, np.percentile(e, 60) * 0.12)
    gaps, i = [], 0                       # midpoints (sec) of pauses >= 0.16 s
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * 0.02 >= 0.16: gaps.append(st + (i + j) / 2 * 0.02)
            i = j
        else: i += 1
    sents = [x for x in re.split(r'(?<=[.?!,;:])\s+', txt) if x]
    lens = np.array([len(x) for x in sents], float)
    cuts = st + (en - st) * np.cumsum(lens)[:-1] / lens.sum()
    snapped, prev = [], st
    for c in cuts:                        # snap each sentence boundary to the nearest pause (within 1.2 s)
        cand = [g for g in gaps if abs(g - c) < 1.2 and g > prev + 0.2]
        c2 = min(cand, key=lambda g: abs(g - c)) if cand else c
        snapped.append(max(c2, prev + 0.2)); prev = snapped[-1]
    bounds = [st] + snapped + [en]
    out = []
    for k, sent in enumerate(sents):
        s0, s1 = bounds[k], bounds[k + 1]
        ws = sent.split(' '); wts = np.array([len(w) + 1.5 for w in ws], float); ed = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        out += [{'w': w, 's': round(s0 + (s1 - s0) * ed[i], 2), 'e': round(s0 + (s1 - s0) * ed[i + 1], 2)} for i, w in enumerate(ws)]
    return out


def apply_glossary(txt, extra=None):
    g = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glossary.json')))
    g.update(extra or {})
    for pat, rep in g.items():
        if pat.startswith('_'):
            continue
        if '\\U' in rep:
            txt = re.sub(pat, lambda m: m.group(1).upper(), txt, flags=re.I)
        else:
            txt = re.sub(pat, rep, txt, flags=re.I)
    return txt


def main():
    path = sys.argv[1]
    lang = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else 'en'
    pj = os.path.join(os.path.dirname(os.path.abspath(path)), 'glossary.json')
    extra = json.load(open(pj)) if os.path.exists(pj) else {}
    a = load(path)
    dur = len(a) / SR
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f'{ASR}/small-encoder.int8.onnx', decoder=f'{ASR}/small-decoder.int8.onnx',
        tokens=f'{ASR}/small-tokens.txt', language=lang, task='transcribe', num_threads=4)
    segs = []
    for st, en in vad_segments(a):
        s = rec.create_stream(); s.accept_waveform(SR, a[int(st * SR):int(en * SR)]); rec.decode_stream(s)
        txt = apply_glossary(re.sub(r'\s+', ' ', s.result.text).strip(), extra)
        if not txt:
            continue
        words = word_times(txt, a, st, en)
        segs.append({'start': round(st, 2), 'end': round(en, 2), 'text': txt, 'words': words})
        print(f'[{st:7.2f} – {en:7.2f}] {txt}', flush=True)
    # loudness envelope (0..1) at FPS, used to animate the presenter avatar ring
    hop = SR // FPS
    rms = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop])
    env = np.clip(rms / (np.percentile(rms, 98) + 1e-9), 0, 1)
    out = {'audio': os.path.basename(path), 'duration': round(dur, 2), 'segments': segs, 'envelope': [round(float(x), 3) for x in env]}
    d = os.path.dirname(os.path.abspath(path))
    json.dump(out, open(f'{d}/transcript.json', 'w'), ensure_ascii=False)
    with open(f'{d}/transcript.txt', 'w') as f:
        for s in segs:
            f.write(f"[{s['start']:7.2f} – {s['end']:7.2f}] {s['text']}\n")
    print(f'\nduration {dur:.1f}s, {len(segs)} segments -> {d}/transcript.json')


if __name__ == '__main__':
    main()
