#!/usr/bin/env python3
"""Estimate final Short/Reel length from a voiceover script.

Usage:
    python3 timing_check.py script.md [--speed 1.1] [--wpm 150]

If the file contains a "## Voiceover only" section, only that section is
measured; otherwise the whole file is measured. Exits 1 if the estimated
final length at the chosen speed falls outside 60-120 seconds.
"""
import argparse
import re
import sys

MIN_S, MAX_S = 60, 120


def voiceover_text(raw: str) -> str:
    m = re.search(r"^##\s*Voiceover only.*?$(.*?)(?=^##\s|\Z)", raw, re.S | re.M | re.I)
    return m.group(1) if m else raw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--speed", type=float, default=1.1)
    p.add_argument("--wpm", type=float, default=150, help="natural pace at 1.0x")
    a = p.parse_args()

    if not 1.0 <= a.speed <= 1.2:
        print(f"Speed {a.speed}x is outside the allowed 1.0x-1.2x range.")
        return 1

    with open(a.file, encoding="utf-8") as f:
        text = voiceover_text(f.read())
    text = re.sub(r"[`*_#>|\[\]()-]", " ", text)
    words = len(re.findall(r"[\w₹%.,']+", text))

    raw_s = words / a.wpm * 60
    print(f"Words: {words} | Raw recording at 1.0x: {raw_s:.0f}s")
    for s in (1.0, 1.1, 1.2):
        final = raw_s / s
        mark = "<-- chosen" if abs(s - a.speed) < 1e-9 else ""
        ok = "OK" if MIN_S <= final <= MAX_S else "OUT OF RANGE"
        print(f"  {s:.1f}x -> {final:5.0f}s  {ok} {mark}")

    final = raw_s / a.speed
    if a.speed not in (1.0, 1.1, 1.2):
        print(f"  {a.speed:.2f}x -> {final:5.0f}s (chosen)")
    lo, hi = MIN_S / 60 * a.wpm * a.speed, MAX_S / 60 * a.wpm * a.speed
    print(f"Allowed word range at {a.speed}x: {lo:.0f}-{hi:.0f}")
    if not MIN_S <= final <= MAX_S:
        print("FAIL: trim or expand the voiceover.")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
