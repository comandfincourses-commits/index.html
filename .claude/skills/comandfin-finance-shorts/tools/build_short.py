#!/usr/bin/env python3
"""Turn raw voice recordings into an edited Short: audio edit + caption timing + scene timeline.

Usage:
    python3 build_short.py spec.json out_dir

spec.json:
{
  "id": "ipo-short-1", "speed": 1.1,
  "segments": [
    {"src": "rec1.mkv", "asr": "asr1.json", "start": 11.0, "end": 34.4,
     "text": "Corrected transcript of exactly what is spoken in this range."}
  ],
  "scenes": [{"at": "phrase that starts the scene", "type": "...", ...}],
  "end_card": {...}
}

`asr` is a Vosk word list ([{word,start,end}], see asr.py). Pauses longer than
MAX_GAP are tightened, segments are joined with SEG_GAP, then the voice is
cleaned (high-pass, FFT denoise, compression, -14 LUFS) and sped up with atempo.
Outputs voice.wav and timeline.json (captions + scenes on the final timebase).
"""
import difflib, json, os, re, subprocess, sys, wave
import numpy as np

SR = 48000
MAX_GAP = 0.32      # longest pause kept inside a segment (s, before speed-up)
SEG_GAP = 0.45      # pause inserted between segments
PAD_PRE, PAD_POST = 0.06, 0.12
END_CARD = 2.6      # seconds of end card after the voice


