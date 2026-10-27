#!/usr/bin/env python3
"""Build transcript.json from a hand-written phrase script with phrase timings.
Use for Hinglish/Hindi audio where ASR spelling is unreliable but phrase timing (from
transcribe_whisper_onnx.py) is good: you write the exact Roman-script captions.

    python align_phrases.py WORK phrases.txt

phrases.txt: one phrase per line: "START-END  text as spoken"  (seconds). Words inside a phrase
are spread by length. Writes transcript.json / .txt / captions.srt.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript_io import write_outputs  # noqa: E402


def main():
    work, path = sys.argv[1], sys.argv[2]
    words, segs = [], []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*([\d.]+)\s*-\s*([\d.]+)\s+(.+)", line)
        if not m:
            continue
        s, e, text = float(m.group(1)), float(m.group(2)), m.group(3).strip()
        toks = text.split()
        wts = [max(1, len(re.sub(r"\W", "", t))) for t in toks]
        tot, acc, span, w0 = sum(wts), 0.0, (e - s) * 0.94, len(words)
        for t, wt in zip(toks, wts):
            ws = s + 0.04 + span * acc / tot
            acc += wt
            words.append({"i": len(words), "w": t, "start": round(ws, 3), "end": round(s + 0.04 + span * acc / tot, 3)})
        segs.append({"start": s, "end": e, "text": text, "w0": w0, "w1": len(words) - 1})
    write_outputs(work, words, segs, source="align_phrases (hand-written captions)")


if __name__ == "__main__":
    main()
