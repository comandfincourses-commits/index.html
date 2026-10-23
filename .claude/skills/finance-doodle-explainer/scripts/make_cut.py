#!/usr/bin/env python3
"""Cut a Short / Reel out of a long voice-over: keeps chosen time ranges, re-times the transcript.

    python make_cut.py SRC_WORK OUT_WORK START-END [START-END ...] [--gap 0.15]

SRC_WORK must hold voice.wav + transcript.json (from the long video). Ranges are seconds in the
long video; pick them at sentence boundaries (see transcript.txt). Writes OUT_WORK/voice.wav,
transcript.json/.txt and captions.srt, ready for a 1080x1920 storyboard (meta.width/height,
meta.captions: true).
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript_io import write_outputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("ranges", nargs="+")
    ap.add_argument("--gap", type=float, default=0.15)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    words = json.load(open(os.path.join(a.src, "transcript.json")))["words"]
    rngs = [tuple(float(x) for x in r.split("-")) for r in a.ranges]
    parts, new_words, offset = [], [], 0.0
    for k, (s, e) in enumerate(rngs):
        p = os.path.join(a.out, f".part{k}.wav")
        fade = min(0.08, (e - s) / 4)
        # seek BEFORE -i so timestamps restart at 0 (fades are computed on the clip's own clock)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(s), "-to", str(e), "-i", os.path.join(a.src, "voice.wav"),
                        "-af", f"afade=t=in:d={fade},afade=t=out:st={e - s - fade}:d={fade},apad=pad_dur={a.gap}", "-ar", "48000", "-ac", "1", p], check=True)
        parts.append(p)
        for w in words:
            if w["start"] >= s - 0.02 and w["end"] <= e + 0.15:
                new_words.append({"i": len(new_words), "w": w["w"], "start": round(w["start"] - s + offset, 3), "end": round(min(w["end"], e) - s + offset, 3)})
        offset += (e - s) + a.gap
    lst = os.path.join(a.out, ".list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "pcm_s16le", os.path.join(a.out, "voice.wav")], check=True)
    for p in parts + [lst]:
        os.remove(p)
    write_outputs(a.out, new_words, [], source=f"cut of {a.src} {a.ranges}")
    print(f"cut duration {offset - a.gap:.2f}s, {len(new_words)} words")


if __name__ == "__main__":
    main()
