#!/usr/bin/env python3
"""Clean and normalise a voice-over before transcription and mixing.

    python prep_audio.py INPUT_AUDIO WORK_DIR [--denoise] [--trim]

Writes WORK_DIR/voice.wav (48 kHz mono, -16 LUFS, high-passed, optional light denoise)
and prints the duration. Accepts mp3, wav, m4a, aac, ogg, flac, or a video file (audio is extracted).
"""
import argparse
import json
import os
import subprocess
import sys


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("workdir")
    ap.add_argument("--denoise", action="store_true", help="light FFT denoise for room hiss")
    ap.add_argument("--trim", action="store_true", help="trim leading/trailing silence")
    a = ap.parse_args()

    os.makedirs(a.workdir, exist_ok=True)
    out = os.path.join(a.workdir, "voice.wav")
    filters = ["highpass=f=70", "lowpass=f=15000"]
    if a.denoise:
        filters.append("afftdn=nr=10:nf=-45")
    if a.trim:
        filters += ["silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15",
                    "areverse",
                    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.4",
                    "areverse"]
    filters += ["acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2",
                "loudnorm=I=-16:TP=-1.5:LRA=11"]
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, "-vn", "-ac", "1", "-ar", "48000",
         "-af", ",".join(filters), out])
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=nk=1:nw=1", out]).stdout.strip())
    json.dump({"voice": "voice.wav", "duration": dur}, open(os.path.join(a.workdir, "audio_info.json"), "w"), indent=1)
    print(f"voice.wav written ({dur:.2f}s) -> {out}")


if __name__ == "__main__":
    main()
