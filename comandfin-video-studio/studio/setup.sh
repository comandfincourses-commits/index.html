#!/usr/bin/env bash
# One-time setup for a fresh machine/session. Downloads offline speech models from GitHub releases.
set -e
pip install -q "sherpa-onnx==1.12.40" soundfile numpy pillow "rembg[cpu]"
mkdir -p /opt/asr && cd /opt/asr
if [ ! -f sherpa-onnx-whisper-small/small-encoder.int8.onnx ]; then
  curl -sSL -o small.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
  tar xjf small.tar.bz2 && rm small.tar.bz2
  rm -f sherpa-onnx-whisper-small/small-encoder.onnx sherpa-onnx-whisper-small/small-decoder.onnx
fi
[ -f vad.onnx ] || curl -sSL -o vad.onnx https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
command -v ffmpeg >/dev/null && node -e "require('playwright')" && echo "setup OK"
