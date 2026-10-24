#!/usr/bin/env python3
"""Transcribe a voice-over into timed segments with Whisper (sherpa-onnx) + Silero VAD.

  transcribe.py voice.wav out.json --models DIR [--lang en]

DIR holds sherpa-onnx-whisper-small/ and silero_vad.onnx, downloaded from
https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models
Output: [{"start": s, "end": e, "text": "..."}]"""
import argparse, json, os, subprocess
import numpy as np
import sherpa_onnx

SR = 16000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--models", required=True)
    ap.add_argument("--lang", default="", help="'' = auto-detect, 'en', 'hi', ...")
    a = ap.parse_args()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.audio, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    wd = os.path.join(a.models, "sherpa-onnx-whisper-small")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(wd, "small-encoder.int8.onnx"), decoder=os.path.join(wd, "small-decoder.int8.onnx"),
        tokens=os.path.join(wd, "small-tokens.txt"), language=a.lang, task="transcribe", num_threads=os.cpu_count())
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(a.models, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = 0.35
    cfg.silero_vad.max_speech_duration = 20
    cfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)
    segs = []
    win = cfg.silero_vad.window_size
    for i in range(0, len(audio), win):
        vad.accept_waveform(audio[i:i + win])
        while not vad.empty():
            segs.append((vad.front.start, list(vad.front.samples)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        segs.append((vad.front.start, list(vad.front.samples)))
        vad.pop()
    out = []
    for start, samples in segs:
        st = rec.create_stream()
        st.accept_waveform(SR, np.array(samples, np.float32))
        rec.decode_stream(st)
        text = st.result.text.strip()
        if text:
            out.append({"start": round(start / SR, 2), "end": round((start + len(samples)) / SR, 2), "text": text})
            print(f"[{out[-1]['start']:7.2f}] {text}", flush=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
