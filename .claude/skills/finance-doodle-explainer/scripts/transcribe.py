#!/usr/bin/env python3
"""Transcribe the voice-over with word-level timestamps (faster-whisper).

    python transcribe.py WORK_DIR/voice.wav WORK_DIR [--model small.en] [--language en]

Writes:
  WORK_DIR/transcript.json   {"words":[{"i","w","start","end"}], "segments":[...], "text": "..."}
  WORK_DIR/transcript.txt    numbered, time-stamped sentences for storyboard planning
  WORK_DIR/captions.srt      YouTube-ready captions

Model download needs internet access to huggingface.co (first run only). If that is not
possible, use align_script.py with your written script instead.
Model guide: small.en (fast, good) | medium.en (better accents) | large-v3 (best, slow, multilingual / Hinglish).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript_io import write_outputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("workdir")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--language", default=None, help="e.g. en, hi. Omit for auto (non-.en models)")
    ap.add_argument("--prompt", default="Finance lecture. Rupees, crore, lakh, EBITDA, NPV, IRR, SIP, EMI, CIBIL, GST, IND AS, IFRS.",
                    help="vocabulary hint for domain terms")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed. Run: pip install faster-whisper")

    try:
        model = WhisperModel(a.model, device="auto", compute_type="auto")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Could not load Whisper model '{a.model}': {e}\n"
                 "If the model cannot be downloaded (no access to huggingface.co), use:\n"
                 "  python align_script.py voice.wav script.txt WORK_DIR")
    lang = a.language or ("en" if a.model.endswith(".en") else None)
    segments, info = model.transcribe(a.audio, language=lang, word_timestamps=True, vad_filter=True,
                                      initial_prompt=a.prompt, beam_size=5)
    words, segs = [], []
    for s in segments:
        seg_words = []
        for w in s.words or []:
            token = w.word.strip()
            if not token:
                continue
            words.append({"i": len(words), "w": token, "start": round(w.start, 3), "end": round(w.end, 3)})
            seg_words.append(len(words) - 1)
        if seg_words:
            segs.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                         "w0": seg_words[0], "w1": seg_words[-1]})
        print(f"[{s.start:7.2f}] {s.text.strip()}")
    write_outputs(a.workdir, words, segs, source=f"faster-whisper {a.model}")


if __name__ == "__main__":
    main()
