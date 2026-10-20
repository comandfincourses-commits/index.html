#!/usr/bin/env python3
"""Multilingual transcriber (Hindi / Hinglish / any Whisper language) via sherpa-onnx Whisper.
No huggingface.co needed: the model downloads from GitHub releases.

    python transcribe_whisper_onnx.py WORK/voice.wav WORK --model-dir DIR [--language hi] [--task transcribe]

One-time model download (~560 MB):
    pip install sherpa-onnx
    curl -L -o turbo.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2
    tar xjf turbo.tar.bz2          # -> sherpa-onnx-whisper-turbo/

How timing works: the audio is split at natural pauses into phrases of ~1.5-9 s, each phrase is
transcribed separately (exact phrase start/end), and words inside a phrase are spread by length.
Phrase-level accuracy is what matters for 2-3 s shots. Writes transcript.json / .txt / captions.srt.
Tip: --task translate gives English text for planning when the speech is Hindi.
"""
import argparse
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript_io import write_outputs  # noqa: E402

SR = 16000


def load(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode())
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def phrases(x, min_len=1.5, max_len=9.0, min_pause=0.18):
    hop = int(0.02 * SR)
    n = len(x) // hop
    db = 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
    floor = np.percentile(db, 10)
    thr = floor + 0.35 * (np.percentile(db, 90) - floor)
    voiced = np.convolve(db > thr, np.ones(5) / 5, mode="same") > 0.3
    segs, i = [], 0
    while i < n:  # voiced runs separated by pauses >= min_pause
        if voiced[i]:
            j = i
            while j < n:
                if not voiced[j]:
                    k = j
                    while k < n and not voiced[k]:
                        k += 1
                    if (k - j) * 0.02 >= min_pause or k >= n:
                        break
                    j = k
                else:
                    j += 1
            segs.append([i * 0.02, j * 0.02])
            i = j
        else:
            i += 1
    merged = []
    for s, e in segs:  # merge short bits, split long ones at their quietest frame
        if merged and (e - merged[-1][0] <= max_len) and ((merged[-1][1] - merged[-1][0]) < min_len or (s - merged[-1][1]) < 0.12):
            merged[-1][1] = e
        else:
            merged.append([s, e])
    out = []
    for s, e in merged:
        while e - s > max_len:
            a, b = int((s + max_len * 0.5) / 0.02), int((s + max_len) / 0.02)
            cut = (a + int(np.argmin(db[a:b]))) * 0.02
            out.append([s, cut])
            s = cut
        out.append([s, e])
    return [(max(0, s - 0.08), min(len(x) / SR, e + 0.12)) for s, e in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("workdir")
    ap.add_argument("--model-dir", default=os.environ.get("WHISPER_ONNX_DIR", "sherpa-onnx-whisper-turbo"))
    ap.add_argument("--language", default="hi")
    ap.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    a = ap.parse_args()
    import sherpa_onnx
    md = a.model_dir
    pre = next((f.split("-encoder")[0] for f in os.listdir(md) if f.endswith("-encoder.int8.onnx")), None)
    if not pre:
        sys.exit(f"No *-encoder.int8.onnx in {md}")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(md, f"{pre}-encoder.int8.onnx"), decoder=os.path.join(md, f"{pre}-decoder.int8.onnx"),
        tokens=os.path.join(md, f"{pre}-tokens.txt"), language=a.language, task=a.task,
        num_threads=max(1, os.cpu_count() or 1))
    x = load(a.audio)
    words, segs = [], []
    for s, e in phrases(x):
        st = rec.create_stream()
        st.accept_waveform(SR, np.concatenate([x[int(s * SR):int(e * SR)], np.zeros(int(0.3 * SR), np.float32)]))
        rec.decode_stream(st)
        text = st.result.text.strip()
        # drop Whisper hallucinations on near-silence
        if not text or re.fullmatch(r"[\W_]*", text) or text.lower() in {"thank you.", "you", "thanks for watching!"}:
            continue
        toks = text.split()
        weights = [max(1, len(re.sub(r"\W", "", t))) for t in toks]
        tot, acc = sum(weights), 0.0
        span = (e - s) * 0.94
        w0 = len(words)
        for t, wt in zip(toks, weights):
            ws = s + 0.04 + span * acc / tot
            acc += wt
            words.append({"i": len(words), "w": t, "start": round(ws, 3), "end": round(s + 0.04 + span * acc / tot, 3)})
        segs.append({"start": round(s, 3), "end": round(e, 3), "text": text, "w0": w0, "w1": len(words) - 1})
        print(f"[{s:7.2f}-{e:7.2f}] {text}", flush=True)
    write_outputs(a.workdir, words, segs, source=f"sherpa-onnx whisper ({pre}, {a.language}, {a.task})")


if __name__ == "__main__":
    main()
