#!/usr/bin/env python3
"""Correct misheard words in transcript.json (keeps timings), then rewrite .txt/.srt.

    python fix_transcript.py WORK fixes.txt

fixes.txt: one rule per line, "heard phrase => correct phrase". Matching is case-insensitive on
whole words, ignoring punctuation. The corrected text is placed on the first matched word; the
other matched words are emptied (renderers skip empty words), so timings stay intact.
    Red Hearing Prospectors => Red Herring Prospectus
    ATM => Paytm
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript_io import write_outputs  # noqa: E402

norm = lambda s: re.sub(r"[^a-z0-9₹%.]", "", s.lower()).rstrip(".")  # noqa: E731


def main():
    work, rules_path = sys.argv[1], sys.argv[2]
    path = os.path.join(work, "transcript.json")
    d = json.load(open(path))
    words = d["words"]
    rules = []
    for line in open(rules_path, encoding="utf-8"):
        if "=>" in line and not line.strip().startswith("#"):
            a, b = (x.strip() for x in line.split("=>", 1))
            rules.append(([norm(t) for t in a.split()], b))
    n = 0
    for toks, repl in rules:
        i = 0
        while i <= len(words) - len(toks):
            if all(norm(words[i + k]["w"]) == toks[k] for k in range(len(toks))):
                trail = re.search(r"[.,!?;:]+$", words[i + len(toks) - 1]["w"])
                words[i]["w"] = repl + (trail.group(0) if trail and not re.search(r"[.,!?;:]$", repl) else "")
                for k in range(1, len(toks)):
                    words[i + k]["w"] = ""
                n += 1
                i += len(toks)
            else:
                i += 1
    kept = [w for w in words if w["w"]]
    for i, w in enumerate(kept):
        w["i"] = i
    write_outputs(work, kept, d.get("segments", []), source=d.get("source", "") + " +fixes")
    print(f"{n} corrections applied")


if __name__ == "__main__":
    main()
