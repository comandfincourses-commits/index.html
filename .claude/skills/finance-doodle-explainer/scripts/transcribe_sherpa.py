#!/usr/bin/env python3
"""Alternative transcriber: sherpa-onnx + NVIDIA Parakeet-TDT (English, punctuation, word timestamps).
Use when huggingface.co (Whisper) is blocked: the model downloads from GitHub releases.

    python transcribe_sherpa.py WORK/voice.wav WORK [--model-dir DIR]

One-time model download (~480 MB):
    pip install sherpa-onnx
    curl -L -o parakeet.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
    tar xjf parakeet.tar.bz2      # -> sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/
Writes the same files as transcribe.py (transcript.json / .txt / captions.srt).
"""
import argparse
import os
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


def chunks(x, max_len=22.0, min_len=6.0):
    """Cut at the quietest 20 ms frame between min_len and max_len seconds."""
    hop = int(0.02 * SR)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    out, s = [], 0
    while s < n:
        if (n - s) * 0.02 <= max_len:
            out.append((s * hop, len(x)))
            break
        lo, hi = s + int(min_len / 0.02), s + int(max_len / 0.02)
        # smooth so we pick a real pause, not a stop consonant
        win = np.convolve(rms[lo:hi], np.ones(10) / 10, mode="same")
        cut = lo + int(np.argmin(win))
        out.append((s * hop, cut * hop))
        s = cut
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("workdir")
    ap.add_argument("--model-dir", default=os.environ.get("PARAKEET_DIR", "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"))
    a = ap.parse_args()
    try:
        import sherpa_onnx
    except ImportError:
        sys.exit("pip install sherpa-onnx")
    md = a.model_dir
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=os.path.join(md, "encoder.int8.onnx"), decoder=os.path.join(md, "decoder.int8.onnx"),
        joiner=os.path.join(md, "joiner.int8.onnx"), tokens=os.path.join(md, "tokens.txt"),
        model_type="nemo_transducer", num_threads=max(1, os.cpu_count() or 1))
    x = load(a.audio)
    words, segs = [], []
    for c0, c1 in chunks(x):
        st = rec.create_stream()
        st.accept_waveform(SR, x[c0:c1])
        rec.decode_stream(st)
        r = st.result
        off = c0 / SR
        cur = None
        w0 = len(words)
        for tok, t in zip(r.tokens, r.timestamps):
            t = off + float(t)
            if tok.startswith("▁") or tok.startswith(" ") or cur is None:
                if cur and cur["w"]:
                    words.append(cur)
                cur = {"w": tok.lstrip("▁ "), "start": round(t, 3), "end": round(t + 0.08, 3)}
            else:
                cur["w"] += tok
                cur["end"] = round(t + 0.08, 3)
        if cur and cur["w"]:
            words.append(cur)
        text = r.text.strip()
        print(f"[{off:7.2f}] {text}")
        if len(words) > w0:
            segs.append({"start": round(off, 3), "end": round(c1 / SR, 3), "text": text, "w0": w0, "w1": len(words) - 1})
    for i, w in enumerate(words):
        w["i"] = i
        if i + 1 < len(words):
            w["end"] = round(min(max(w["end"], w["start"] + 0.05), words[i + 1]["start"]), 3)
    words = [{"i": w["i"], "w": w["w"], "start": w["start"], "end": w["end"]} for w in words]
    write_outputs(a.workdir, words, segs, source="sherpa-onnx parakeet-tdt-0.6b-v2")


if __name__ == "__main__":
    main()
