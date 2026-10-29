import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[3], device="cpu", compute_type="int8")
raw = subprocess.run(['ffmpeg','-v','error','-i',sys.argv[1],'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
audio = np.frombuffer(raw, np.float32)
segs, info = m.transcribe(audio, vad_filter=True, beam_size=5, word_timestamps=True)
out=[]
for s in segs:
    out.append({"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip(),
                "words":[[round(w.start,2),round(w.end,2),w.word] for w in (s.words or [])]})
    print(f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}", flush=True)
print("LANG", info.language, info.language_probability)
json.dump({"lang":info.language,"segments":out}, open(sys.argv[2],"w"), ensure_ascii=False, indent=1)
