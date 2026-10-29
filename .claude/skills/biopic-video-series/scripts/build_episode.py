#!/usr/bin/env python3
"""Assemble one long-form episode (16:9, 1920x1080, 30fps).

Order:  TEASER (8-10s)  ->  COMandFIN INTRO  ->  RECAP (Part 2 onwards)  ->  STORY  ->  END CARD

usage: python3 build_episode.py episode.json
episode.json example:
{
  "series": "Rakesh Jhunjhunwala",
  "part": 2,
  "intro": "assets/Intro_Video.mp4",
  "teaser": [{"src": "scenes/s14.mp4", "start": 1.0, "dur": 3},
             {"src": "scenes/s22.mp4", "start": 0.5, "dur": 3},
             {"src": "scenes/s30.mp4", "start": 2.0, "dur": 3}],
  "recap":  [{"src": "../part1/scenes/s05.mp4", "start": 0, "dur": 8}],
  "scenes": ["scenes/s01.mp4", "scenes/s02.mp4"],
  "voiceover": "audio/part2_vo.mp3",
  "music": "audio/bgm.mp3",
  "subtitles": "audio/part2.srt",
  "output": "out/RJ_Part2.mp4"
}
"voiceover", "music", "subtitles" and "recap" are optional. Paths are relative to the json file.
Scenes may be plain paths or {"src", "start", "dur"} to cut each clip to its shot slot.
"supers": [{"at": 43.8, "dur": 3, "text": "OMAHA, NEBRASKA • 1930"}] adds top-left captions (story time).
Optional keys: "title_at" (s into the story to show the title card, default 0), "disclaimer" (default true),
"target_minutes": [8, 9], "clip_audio_volume" (default 0.15 with a voiceover),
"voiceover_delay" (s, default 0.5), "tail_seconds" (default 1.5).
With a voiceover, the story length follows the voiceover: the scene clips are cut to it (or the last frame is held).
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
NORM = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={FPS},format=yuv420p,setsar=1")
GOLD, NAVY = (214, 170, 84), (13, 27, 52)
SER = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
BLK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


def run(cmd):
    subprocess.run(cmd, check=True)


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return bool(r.stdout.strip())


def norm(src, out, start=0.0, length=None, overlay=None):
    """Re-encode any clip to the house format; adds silent audio if the clip has none."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(start)]
    if length:
        cmd += ["-t", str(length)]
    cmd += ["-i", src]
    if overlay:
        cmd += ["-loop", "1", "-i", overlay]
    if not has_audio(src):
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    a_idx = 2 if overlay else 1
    vf = f"[0:v]{NORM}[v0]"
    vf += ";[v0][1:v]overlay=0:0:shortest=1[v]" if overlay else ";[v0]null[v]"
    amap = "0:a" if has_audio(src) else f"{a_idx}:a"
    cmd += ["-filter_complex", vf, "-map", "[v]", "-map", amap, "-shortest",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-ar", "48000", "-ac", "2",
            "-c:a", "aac", "-b:a", "192k", out]
    run(cmd)


def card(path, lines, bands=()):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y0, y1, alpha in bands:  # dark gradient bands keep text readable on any footage
        for y in range(y0, y1):
            k = 1 - abs((y - y0) / max(1, y1 - y0) * 2 - 1) ** 3
            d.line([(0, y), (W, y)], fill=(8, 16, 32, int(alpha * k)))
    for text, font, size, fill, y, box in lines:
        f = ImageFont.truetype(font, size)
        w = d.textlength(text, font=f)
        x = (W - w) / 2
        if box:
            d.rounded_rectangle((x - 30, y - 10, x + w + 30, y + size + 22), 14, fill=box)
        d.text((x, y), text, font=f, fill=fill)
    im.save(path)


