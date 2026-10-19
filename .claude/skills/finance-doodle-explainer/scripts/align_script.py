#!/usr/bin/env python3
"""Fallback aligner when Whisper is unavailable: script text + pause detection.

    python align_script.py WORK_DIR/voice.wav script.txt WORK_DIR [--noise -35] [--min-pause 0.28]

The script must match what was actually spoken (paragraph/sentence order). Speech is split
into voiced chunks on pauses; script sentences are mapped onto the chunks by cumulative
character length, then words are spread inside each chunk by syllable weight.
Accuracy: typically within ±0.3 s per word — good enough for kinetic text on 2–3 s shots.
Produces the same files as transcribe.py.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript_io import write_outputs  # noqa: E402


def voiced_chunks(audio, noise, min_pause):
    r = subprocess.run(["ffmpeg", "-i", audio, "-af", f"silencedetect=n={noise}dB:d={min_pause}", "-f", "null", "-"],
                       capture_output=True, text=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                "default=nk=1:nw=1", audio], capture_output=True, text=True).stdout)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    chunks, t = [], 0.0
    for s, e in zip(starts, ends + [dur] * (len(starts) - len(ends))):
        if s - t > 0.12:
            chunks.append([t, s])
        t = e
    if dur - t > 0.12:
        chunks.append([t, dur])
    return chunks, dur


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1 + len(re.sub(r"[^0-9]", "", word)) // 2  # numbers take time to say
    return max(1, len(re.findall(r"[aeiouy]+", w)) - (1 if w.endswith("e") and len(w) > 3 else 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("script")
    ap.add_argument("workdir")
    ap.add_argument("--noise", type=float, default=-35)
    ap.add_argument("--min-pause", type=float, default=0.28)
    a = ap.parse_args()

    text = open(a.script, encoding="utf-8").read()
    tokens = text.split()
    if not tokens:
        sys.exit("Script is empty")
    chunks, dur = voiced_chunks(a.audio, a.noise, a.min_pause)
    if not chunks:
        sys.exit("No speech detected — check the audio or lower --noise")

    weights = [syllables(t) + (1.2 if re.search(r"[,;:]$", t) else 0) + (2.0 if re.search(r"[.!?]$", t) else 0)
               for t in tokens]
    total_w = sum(weights)
    speech = sum(e - s for s, e in chunks)

    # Map cumulative word weight onto cumulative voiced time.
    def time_at(frac):
        target = frac * speech
        acc = 0.0
        for s, e in chunks:
            if acc + (e - s) >= target:
                return s + (target - acc)
            acc += e - s
        return chunks[-1][1]

    # Snap sentence starts to the nearest chunk start so pauses land between sentences.
    chunk_starts = [s for s, _ in chunks]
    words, acc = [], 0.0
    for i, (tok, wt) in enumerate(zip(tokens, weights)):
        st = time_at(acc / total_w)
        if i == 0 or re.search(r"[.!?]$", tokens[i - 1]):
            near = min(chunk_starts, key=lambda c: abs(c - st))
            if abs(near - st) < 0.8:
                st = near
        acc += wt
        en = time_at(acc / total_w)
        words.append({"i": i, "w": tok, "start": round(st, 3), "end": round(max(en, st + 0.05), 3)})
    for i in range(1, len(words)):
        words[i]["start"] = max(words[i]["start"], words[i - 1]["start"] + 0.02)
    segs = [{"start": s, "end": e, "text": "", "w0": None, "w1": None} for s, e in chunks]
    write_outputs(a.workdir, words, segs, source="align_script (pause-based estimate)")
    print(f"Voiced chunks: {len(chunks)}  speech {speech:.1f}s of {dur:.1f}s")


if __name__ == "__main__":
    main()
