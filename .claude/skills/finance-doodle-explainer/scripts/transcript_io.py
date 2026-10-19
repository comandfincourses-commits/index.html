"""Shared writers for transcript.json / transcript.txt / captions.srt."""
import json
import os
import re


def _ts(t):
    h, rem = divmod(max(0.0, t), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"


def sentences(words, segs):
    """Split into sentence-like phrases on punctuation; fall back to segments."""
    out, cur = [], []
    for w in words:
        cur.append(w["i"])
        if re.search(r"[.!?;:]$", w["w"]) or len(cur) >= 22:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def write_outputs(workdir, words, segs, source=""):
    os.makedirs(workdir, exist_ok=True)
    text = " ".join(w["w"] for w in words)
    json.dump({"source": source, "text": text, "words": words, "segments": segs},
              open(os.path.join(workdir, "transcript.json"), "w"), indent=1, ensure_ascii=False)

    lines = ["# Transcript — [first-last word index] start–end  text",
             "# Use the word indices for scene \"word\" / element \"at_word\" in the storyboard.", ""]
    for idx in sentences(words, segs):
        a, b = words[idx[0]], words[idx[-1]]
        lines.append(f"[{a['i']}-{b['i']}] {a['start']:.2f}–{b['end']:.2f}  " + " ".join(f"{words[i]['w']}" for i in idx))
    lines.append("")
    lines.append("# Word index (i:word@start)")
    row = []
    for w in words:
        row.append(f"{w['i']}:{w['w']}@{w['start']:.2f}")
        if len(row) == 12:
            lines.append("  ".join(row))
            row = []
    if row:
        lines.append("  ".join(row))
    open(os.path.join(workdir, "transcript.txt"), "w").write("\n".join(lines) + "\n")

    # SRT: ~7 words / max 3.5 s per caption
    srt, chunk, n = [], [], 1
    for w in words:
        chunk.append(w)
        if len(chunk) >= 7 or re.search(r"[.!?]$", w["w"]) or (chunk[-1]["end"] - chunk[0]["start"]) > 3.5:
            srt.append(f"{n}\n{_ts(chunk[0]['start'])} --> {_ts(chunk[-1]['end'])}\n{' '.join(c['w'] for c in chunk)}\n")
            n += 1
            chunk = []
    if chunk:
        srt.append(f"{n}\n{_ts(chunk[0]['start'])} --> {_ts(chunk[-1]['end'])}\n{' '.join(c['w'] for c in chunk)}\n")
    open(os.path.join(workdir, "captions.srt"), "w").write("\n".join(srt))
    print(f"{len(words)} words -> transcript.json, transcript.txt, captions.srt in {workdir}")
