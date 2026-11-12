#!/usr/bin/env python3
"""Explainer-video renderer (illustrated-storytelling style).
Usage: python3 render.py scenes.csv voiceover.mp3 output.mp4 [--music bg.mp3] [--subs subs.srt]
scenes.csv columns: image,start   (start = second in the voiceover where the image appears)
Each still gets a slow Ken Burns move (alternating zoom-in / zoom-out / pan), 0.3s crossfades,
and is timed to the voiceover. Output: 1920x1080, 30fps, H.264/AAC.
"""
import csv, subprocess, sys, argparse, json

W, H, FPS, XF = 1920, 1080, 30, 0.3
MOVES = [  # zoompan expressions: zoom, x, y
    ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),           # slow zoom in
    ("1.10-0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),        # slow zoom out
    ("1.08", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),                 # pan left->right
    ("1.08", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),             # pan right->left
]

def dur(path):
    out = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",path])
    return float(json.loads(out)["format"]["duration"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes"); ap.add_argument("audio"); ap.add_argument("out")
    ap.add_argument("--music"); ap.add_argument("--music_vol", type=float, default=0.08)
    ap.add_argument("--subs")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.scenes)))
    total = dur(a.audio)
    starts = [float(r["start"]) for r in rows] + [total]
    cmd, filt = ["ffmpeg","-y"], []
    for i, r in enumerate(rows):
        d = starts[i+1] - starts[i] + (XF if i < len(rows)-1 else 0)
        n = int(d * FPS)
        z, x, y = (s.format(n=n) for s in MOVES[i % len(MOVES)])
        cmd += ["-loop","1","-t",f"{d:.3f}","-i",r["image"]]
        filt.append(f"[{i}:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                    f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[v{i}]")
    last = "v0"
    for i in range(1, len(rows)):
        filt.append(f"[{last}][v{i}]xfade=transition=fade:duration={XF}:offset={starts[i]:.3f}[x{i}]")
        last = f"x{i}"
    if a.subs:
        filt.append(f"[{last}]subtitles={a.subs}:force_style='FontName=Arial,FontSize=22,Bold=1,"
                    f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,MarginV=40'[vs]"); last = "vs"
    ai = len(rows); cmd += ["-i", a.audio]
    if a.music:
        cmd += ["-stream_loop","-1","-i",a.music]
        filt.append(f"[{ai+1}:a]volume={a.music_vol}[m];[{ai}:a][m]amix=inputs=2:duration=first:normalize=0[aout]")
    else:
        filt.append(f"[{ai}:a]anull[aout]")
    cmd += ["-filter_complex",";".join(filt),"-map",f"[{last}]","-map","[aout]",
            "-c:v","libx264","-preset","medium","-crf","18","-c:a","aac","-b:a","192k",
            "-t",f"{total:.3f}","-movflags","+faststart",a.out]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