def load_pcm(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def islands(words, gap):
    out = []
    for w in words:
        if out and w["start"] - out[-1]["end"] <= gap:
            out[-1]["end"] = w["end"]; out[-1]["words"].append(w)
        else:
            out.append({"start": w["start"], "end": w["end"], "words": [w]})
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def align(tokens, asr):
    """Give each corrected token a (start, end) using matching ASR words; interpolate the rest."""
    a = [norm(w["word"]) for w in asr]
    b = [norm(t) for t in tokens]
    times = [None] * len(tokens)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            w = asr[blk.a + k]; times[blk.b + k] = (w["start"], w["end"])
    # anchor ends, then interpolate unmatched runs by character length
    if times[0] is None: times[0] = (asr[0]["start"], asr[0]["start"] + 0.2)
    if times[-1] is None: times[-1] = (asr[-1]["end"] - 0.2, asr[-1]["end"])
    i = 0
    while i < len(tokens):
        if times[i] is not None: i += 1; continue
        j = i
        while times[j] is None: j += 1
        t0, t1 = times[i - 1][1], times[j][0]
        lens = [len(tokens[k]) + 1 for k in range(i, j)]; tot = sum(lens); acc = 0
        for k in range(i, j):
            s = t0 + (t1 - t0) * acc / tot; acc += lens[k - i]
            times[k] = (s, t0 + (t1 - t0) * acc / tot)
        i = j
    return times


def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    speed = float(spec.get("speed", 1.1)); assert 1.0 <= speed <= 1.2
    pieces, tokens, cursor, cache = [], [], 0.0, {}
    for si, seg in enumerate(spec["segments"]):
        src = os.path.join(base, seg["src"])
        pcm = cache.setdefault(src, load_pcm(src))
        asr = [w for w in json.load(open(os.path.join(base, seg["asr"])))
               if w["start"] >= seg["start"] and w["end"] <= seg["end"]]
        if si: cursor += SEG_GAP; pieces.append(np.zeros(int(SEG_GAP * SR), np.float32))
        remap = []  # (src_start, src_end, out_start)
        for k, isl in enumerate(islands(asr, MAX_GAP)):
            s = max(isl["start"] - PAD_PRE, seg["start"]); e = min(isl["end"] + PAD_POST, seg["end"])
            if k:
                cursor += MAX_GAP * 0.6; pieces.append(np.zeros(int(MAX_GAP * 0.6 * SR), np.float32))
            clip = pcm[int(s * SR):int(e * SR)].copy()
            f = min(int(0.008 * SR), len(clip) // 2)
            clip[:f] *= np.linspace(0, 1, f); clip[-f:] *= np.linspace(1, 0, f)
            pieces.append(clip); remap.append((s, e, cursor)); cursor += len(clip) / SR
        def mp(t):
            for s, e, o in remap:
                if s <= t <= e: return o + t - s
            best = min(remap, key=lambda r: min(abs(t - r[0]), abs(t - r[1])))
            return best[2] + (0 if t < best[0] else best[1] - best[0])
        toks = seg["text"].split()
        for tok, (s, e) in zip(toks, align(toks, asr)):
            tokens.append({"w": tok, "s": mp(s) / speed, "e": mp(e) / speed, "seg": si})
    voice = np.concatenate(pieces)

    raw = os.path.join(out, "voice_raw.wav")
    with wave.open(raw, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(voice, -1, 1) * 32767).astype(np.int16).tobytes())
    chain = ("highpass=f=80,lowpass=f=14000,afftdn=nf=-28:tn=1,"
             "equalizer=f=3500:t=q:w=1.2:g=2,"
             "acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,"
             f"atempo={speed},loudnorm=I=-14:TP=-1.5:LRA=7,aresample={SR}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", chain, "-ac", "2",
                    os.path.join(out, "voice.wav")], check=True)
    voice_dur = len(voice) / SR / speed

    # caption chunks: <=4 words, break after punctuation or a pause
    chunks, cur = [], []
    for i, t in enumerate(tokens):
        cur.append(i)
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        if (len(cur) >= 4 or re.search(r"[.?!,:;]$", t["w"]) or nxt is None
                or nxt["s"] - t["e"] > 0.3 or nxt["seg"] != t["seg"]):
            chunks.append(cur); cur = []
    # merge chunks that would flash for under MIN_CAP seconds (usually mis-heard words)
    MIN_CAP = 0.45
    k = 0
    while k < len(chunks):
        c = chunks[k]
        nxt = chunks[k + 1] if k + 1 < len(chunks) else None
        dur = (tokens[nxt[0]]["s"] if nxt else tokens[c[-1]]["e"] + 0.3) - tokens[c[0]]["s"]
        if dur < MIN_CAP and nxt and tokens[nxt[0]]["seg"] == tokens[c[0]]["seg"] and len(c) + len(nxt) <= 7:
            chunks[k] = c + nxt; del chunks[k + 1]; continue
        if dur < MIN_CAP and k and len(chunks[k - 1]) + len(c) <= 7:
            chunks[k - 1] += c; del chunks[k]; k -= 1; continue
        k += 1
    caps = []
    for k, c in enumerate(chunks):
        end = tokens[chunks[k + 1][0]]["s"] if k + 1 < len(chunks) else tokens[c[-1]]["e"] + 0.3
        if end - tokens[c[-1]]["e"] > 0.6: end = tokens[c[-1]]["e"] + 0.35
        caps.append({"s": tokens[c[0]]["s"], "e": end, "words": [tokens[i] for i in c]})

    # scenes start at the first spoken token of their anchor phrase
    normtoks = [norm(t["w"]) for t in tokens]
    scenes, last = [], 0
    for sc in spec["scenes"]:
        if sc.get("at") in (None, "", "START"):
            st, idx = 0.0, 0
        else:
            ph = [norm(x) for x in sc["at"].split()]
            idx = next((i for i in range(last, len(tokens)) if normtoks[i:i + len(ph)] == ph), None)
            if idx is None: sys.exit(f"anchor not found after token {last}: {sc['at']!r}")
            st = tokens[idx]["s"] - 0.15
        sc = dict(sc, start=max(0.0, st)); last = idx
        # element anchors inside a scene
        for el in sc.get("items", []):
            if isinstance(el, dict) and el.get("at"):
                ph = [norm(x) for x in el["at"].split()]
                j = next((i for i in range(idx, len(tokens)) if normtoks[i:i + len(ph)] == ph), None)
                if j is None: sys.exit(f"item anchor not found: {el['at']!r}")
                el["t"] = round(tokens[j]["s"] - sc["start"], 3)
        scenes.append(sc)
    total = voice_dur + END_CARD
    scenes.append(dict(spec.get("end_card", {}), type="end", start=voice_dur + 0.1))
    for a, b in zip(scenes, scenes[1:] + [None]):
        a["end"] = b["start"] if b else total
    json.dump({"id": spec["id"], "duration": total, "voice_duration": voice_dur, "fps": 30,
               "theme": spec.get("theme", {}), "header": spec.get("header", {}),
               "scenes": scenes, "captions": caps}, open(os.path.join(out, "timeline.json"), "w"), indent=1)
    print(f"{spec['id']}: voice {voice_dur:.1f}s @ {speed}x, total {total:.1f}s, "
          f"{len(tokens)} words, {len(caps)} caption chunks, {len(scenes)} scenes")
    if not 60 <= total <= 120: print("WARNING: outside 60-120s")


if __name__ == "__main__":
    main()
