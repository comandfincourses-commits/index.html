#!/usr/bin/env python3
"""Two-pass builder: (1) each still -> Ken Burns clip, (2) crossfade chain + CTA overlays + voiceover.
Usage: python3 build.py scenes.csv IMAGE_DIR VOICEOVER OUT.mp4 --cta DIR@START [--cta DIR@START ...] [--tail 2.0]
"""
import argparse, csv, json, os, subprocess
from concurrent.futures import ThreadPoolExecutor

W, H, FPS, XF = 1920, 1080, 30, 0.35
MOVES = [("1.0+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
         ("1.12-0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
         ("1.10", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
         ("1.0+0.10*on/{n}", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*0.3"),
         ("1.10", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)")]

def dur(p):
    return float(json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p]))["format"]["duration"])

def clip(job):
    i, img, d, out = job
    n = round(d * FPS); z, x, y = (s.format(n=n) for s in MOVES[i % len(MOVES)])
    vf = (f"scale=3840:2160:force_original_aspect_ratio=increase:flags=lanczos,crop=3840:2160,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", img, "-vf", vf,
                    "-frames:v", str(n), "-c:v", "libx264", "-crf", "14", "-preset", "fast", out], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes"); ap.add_argument("imgdir"); ap.add_argument("audio"); ap.add_argument("out")
    ap.add_argument("--cta", action="append", default=[]); ap.add_argument("--tail", type=float, default=2.0)
    ap.add_argument("--work", default="work")
    a = ap.parse_args(); os.makedirs(a.work, exist_ok=True)
    rows = list(csv.DictReader(open(a.scenes)))
    total = dur(a.audio) + a.tail
    starts = [float(r["start"]) for r in rows] + [total]
    jobs = []
    for i, r in enumerate(rows):
        d = starts[i + 1] - starts[i] + (XF if i < len(rows) - 1 else 0)
        jobs.append((i, os.path.join(a.imgdir, r["image"]), d, os.path.join(a.work, f"s{i:03d}.mp4")))
    with ThreadPoolExecutor(4) as ex: list(ex.map(clip, jobs))
    cmd, filt = ["ffmpeg", "-v", "error", "-stats", "-y"], []
    for j in jobs: cmd += ["-i", j[3]]
    last = "0:v"
    for i in range(1, len(jobs)):
        filt.append(f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={starts[i]:.3f}[x{i}]"); last = f"x{i}"
    k = len(jobs)
    for c in a.cta:
        d, t = c.rsplit("@", 1)
        cmd += ["-framerate", str(FPS), "-itsoffset", t, "-i", os.path.join(d, "c_%04d.png")]
        filt.append(f"[{last}][{k}:v]overlay=eof_action=pass:format=auto[o{k}]"); last = f"o{k}"; k += 1
    cmd += ["-i", a.audio]
    filt.append(f"[{k}:a]apad,atrim=0:{total:.3f},afade=t=out:st={total-1.0:.3f}:d=1.0[aout]")
    filt.append(f"[{last}]fade=t=out:st={total-0.8:.3f}:d=0.8,format=yuv420p[vout]")
    cmd += ["-filter_complex", ";".join(filt), "-map", "[vout]", "-map", "[aout]", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
