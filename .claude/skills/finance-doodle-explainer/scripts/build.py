#!/usr/bin/env python3
"""One-command build: validate -> render frames -> mix audio -> mux -> thumbnail -> chapters.

    python build.py WORK_DIR [--draft] [--workers 4] [--music generated|none|PATH] [--no-sfx]
                    [--skip-render] [--range 0-60]

Expects WORK_DIR/storyboard.json, WORK_DIR/transcript.json, WORK_DIR/voice.wav.
Outputs in WORK_DIR/output/:
  <slug>.mp4            final 1080p H.264 + AAC (YouTube/Udemy ready, -14 LUFS)
  <slug>_thumbnail.png  if meta.thumbnail is defined
  <slug>.srt            captions
  chapters.txt          YouTube chapter list from scenes that carry "chapter"
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, **kw):
    print("$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"Step failed: {cmd[0]} {cmd[1] if len(cmd) > 1 else ''}")


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:80] or "video"


def ts(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--workers", default="4")
    ap.add_argument("--music", default=None)
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--range", default=None)
    a = ap.parse_args()
    wd = os.path.abspath(a.workdir)
    story_path = os.path.join(wd, "storyboard.json")

    run([sys.executable, os.path.join(HERE, "validate_storyboard.py"), story_path])
    video = os.path.join(wd, "video_noaudio.mp4")
    if not a.skip_render:
        cmd = ["node", os.path.join(HERE, "render.cjs"), "--story", story_path, "--out", video, "--workers", a.workers]
        if a.draft:
            cmd.append("--draft")
        if a.range:
            cmd += ["--range", a.range]
        run(cmd)

    mix_cmd = [sys.executable, os.path.join(HERE, "mix_audio.py"), wd]
    if a.music:
        mix_cmd += ["--music", a.music]
    if a.no_sfx:
        mix_cmd.append("--no-sfx")
    run(mix_cmd)

    story = json.load(open(os.path.join(wd, "resolved_storyboard.json")))
    meta = story.get("meta", {})
    name = slug(meta.get("title", "video")) + ("_DRAFT" if a.draft else "")
    out_dir = os.path.join(wd, "output")
    os.makedirs(out_dir, exist_ok=True)
    final = os.path.join(out_dir, name + ".mp4")
    audio_args = []
    if a.range:
        s, e = (float(x) for x in a.range.split("-"))
        audio_args = ["-ss", str(s), "-t", str(e - s)]
    run(["ffmpeg", "-y", "-v", "error", "-i", video] + audio_args + ["-i", os.path.join(wd, "mix.wav"),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-shortest", "-movflags", "+faststart",
         "-metadata", f"title={meta.get('title', '')}", "-metadata", f"artist={meta.get('author', '')}", final])

    if meta.get("thumbnail") and not a.draft:
        thumb = os.path.join(out_dir, name + "_thumbnail.png")
        run(["node", os.path.join(HERE, "render.cjs"), "--story", story_path, "--thumb", thumb])
        run(["ffmpeg", "-y", "-v", "error", "-i", thumb, "-vf", "scale=1280:720", thumb.replace(".png", "_1280x720.jpg")])

    srt = os.path.join(wd, "captions.srt")
    if os.path.exists(srt):
        shutil.copy(srt, os.path.join(out_dir, name + ".srt"))

    chapters = [(sc["start"], sc["chapter"]) for sc in story["scenes"] if sc.get("chapter")]
    if chapters:
        if chapters[0][0] > 0.5:
            chapters.insert(0, (0, "Introduction"))
        with open(os.path.join(out_dir, "chapters.txt"), "w") as f:
            for t, c in chapters:
                f.write(f"{ts(0 if t < 0.5 else t)} {c}\n")

    # Long-form house format: TEASER -> BRAND INTRO -> body (skipped for drafts, ranges and vertical cuts)
    src_meta = json.load(open(story_path)).get("meta", {})  # source of truth even with --skip-render
    teaser = src_meta.get("teaser")
    if teaser and not a.draft and not a.range and meta.get("width", 1920) > meta.get("height", 1080):
        body = os.path.join(wd, "body_" + os.path.basename(final))
        os.replace(final, body)
        cmd = [sys.executable, os.path.join(HERE, "assemble_long.py"), body, "--teaser", teaser, "--out", final,
               "--chapters", os.path.join(out_dir, "chapters.txt")]
        if src_meta.get("intro"):
            cmd += ["--intro", os.path.join(wd, src_meta["intro"])]
        run(cmd)

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                "default=nk=1:nw=1", final], capture_output=True, text=True).stdout or 0)
    print(f"\nDONE  {final}  ({dur / 60:.1f} min)")
    print(f"Output folder: {out_dir}")


if __name__ == "__main__":
    main()
