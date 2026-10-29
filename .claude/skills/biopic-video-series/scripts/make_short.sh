#!/bin/bash
# usage: make_short.sh SRC START END TITLE PART NEXT INTRO OUT
# Only use when Ankit supplies a dedicated Shorts audio; swap the source audio for it before publishing.
set -e
SRC=$1; SS=$2; TO=$3; TITLE=$4; PART=$5; NXT=$6; INTRO=$7; OUT=$8
T=$(mktemp -d); python3 -I "$(dirname $0)/short_overlays.py" $T/ov "$TITLE" "$PART" "$NXT"
VF="[0:v]trim=$SS:$TO,setpts=PTS-STARTPTS,fps=30,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.15[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2[v1];[v1][1:v]overlay=0:0:shortest=1,format=yuv420p,setsar=1[story]"
EF="[2:v]trim=5:10,setpts=PTS-STARTPTS,fps=30,split[c][d];[c]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.25[ebg];[d]scale=1080:-2[efg];[ebg][efg]overlay=0:(H-h)/2[e1];[e1][3:v]overlay=0:0:shortest=1,format=yuv420p,setsar=1[end]"
AF="[0:a]atrim=$SS:$TO,asetpts=PTS-STARTPTS,afade=t=out:st=$(echo "$TO-$SS-1"|bc):d=1,aformat=sample_rates=48000:channel_layouts=stereo[sa];[2:a]atrim=5:10,asetpts=PTS-STARTPTS,afade=t=in:d=0.3,aformat=sample_rates=48000:channel_layouts=stereo[ea]"
ffmpeg -v error -y -i "$SRC" -loop 1 -i $T/ov_story.png -i "$INTRO" -loop 1 -i $T/ov_end.png \
 -filter_complex "$VF;$EF;$AF;[story][sa][end][ea]concat=n=2:v=1:a=1[v][aout]" \
 -map "[v]" -map "[aout]" -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf $T
