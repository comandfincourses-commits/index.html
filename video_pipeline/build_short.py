#!/usr/bin/env python3
"""Cut a long-form explainer into a vertical YouTube Short / Reel (1080x1920, <=60s).
Inputs: the long-form scenes.csv, word timestamps (words.json from faster-whisper), the voiceover,
and a list of voiceover segments to keep. Produces: tightened voiceover, auto-remapped scenes,
vertical reframe (blurred fill + panning square panel), headline card, word-by-word captions, CTAs.
"""
import argparse, csv, json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, XF = 1080, 1920, 30, 0.25
PANEL_Y, PANEL_W, PANEL_H = 380, 1080, 1400
PAN_FROM, PAN_TO = 0.15, 0.85  # pan across the centre 70% of the scene (slower, keeps subjects in frame)
INTER = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
GAP = 0.12  # silence kept between joined segments

FIX = {"reliance": "Reliance", "reliance,": "Reliance,", "rajera.": "Raj era.", "Geo": "Jio", "Deerubhai": "Dhirubhai",
       "Command": "COMandFIN", "Finn": "", "license": "Licence", "paralyzed": "paralysed"}
HILITE = ("350", "96", "1932", "1958", "1977", "1986", "$10", "Aden", "Chorwad", "petrol", "BIG", "big,",
          "fast,", "ahead.", "today.", "public", "stroke", "Reliance", "Jamnagar", "small.", "small,", "COMandFIN")

def sh(cmd): subprocess.run(cmd, check=True)
def dur(p): return float(json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",p]))["format"]["duration"])

def build_audio(src, segs, tail, out, work):
    parts, filt = [], []
    for i, (a, b) in enumerate(segs):
        filt.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b-a-0.03:.3f}:d=0.03,apad=pad_dur={GAP}[p{i}]")
        parts.append(f"[p{i}]")
    filt.append(f"{''.join(parts)}concat=n={len(segs)}:v=0:a=1,apad=pad_dur={tail}[a]")
    sh(["ffmpeg","-v","error","-y","-i",src,"-filter_complex",";".join(filt),"-map","[a]","-ar","48000","-c:a","pcm_s16le",out])

def remap(t, segs):
    """source time -> short time (None if cut)."""
    off = 0.0
    for a, b in segs:
        if a <= t <= b: return off + (t - a)
        off += (b - a) + GAP
    return None

def scenes_for_short(rows, segs, src_total, min_len=0.7):
    starts = [float(r["start"]) for r in rows] + [src_total]
    out, off = [], 0.0
    for a, b in segs:
        for i, r in enumerate(rows):
            s, e = max(starts[i], a), min(starts[i+1], b)
            if e - s > 0.05:
                out.append([r["image"], off + (s - a), off + (e - a) + (GAP if e >= b - 1e-6 else 0), r.get("crop") or ""])
        off += (b - a) + GAP
    merged = []
    for img, s, e, c in out:  # drop slivers, merge consecutive duplicates
        if merged and (merged[-1][0] == img or e - s < min_len):
            merged[-1][2] = e; continue
        merged.append([img, s, e, c])
    return merged

def headline(path, kicker, line1, line2):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fk, fh = ImageFont.truetype(INTER, 38), ImageFont.truetype(INTER, 66)
    kw = d.textlength(kicker, font=fk)
    d.rounded_rectangle([(W-kw)/2-26, 150, (W+kw)/2+26, 212], 31, fill=(230,33,23), outline=(35,31,32), width=4)
    d.text((W/2, 181), kicker, font=fk, fill="white", anchor="mm")
    for k, t in enumerate((line1, line2)):
        d.text((W/2, 262 + k*76), t, font=fh, fill=(255,214,10) if k else "white", anchor="mm",
               stroke_width=7, stroke_fill=(20,18,18))
    im.save(path)

