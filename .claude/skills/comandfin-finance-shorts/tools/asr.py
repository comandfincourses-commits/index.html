#!/usr/bin/env python3
"""Word-level speech recognition with Vosk (offline).
Usage: python3 asr.py <dir-with-srt-stub-or-""> <vosk-model-dir> in1.mkv out1.json [in2 out2 ...]
Any small English Vosk model works (e.g. vosk-model-small-en-us-0.15)."""
import sys, json, subprocess, wave
sys.path.insert(0, sys.argv[1])
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(-1)
model = Model(sys.argv[2])
for src, out in zip(sys.argv[3::2], sys.argv[4::2]):
    pcm = subprocess.run(["ffmpeg","-v","error","-i",src,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    rec = KaldiRecognizer(model, 16000); rec.SetWords(True)
    words=[]
    for i in range(0,len(pcm),8000):
        if rec.AcceptWaveform(pcm[i:i+8000]): words+=json.loads(rec.Result()).get("result",[])
    words+=json.loads(rec.FinalResult()).get("result",[])
    json.dump(words,open(out,"w"))
    print(out, len(words), " ".join(w["word"] for w in words)[:300])
