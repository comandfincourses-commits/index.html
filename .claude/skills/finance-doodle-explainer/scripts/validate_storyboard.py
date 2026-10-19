#!/usr/bin/env python3
"""Lint a storyboard before rendering. Errors stop the build; warnings are style advice.

    python validate_storyboard.py WORK_DIR/storyboard.json
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = open(os.path.join(HERE, "web", "library.js"), encoding="utf-8").read()
PROPS = set(re.findall(r"\n  P\.(\w+) = ", LIB))
FACES = set(re.findall(r"\n    (\w+): \{ pupil", LIB))
POSES = set(re.findall(r"\n    (\w+): \['M", LIB))
TYPES = {"character", "prop", "text", "title", "label", "card", "bubble", "arrow", "line", "bars", "linechart",
         "pie", "gauge", "counter", "table", "image", "svg"}
INS = {"pop", "fade", "grow", "slide-left", "slide-right", "slide-up", "slide-down", "drop", "wipe", "rise", "none"}
BGS = {"yellow", "cream", "white", "navy", "room", "desk", "office", "street", "night"}


def main():
    path = sys.argv[1]
    d = os.path.dirname(os.path.abspath(path))
    try:
        story = json.load(open(path, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ERROR storyboard.json is not valid JSON: {e}")
    scenes = list(story.get("scenes", []))
    for inc in story.get("include", []):
        scenes += json.load(open(os.path.join(d, inc), encoding="utf-8")).get("scenes", [])
    tr_path = os.path.join(d, "transcript.json")
    words = json.load(open(tr_path))["words"] if os.path.exists(tr_path) else []
    errs, warns = [], []

    starts = []
    for i, sc in enumerate(scenes):
        sid = sc.get("id", f"#{i + 1}")
        if "start" in sc:
            starts.append((float(sc["start"]), sid))
        elif "word" in sc:
            if not words:
                errs.append(f"{sid}: uses 'word' but no transcript.json")
            elif not (0 <= sc["word"] < len(words)):
                errs.append(f"{sid}: word {sc['word']} out of range (0-{len(words) - 1})")
            else:
                starts.append((words[sc["word"]]["start"], sid))
        else:
            errs.append(f"{sid}: needs 'start' or 'word'")
        bgs = sc.get("bg", "yellow")
        for b in (bgs if isinstance(bgs, list) else [bgs]):
            if b not in BGS and not re.match(r"^#[0-9a-fA-F]{3,8}$", str(b)):
                warns.append(f"{sid}: unknown bg '{b}' (falls back to yellow)")
        els = sc.get("elements", [])
        if not els:
            warns.append(f"{sid}: empty scene")
        for el in els:
            t = el.get("type")
            if t not in TYPES:
                errs.append(f"{sid}: unknown element type '{t}'")
                continue
            if t == "prop" and el.get("name") not in PROPS:
                errs.append(f"{sid}: unknown prop '{el.get('name')}'. Available: {', '.join(sorted(PROPS))}")
            if t == "character":
                if el.get("pose", "stand") not in POSES:
                    errs.append(f"{sid}: unknown pose '{el.get('pose')}'. Available: {', '.join(sorted(POSES))}")
                if el.get("expr", "neutral") not in FACES:
                    errs.append(f"{sid}: unknown expr '{el.get('expr')}'. Available: {', '.join(sorted(FACES))}")
            if el.get("in", "pop") not in INS:
                errs.append(f"{sid}: unknown entrance '{el.get('in')}'")
            if t in ("text", "title") and not el.get("text"):
                errs.append(f"{sid}: {t} without 'text'")
            if t == "text" and len(str(el.get("text", "")).split()) > 16:
                warns.append(f"{sid}: text has {len(el['text'].split())} words — keep on-screen text under ~12 words")
            if t in ("arrow", "line") and not (el.get("from") and el.get("to")):
                errs.append(f"{sid}: {t} needs 'from' and 'to' [x,y]")
            if t in ("bars", "linechart", "pie") and not el.get("values"):
                errs.append(f"{sid}: {t} needs 'values'")
            if t == "counter" and "to" not in el:
                errs.append(f"{sid}: counter needs 'to'")
            if t == "gauge" and "value" not in el:
                errs.append(f"{sid}: gauge needs 'value'")
            if t == "table" and not el.get("rows"):
                errs.append(f"{sid}: table needs 'rows'")
            if t == "image" and el.get("src") and not re.match(r"^(https?|file|data):", el["src"]):
                if not os.path.exists(os.path.join(d, el["src"])):
                    errs.append(f"{sid}: image not found: {el['src']}")
            for k in ("at_word", "out_word"):
                if k in el and words and not (0 <= el[k] < len(words)):
                    errs.append(f"{sid}: {k} {el[k]} out of range")
            x, y = el.get("x", 960), el.get("y", 540)
            if not (-200 <= x <= 2120 and -200 <= y <= 1280):
                warns.append(f"{sid}: element at ({x},{y}) is far off-canvas")

    starts.sort()
    dur = story.get("meta", {}).get("duration") or (words[-1]["end"] + 1 if words else None)
    if starts and dur:
        bounds = [s for s, _ in starts] + [dur]
        lens = [(bounds[i + 1] - bounds[i], starts[i][1]) for i in range(len(starts))]
        for ln, sid in lens:
            if ln < 0.6:
                warns.append(f"{sid}: very short shot ({ln:.2f}s)")
            if ln > 7:
                warns.append(f"{sid}: long shot ({ln:.1f}s) — reference style cuts every 2-3 s; split it or add builds")
        avg = sum(ln for ln, _ in lens) / len(lens)
        print(f"Scenes: {len(starts)}   avg shot {avg:.2f}s   (reference style ~2.1 s)")
        if avg > 4:
            warns.append(f"average shot {avg:.1f}s is slow for this style — aim for 2-3.5 s")
    for w in warns:
        print("WARN  " + w)
    for e in errs:
        print("ERROR " + e)
    if errs:
        sys.exit(1)
    print("Storyboard OK")


if __name__ == "__main__":
    main()
