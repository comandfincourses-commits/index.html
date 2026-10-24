#!/usr/bin/env python3
"""Final assembly for every long-form video: TEASER (5-10 s) -> BRAND INTRO -> MAIN VIDEO.

    python assemble_long.py MAIN.mp4 --teaser 7.7-17.4 --out FINAL.mp4
                            [--intro assets/brand/intro.mp4] [--label "COMING UP"]
                            [--chapters chapters.txt] [--description youtube_description.txt]

--teaser   seconds in MAIN.mp4 for the hook. Pick the punchiest complete sentence(s) from
           transcript.txt (a shocking number, a bold claim or a question): 5-10 s, cut on word
           boundaries. The teaser keeps the main video's visuals, voice and music and gets a
           "COMING UP" badge, then hard-cuts to the intro.
--chapters / --description  shift YouTube chapter timestamps by (teaser + intro) and prepend
           "0:00 Coming up + intro". The first chapter must last >= 10 s; teaser + intro (~17-20 s)
           satisfies that. The description file is patched in place; chapters.txt is rewritten.
Output: 1920x1080, 30 fps, H.264 (CRF 18), AAC 192 kbps 48 kHz stereo, -14 LUFS.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=nk=1:nw=1", path], capture_output=True, text=True).stdout)


def ts(t):
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def parse_ts(s):
    p = [int(x) for x in s.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


CH_RE = re.compile(r"^(\d{1,2}:\d{2}(?::\d{2})?) (.+)$")


def shift_chapters(lines, offset):
    out = ["0:00 Coming up + intro"]
    for ln in lines:
        m = CH_RE.match(ln.strip())
        if m:
            out.append(f"{ts(parse_ts(m.group(1)) + offset)} {m.group(2)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("main")
    ap.add_argument("--teaser", required=True)
    ap.add_argument("--intro", default=os.path.join(ASSETS, "brand", "intro.mp4"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="COMING UP")
    ap.add_argument("--chapters")
    ap.add_argument("--description")
    a = ap.parse_args()

    t0, t1 = (float(x) for x in a.teaser.split("-"))
    tl = t1 - t0
    if not 4.0 <= tl <= 11.0:
        print(f"WARN teaser is {tl:.1f}s; aim for 5-10 s")
    if not os.path.exists(a.intro):
        sys.exit(f"Intro not found: {a.intro}")
    il = dur(a.intro)
    font = os.path.join(ASSETS, "fonts", "LuckiestGuy.ttf")
    label = a.label.replace(":", r"\:").replace("'", "")
    norm_v = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,setsar=1,format=yuv420p"
    norm_a = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    fc = (
        f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,{norm_v},"
        f"drawtext=fontfile='{font}':text='{label}':x=56:y=48:fontsize=60:fontcolor=white:borderw=3:bordercolor=0x111111:"
        f"box=1:boxcolor=0xE53935:boxborderw=22,"
        f"drawbox=x=0:y=0:w=iw:h=ih:color=0x111111@1:t=10,"
        f"fade=t=out:st={tl - 0.2:.3f}:d=0.2[tv];"
        f"[0:a]atrim={t0}:{t1},asetpts=PTS-STARTPTS,{norm_a},afade=t=in:d=0.04,afade=t=out:st={tl - 0.25:.3f}:d=0.25[ta];"
        f"[1:v]{norm_v}[iv];[1:a]{norm_a}[ia];"
        f"[2:v]{norm_v}[mv];[2:a]{norm_a}[ma];"
        f"[tv][ta][iv][ia][mv][ma]concat=n=3:v=1:a=1[v][a0]"
    )
    mkv = a.out + ".tmp.mkv"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.main, "-i", a.intro, "-i", a.main,
                        "-filter_complex", fc, "-map", "[v]", "-map", "[a0]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-c:a", "pcm_s16le", "-ar", "48000", mkv], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])
    # two-pass loudness on the whole programme so the intro, teaser and body sit at the same level
    probe = subprocess.run(["ffmpeg", "-nostats", "-i", mkv, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(probe[probe.rindex("{"):])
    ln = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mkv, "-c:v", "copy", "-af", ln, "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", a.out], check=True)
    os.remove(mkv)

    offset = tl + il
    print(f"Assembled: teaser {tl:.1f}s + intro {il:.1f}s + main {dur(a.main):.1f}s = {dur(a.out):.1f}s -> {a.out}")
    if a.chapters and os.path.exists(a.chapters):
        lines = shift_chapters(open(a.chapters).read().splitlines(), offset)
        open(a.chapters, "w").write("\n".join(lines) + "\n")
        print("chapters.txt shifted by", round(offset, 1), "s")
    if a.description and os.path.exists(a.description):
        txt = open(a.description, encoding="utf-8").read().splitlines()
        idx = [i for i, l in enumerate(txt) if CH_RE.match(l.strip())]
        if idx:
            new = shift_chapters([txt[i] for i in idx], offset)
            txt = txt[:idx[0]] + new + txt[idx[-1] + 1:]
            open(a.description, "w", encoding="utf-8").write("\n".join(txt) + "\n")
            print("description chapters shifted by", round(offset, 1), "s")


if __name__ == "__main__":
    main()