def clip(job):
    i, img, d, out, crop = job
    n = round(d * FPS)
    iw, ih = Image.open(img).size
    x0, x1 = (int(v) for v in crop.split("-")) if crop else (0, iw)
    cw = x1 - x0
    k = max(PANEL_W / cw, PANEL_H / ih)            # cover the panel
    sw, sh_ = int(round(cw * k / 2) * 2), int(round(ih * k / 2) * 2)
    a0, a1 = (PAN_FROM, PAN_TO) if i % 2 == 0 else (PAN_TO, PAN_FROM)
    prog = f"({a0}+({a1}-{a0})*t/{d:.3f})"
    if sw - PANEL_W >= sh_ - PANEL_H: px, py = f"(iw-{PANEL_W})*{prog}", "(ih-oh)/2"   # wide art: pan sideways
    else: px, py = "(iw-ow)/2", f"(ih-{PANEL_H})*{prog}"                              # tall art: pan down/up
    vf = (f"crop={cw}:{ih}:{x0}:0,split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.22:saturation=0.9[bg];"
          f"[b]scale={sw}:{sh_}:flags=lanczos,crop={PANEL_W}:{PANEL_H}:x='{px}':y='{py}'[fg];"
          f"[bg][fg]overlay=0:{PANEL_Y},drawbox=x=0:y={PANEL_Y}:w={W}:h=6:color=0x231F20:t=fill,"
          f"drawbox=x=0:y={PANEL_Y+PANEL_H-6}:w={W}:h=6:color=0x231F20:t=fill,format=yuv420p")
    sh(["ffmpeg","-v","error","-y","-loop","1","-framerate",str(FPS),"-t",f"{d:.3f}","-i",img,"-vf",vf,
        "-frames:v",str(n),"-c:v","libx264","-crf","14","-preset","fast",out])

