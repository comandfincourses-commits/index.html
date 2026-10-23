#!/usr/bin/env bash
# Speed up a recorded clip (1.0x-1.2x), convert to 9:16 1080x1920 @30fps,
# and verify the final length is 60-120 seconds.
#
# Usage: speed_and_format.sh input.mp4 output.mp4 [speed=1.1]
set -euo pipefail

in="${1:?input file}"
out="${2:?output file}"
speed="${3:-1.1}"

awk -v s="$speed" 'BEGIN { exit !(s >= 1.0 && s <= 1.2) }' \
  || { echo "Speed must be between 1.0 and 1.2 (got $speed)"; exit 1; }

ffmpeg -y -i "$in" \
  -filter_complex "[0:v]setpts=PTS/${speed},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30[v];[0:a]atempo=${speed}[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart "$out"

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
printf 'Final duration: %.1fs at %sx\n' "$dur" "$speed"
awk -v d="$dur" 'BEGIN { exit !(d >= 60 && d <= 120) }' \
  && echo "PASS: within 60-120s" \
  || { echo "WARN: outside 60-120s, adjust speed or trim"; exit 2; }
