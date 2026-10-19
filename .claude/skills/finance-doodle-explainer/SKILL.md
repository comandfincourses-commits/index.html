---
name: finance-doodle-explainer
description: Turn a 4–10 minute voice-over (audio file) on any finance / accounting / investing concept into a fully edited, YouTube-ready animated explainer video in the "doodle explainer" style — flat yellow background, thick-outline stick-figure character, kinetic word-by-word captions synced to the voice, props popping in, charts/counters/gauges building up, hard cuts every 2–3 seconds, background music ducked under the voice and cartoon SFX. Use whenever the user uploads or mentions narration/voice-over/audio and wants an animated, cartoon, whiteboard, doodle, stick-figure or "explainer" video, wants a video "like this YouTube video", or asks to edit/animate their finance lecture audio into a video — even if they don't say "doodle". Outputs MP4 (1080p, -14 LUFS), thumbnail, SRT captions and YouTube chapters.
---

# Finance Doodle Explainer

Audio in → word-timed transcript → storyboard (you write it) → deterministic HTML/SVG animation rendered by headless Chromium → ffmpeg → finished MP4.

You (Claude) are the editor: the scripts handle timing, drawing and encoding; the creative work is the **storyboard** — choosing one clear visual idea for every 2–3 seconds of narration. That's what makes these videos work, so spend most of your effort there.

Read before starting:
- `references/style-guide.md` — the editing grammar of the reference video (pacing, shot mix, typography, colour, motion, audio). **Required.**
- `references/storyboard-schema.md` — every scene/element option. **Required** when writing the storyboard.
- `references/visual-metaphors.md` — ready visual ideas for 40+ finance concepts (Indian context).

## 0. One-time setup

```bash
SK=<path to this skill>            # e.g. ~/.claude/skills/finance-doodle-explainer
bash $SK/scripts/setup.sh          # checks ffmpeg/node/python, installs faster-whisper, numpy, playwright+chromium
```
Needs: Python 3.9+, Node 18+, ffmpeg. Whisper's model downloads once from huggingface.co. If that host is blocked, use the script-alignment fallback in step 2.

## 1. Intake (ask only what's missing)

- The audio file (mp3/wav/m4a, or a video to take the audio from). Required.
- The **script text**, if they have it. It improves accuracy and is required if Whisper can't run.
- Video title. Branding defaults: `COMandFIN` watermark, ₹ and lakh/crore formatting, yellow `#FDCF3F`. Change these only if asked.
- Music: `generated` (built-in ukulele loop, fine for drafts), `none`, or a path to a royalty-free track (recommended for publishing).

Create a work folder per video, e.g. `videos/<slug>/`, and do everything there.

## 2. Audio → transcript

```bash
python $SK/scripts/prep_audio.py INPUT_AUDIO WORK [--denoise] [--trim]
python $SK/scripts/transcribe.py WORK/voice.wav WORK --model small.en
#   Hinglish / Hindi / heavy accent:  --model large-v3 --language hi   (or omit --language)
# Fallback when Whisper is unavailable (needs the exact script):
python $SK/scripts/align_script.py WORK/voice.wav script.txt WORK
```
Outputs: `transcript.json`, `transcript.txt` (numbered sentences plus a word index), `captions.srt`. Read `transcript.txt` in full. Fix any obviously misheard finance terms in `transcript.json` (e.g. "sip" → "SIP") before planning.

## 3. Plan, then write the storyboard

1. **Beat sheet first.** Split the transcript into chapters (hook, concept, example, mistakes, takeaway). Then split each sentence into beats of roughly 1.5–3.5 s. Every beat becomes a scene: one idea, one hard cut. Target **20–28 scenes per minute** (the reference averages 2.1 s per shot). A 10-minute video means about 220–280 scenes.
2. **Pick a shot type for each beat** using the style-guide mix (text card, character + prop, data visual, metaphor scene, split comparison). Never use the same shot type three times in a row.
3. **Write `WORK/storyboard.json`**:
   - Start scenes with `"word": <index>` from `transcript.txt`. The renderer derives exact times, and each scene ends where the next begins.
   - Make builds land on the spoken word with `"at_word"`.
   - `text` elements reveal word by word, synced to the voice automatically when the on-screen words match the spoken ones. Keep on-screen text to 12 words or fewer, and highlight 1–2 key words in red.
   - Put the recurring character (same colour and outfit) in about 40% of scenes for continuity.
   - Use ₹ with Indian grouping (`₹1,00,000`, lakh/crore) unless the user wants $.
   - **Check every number you put on screen** (CAGR, EMI, ratios). Compute with Python if unsure. Wrong numbers in a finance video are unacceptable.
   - Add `"chapter"` on the first scene of each section for YouTube chapters, and a `meta.thumbnail` scene.
   - For long videos, write parts: put `"include": ["part2.json", ...]` in the main file and give each part about 2 minutes of scenes. Validate after each part.
4. Validate: `python $SK/scripts/validate_storyboard.py WORK/storyboard.json`. Fix every ERROR, and treat WARNs as style advice.

## 4. Preview, inspect, fix

```bash
node $SK/scripts/render.cjs --story WORK/storyboard.json --preview          # one still per scene + contact sheets
node $SK/scripts/render.cjs --story WORK/storyboard.json --times 12.4,30.1  # specific moments
```
**Look at every `WORK/preview/sheet_*.png`.** Check for overlapping elements, text running off the canvas, empty or cluttered frames, the wrong prop for the idea, and character expressions that don't fit the line. Fix and preview again. This loop is where the quality comes from, so don't skip it.

## 5. Build

```bash
python $SK/scripts/build.py WORK --draft --range 0-60   # optional quick look at the first minute (half resolution)
python $SK/scripts/build.py WORK --workers 4            # final: about 0.7× real time on 4 cores
```
Output goes to `WORK/output/`: `<Title>.mp4`, `<Title>_thumbnail.png` and `_1280x720.jpg`, `<Title>.srt`, `chapters.txt`.

## 6. QA before handing over

- Extract 8–12 frames around complex builds and look at them: `ffmpeg -ss T -i out.mp4 -frames:v 1 f.png`.
- The video duration should equal the audio duration ± 0.1 s.
- Loudness should be about -14 LUFS: `ffmpeg -i out.mp4 -af ebur128 -f null -` (see the Summary).
- Spot-check that captions sync with the voice at the start, middle and end.

## 7. Deliver

Give the user the MP4, thumbnail, SRT and chapters. Also write `WORK/output/youtube.md` with:
- 3 SEO title options
- a description with a hook, learning outcomes, the chapters (from `chapters.txt`), a CTA to COMandFIN courses, and hashtags
- a pinned-comment question

If running on the user's Windows PC, also copy the output folder to their preferred location (default `D:\Certificate\claude ppts\ppts`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Playwright not found` | `cd $SK/scripts && npm install playwright && npx playwright install chromium` |
| Whisper model download fails | Use `align_script.py` with the script, or allow huggingface.co |
| Words appear early or late | Wrong sentence in `align_script` mode: make sure the script matches the speech. Override with `"words": [t0, t1, ...]` on the element |
| Render slow | Fewer `camera` moves and `float` (moving frames can't be reused), more `--workers`, or `--draft` for checks |
| Element off-centre | x/y is the element's **centre** on a 1920×1080 canvas; arrows/lines use absolute `from`/`to` |
| Custom drawing needed | Use a `svg` element with your own inline SVG (thick `#111` strokes, width 6, flat fills) or an `image` element (PNG with transparent background) |