def ass_time(t):
    h, m = int(t // 3600), int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def captions(words, segs, path, y=1390, per=3):
    ws = []
    for w in words:
        s, e = remap(w["s"], segs), remap(min(w["e"], w["s"] + 1.2), segs)
        if s is None: continue
        t = w["w"].strip(); t = FIX.get(t, t)
        if ws and len(t) > 1 and t[0] in ",.-" and (t[1].isdigit() or t[0] == "-"):  # "5" ",000" / "5" ".8" / "5,000" "-rupee"
            ws[-1][0] += t; ws[-1][2] = e or ws[-1][2]; continue
        if t: ws.append([t, s, e if e is not None else s + 0.3])
    lines = ["[Script Info]","ScriptType: v4.00+",f"PlayResX: {W}",f"PlayResY: {H}","",
             "[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: Cap,Inter Black,84,&H00FFFFFF,&H00FFFFFF,&H00141212,&H96000000,0,0,0,0,100,100,0,0,1,8,3,5,60,60,0,1","",
             "[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    chunks, cur = [], []
    for w in ws:  # break on punctuation or every `per` words
        cur.append(w)
        if len(cur) >= per or w[0][-1] in ".,?!": chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    for ci, ch in enumerate(chunks):
        end_chunk = chunks[ci+1][0][1] if ci + 1 < len(chunks) and chunks[ci+1][0][1] - ch[-1][2] < 0.6 else ch[-1][2] + 0.25
        for wi, w in enumerate(ch):  # active word pops in yellow
            s = w[1]; e = ch[wi+1][1] if wi + 1 < len(ch) else end_chunk
            txt = []
            for wj, x in enumerate(ch):
                word = x[0].upper()
                hot = any(x[0].startswith(h) for h in HILITE)
                if wj == wi: txt.append(r"{\c&H0AD6FF&\fscx112\fscy112}" + word + r"{\r}")
                elif hot and wj < wi: txt.append(r"{\c&H0AD6FF&}" + word + r"{\r}")
                else: txt.append(word)
            pop = r"{\pos(%d,%d)\fad(0,0)}" % (W//2, y)
            if wi == 0: pop = r"{\pos(%d,%d)\t(0,90,\fscx105\fscy105)\t(90,160,\fscx100\fscy100)}" % (W//2, y)
            lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{pop}{' '.join(txt)}")
    open(path, "w").write("\n".join(lines) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", required=True); ap.add_argument("--imgdir", required=True)
    ap.add_argument("--audio", required=True); ap.add_argument("--words", required=True)
    ap.add_argument("--segs", required=True, help="CSV of start,end source seconds to keep")
    ap.add_argument("--out", required=True); ap.add_argument("--work", default="work_short")
    ap.add_argument("--cta", action="append", default=[], help="DIR@SECONDS (time in the short)")
    ap.add_argument("--kicker", default="THE DHIRUBHAI AMBANI STORY")
    ap.add_argument("--line1", default="From a 350 sq ft room"); ap.add_argument("--line2", default="to ₹96,000 Cr profit")
    ap.add_argument("--tail", type=float, default=1.6)
    ap.add_argument("--style", help="JSON with optional 'fix' (word->replacement) and 'hilite' (word prefixes)")
    a = ap.parse_args(); os.makedirs(a.work, exist_ok=True)
    segs = [(float(r["start"]), float(r["end"])) for r in csv.DictReader(open(a.segs))]
    vo = os.path.join(a.work, "vo_short.wav"); build_audio(a.audio, segs, a.tail, vo, a.work)
    total = dur(vo)
    rows = list(csv.DictReader(open(a.scenes)))
    sc = scenes_for_short(rows, segs, dur(a.audio)); sc[-1][2] = total
    with open(os.path.join(a.work, "short_scenes.csv"), "w") as f:
        f.write("image,start,end,crop\n"); [f.write(f"{i},{s:.2f},{e:.2f},{c}\n") for i, s, e, c in sc]
    jobs = [(i, os.path.join(a.imgdir, img), (e - s) + (XF if i < len(sc) - 1 else 0), os.path.join(a.work, f"v{i:03d}.mp4"), c)
            for i, (img, s, e, c) in enumerate(sc)]
    with ThreadPoolExecutor(4) as ex: list(ex.map(clip, jobs))
    head = os.path.join(a.work, "headline.png"); headline(head, a.kicker, a.line1, a.line2)
    if a.style:
        st = json.load(open(a.style)); FIX.clear(); FIX.update(st.get("fix", {}))
        global HILITE; HILITE = tuple(st.get("hilite", HILITE))
    ass = os.path.join(a.work, "captions.ass"); captions(json.load(open(a.words)), segs, ass)
    cmd, filt = ["ffmpeg","-v","error","-stats","-y"], []
    for j in jobs: cmd += ["-i", j[3]]
    last = "0:v"
    for i in range(1, len(jobs)):
        filt.append(f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={sc[i][1]:.3f}[x{i}]"); last = f"x{i}"
    k = len(jobs); cmd += ["-loop","1","-framerate",str(FPS),"-i",head]
    filt.append(f"[{last}][{k}:v]overlay=0:0:shortest=1[h]"); last = "h"; k += 1
    filt.append(f"[{last}]ass={ass}:fontsdir=/usr/share/fonts/opentype/inter[c]"); last = "c"
    for c in a.cta:
        d, t = c.rsplit("@", 1)
        cmd += ["-framerate", str(FPS), "-itsoffset", t, "-i", os.path.join(d, "c_%04d.png")]
        filt.append(f"[{last}][{k}:v]overlay=eof_action=pass:format=auto[o{k}]"); last = f"o{k}"; k += 1
    cmd += ["-i", vo]
    filt.append(f"[{last}]fade=t=out:st={total-0.6:.3f}:d=0.6,format=yuv420p[vout]")
    filt.append(f"[{k}:a]afade=t=out:st={total-0.8:.3f}:d=0.8[aout]")
    cmd += ["-filter_complex", ";".join(filt), "-map","[vout]","-map","[aout]","-r",str(FPS),
            "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","192k","-t",f"{total:.3f}","-movflags","+faststart",a.out]
    sh(cmd)
    print(f"duration {total:.2f}s, scenes {len(sc)}")

if __name__ == "__main__":
    main()