def main(cfg_path):
    base = os.path.dirname(os.path.abspath(cfg_path))
    cfg = json.load(open(cfg_path))
    P = lambda p: os.path.join(base, p)
    part, series = cfg["part"], cfg["series"]
    t = tempfile.mkdtemp()
    parts = []

    # Overlay graphics
    card(f"{t}/teaser.png", [("COMING UP IN THIS EPISODE", SB, 38, "white", 60, NAVY)], [(0, 200, 150)])
    card(f"{t}/recap.png", [("PREVIOUSLY ON", SB, 36, "white", 60, None),
                            (f"{series.upper()}  |  PART {part - 1}", SER, 54, GOLD, 108, None)], [(0, 260, 220)])
    card(f"{t}/title.png", [(series.upper(), SER, 110, GOLD, 420, None),
                            (f"PART {part}", BLK, 54, "white", 570, NAVY)], [(330, 700, 200)])
    card(f"{t}/end.png", [(f"PART {part + 1}  COMING NEXT", BLK, 76, GOLD, 70, None),
                          ("LIKE  •  SHARE  •  SUBSCRIBE", BLK, 54, "white", 860, (200, 30, 30)),
                          ("Turn on the bell so you don't miss the next part", SB, 34, "white", 975, None)],
         [(0, 230, 235), (820, 1080, 235)])

    # 1. Teaser (8-10 s)
    for i, c in enumerate(cfg["teaser"]):
        o = f"{t}/01_teaser_{i}.mp4"
        norm(P(c["src"]), o, c.get("start", 0), c["dur"], f"{t}/teaser.png")
        parts.append(o)
    # 2. Intro
    norm(P(cfg["intro"]), f"{t}/02_intro.mp4")
    parts.append(f"{t}/02_intro.mp4")
    # 2b. AI-dramatisation disclaimer (3.5 s)
    if cfg.get("disclaimer", True):
        dpng = f"{t}/disc.png"
        im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
        txt = ["DISCLAIMER", "", "This is a creative dramatisation produced with the help of artificial intelligence,",
               f"inspired by publicly available information on the life of {series}.",
               "Some scenes, dialogues and visuals are recreated for storytelling and educational purposes."]
        for k, line in enumerate(txt):
            f = ImageFont.truetype(BLK if k == 0 else SB, 40 if k == 0 else 30)
            w = d.textlength(line, font=f); d.text(((W - w) / 2, 400 + k * 52), line, font=f, fill="white")
        im.save(dpng)
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", "3.5", "-i", dpng, "-f", "lavfi", "-t", "3.5", "-i",
             "anullsrc=r=48000:cl=stereo", "-vf", f"fps={FPS},format=yuv420p,setsar=1", "-c:v", "libx264", "-crf", "19",
             "-c:a", "aac", "-b:a", "192k", "-shortest", f"{t}/02b_disc.mp4"])
        parts.append(f"{t}/02b_disc.mp4")
    # 3. Recap (Part 2 onwards)
    if part > 1:
        for i, c in enumerate(cfg.get("recap", [])):
            o = f"{t}/03_recap_{i}.mp4"
            norm(P(c["src"]), o, c.get("start", 0), c["dur"], f"{t}/recap.png")
            parts.append(o)
    # 4. Story: title card burned over the first 4 s of scene 1, then remaining scenes
    story = []
    for i, s in enumerate(cfg["scenes"]):
        o = f"{t}/04_scene_{i:03d}.mp4"
        if isinstance(s, dict):
            norm(P(s["src"]), o, s.get("start", 0), s.get("dur"))
        else:
            norm(P(s), o)
        story.append(o)
    # 5. End card: last 6 s of the intro with CTA overlay
    idur = dur(P(cfg["intro"]))
    norm(P(cfg["intro"]), f"{t}/05_end.mp4", max(0, idur - 6), 6, f"{t}/end.png")

    # Story block gets voiceover / music / subtitles / title overlay
    lst = f"{t}/story.txt"
    open(lst, "w").write("".join(f"file '{p}'\n" for p in story))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{t}/story_raw.mp4"])
    sd = dur(f"{t}/story_raw.mp4")
    if cfg.get("voiceover"):
        vo = dur(P(cfg["voiceover"])) + cfg.get("tail_seconds", 1.5)
        if sd < vo:
            print(f"WARNING: scenes ({sd:.1f}s) shorter than voiceover ({vo:.1f}s); holding last frame")
            run(["ffmpeg", "-v", "error", "-y", "-i", f"{t}/story_raw.mp4", "-filter_complex",
                 f"[0:v]tpad=stop_mode=clone:stop_duration={vo - sd + 0.1}[v];[0:a]apad[a]", "-map", "[v]", "-map", "[a]",
                 "-t", str(vo), "-c:v", "libx264", "-crf", "19", "-c:a", "aac", f"{t}/story_pad.mp4"])
            os.replace(f"{t}/story_pad.mp4", f"{t}/story_raw.mp4")
        sd = vo
    ta = cfg.get("title_at", 0)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", f"{t}/story_raw.mp4", "-loop", "1", "-i", f"{t}/title.png"]
    clip_vol = cfg.get("clip_audio_volume", 0.15 if cfg.get("voiceover") else 1.0)
    amix, n = [f"[0:a]volume={clip_vol}[a0]"], 1
    labels = ["[a0]"]
    sup_in = []
    for k, sp in enumerate(cfg.get("supers", [])):  # top-left location/year captions
        sp_png = f"{t}/sup{k}.png"
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        f = ImageFont.truetype(SB, 34)
        d.text((92, 82), sp["text"], font=f, fill=(0, 0, 0, 140))
        d.text((90, 80), sp["text"], font=f, fill="white")
        im.save(sp_png)
        cmd += ["-loop", "1", "-i", sp_png]
        sup_in.append((sp, 2 + k))
    idx = 2 + len(sup_in)
    if cfg.get("voiceover"):
        cmd += ["-i", P(cfg["voiceover"])]
        amix.append(f"[{idx}:a]adelay={int(cfg.get('voiceover_delay', 0.5) * 1000)}:all=1[vod]")
        amix.append("[vod]volume=1.0[vo]"); labels.append("[vo]"); idx += 1; n += 1
    if cfg.get("music"):
        cmd += ["-stream_loop", "-1", "-i", P(cfg["music"])]
        amix.append(f"[{idx}:a]volume=0.12,afade=t=out:st={sd - 3}:d=3[bg]"); labels.append("[bg]"); idx += 1; n += 1
    vf = f"[1:v]fade=t=in:st={ta}:d=0.5:alpha=1,fade=t=out:st={ta + 3.5}:d=0.5:alpha=1[tt];[0:v][tt]overlay=0:0:shortest=1:enable='between(t,{ta},{ta + 4})'[vt0]"
    last = "vt0"
    for k, (sp, ii) in enumerate(sup_in):
        a, b = sp["at"], sp["at"] + sp.get("dur", 3)
        vf += (f";[{ii}:v]fade=t=in:st={a}:d=0.4:alpha=1,fade=t=out:st={b - 0.4}:d=0.4:alpha=1[sp{k}];"
               f"[{last}][sp{k}]overlay=0:0:shortest=1:enable='between(t,{a},{b})'[vs{k}]")
        last = f"vs{k}"
    vf += f";[{last}]null[vt]"
    if cfg.get("subtitles"):
        vf += (f";[vt]subtitles='{P(cfg['subtitles'])}':force_style='FontName=Inter SemiBold,FontSize=20,"
               f"PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,MarginV=40'[v]")
    else:
        vf += ";[vt]null[v]"
    af = ";".join(amix) + f";{''.join(labels)}amix=inputs={n}:duration=first:normalize=0,alimiter=limit=0.95[a]"
    cmd += ["-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]", "-t", str(sd),
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", f"{t}/04_story.mp4"]
    run(cmd)

    final = parts + [f"{t}/04_story.mp4", f"{t}/05_end.mp4"]
    open(f"{t}/all.txt", "w").write("".join(f"file '{p}'\n" for p in final))
    out = P(cfg["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{t}/all.txt",
         "-c", "copy", "-movflags", "+faststart", out])

    total = dur(out)
    teaser = sum(c["dur"] for c in cfg["teaser"])
    print(f"Built {out}: {total / 60:.2f} min (teaser {teaser:.1f}s)")
    if not 8 <= teaser <= 10:
        print("WARNING: teaser should be 8-10 seconds")
    lo, hi = cfg.get("target_minutes", [8, 9])
    if not lo * 60 <= total <= hi * 60:
        print(f"WARNING: target is {lo}-{hi} minutes; add or trim story scenes")


if __name__ == "__main__":
    main(sys.argv[1])
