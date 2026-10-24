#!/usr/bin/env python3
"""Robotic placeholder voice (eSpeak NG) for testing timing before the real
voice-over arrives. Usage: placeholder_voice.py script.txt|spec.json out.wav"""
import ctypes, sys, wave
import espeakng_loader as el

def synth(text, out, voice=b"en-us", rate=165):
    lib = ctypes.CDLL(el.get_library_path())
    sr = lib.espeak_Initialize(1, 0, el.get_data_path().encode(), 0)  # AUDIO_OUTPUT_RETRIEVAL
    lib.espeak_SetVoiceByName(voice)
    lib.espeak_SetParameter(1, rate, 0)  # espeakRATE
    chunks = []
    CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
    def cb(wav, n, events):
        if n > 0:
            chunks.append(ctypes.string_at(wav, n * 2))
        return 0
    cbf = CB(cb)
    lib.espeak_SetSynthCallback(cbf)
    data = text.encode("utf-8")
    lib.espeak_Synth(data, len(data) + 1, 0, 0, 0, 0x1, None, None)  # espeakCHARS_UTF8
    lib.espeak_Synchronize()
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(chunks))

if __name__ == "__main__":
    src = sys.argv[1]
    if src.endswith(".json"):
        import json
        text = "\n".join(sc.get("line", "") for sc in json.load(open(src, encoding="utf-8"))["scenes"])
    else:
        text = open(src, encoding="utf-8").read()
    synth(text.replace("*", ""), sys.argv[2])
