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
Needs: Python 3.9+, Node 18+, ffmpeg. Whisper's model downloads once from huggingface.co. If that host is blocked, use `transcribe_sherpa.py` (model from GitHub) or the script-alignment fallback in step 2.

## 1. Intake (ask only what's missing)

- The audio file (mp3/wav/m4a, or a video to take the audio from). Required.
- The **script text**, if they have it. It improves accuracy and is required if Whisper can't run.
- Video title. Branding defaults: `COMandFIN` watermark, ₹ and lakh/crore formatting, yellow `#FDCF3F`. Change these only if asked.
- Music: an original arranged track from `scripts/music_gen.py` (default for publishing: `python $SK/scripts/music_gen.py WORK/music.wav --duration <secs>` then `build.py WORK --music WORK/music.wav`), `generated` (simple loop, drafts only), `none`, or the user's own royalty-free file.

To use only part of the audio (e.g. "first 1 minute"): prepare and transcribe a slightly longer piece (`ffmpeg -t 75`), then cut at the **sentence end** nearest the requested length, so the clip never stops mid-thought. Trim `voice.wav` there (with a 0.3 s fade) and drop later words from the transcript.

Create a work folder per video, e.g. `videos/<slug>/`, and do everything there.

## 2. Audio → transcript

```bash
python $SK/scripts/prep_audio.py INPUT_AUDIO WORK [--denoise] [--trim]
python $SK/scripts/transcribe.py WORK/voice.wav WORK --model small.en
#   Hinglish / Hindi / heavy accent:  --model large-v3 --language hi   (or omit --language)
# If huggingface.co is blocked: Parakeet via sherpa-onnx (model downloads from GitHub releases, English only)
python $SK/scripts/transcribe_sherpa.py WORK/voice.wav WORK --model-dir <parakeet dir>   # setup steps in the script header
# Last resort when no speech model is available (needs the exact script):
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

## 5a. House format for every long-form video: TEASER → INTRO → VIDEO (mandatory)

Every long-form (16:9) video opens with:
1. **Teaser hook (5–10 s):** the punchiest complete sentence(s) from the video itself, such as a shocking number, a bold claim or a "how is that possible?" moment. Take it from `transcript.txt` and cut on word boundaries. It plays with its own visuals, voice and music, plus a red "COMING UP" badge.
2. **Brand intro:** `assets/brand/intro.mp4` (COMandFIN, 10 s). Never edit or re-time it.
3. **The video.**

Set `"teaser": "START-END"` (seconds in the body video) in `meta`, and `build.py` does the rest. It renders the body, appends teaser and intro with `assemble_long.py`, normalises the whole programme to -14 LUFS, and shifts `chapters.txt` (first chapter: `0:00 Coming up + intro`). To retrofit an existing video:
`python $SK/scripts/assemble_long.py body.mp4 --teaser 7.7-17.4 --out final.mp4 --description youtube_description.txt`
Keep `body_*.mp4` (the version without teaser and intro); Shorts, vertical cuts and teaser re-picks are made from it. Shorts and Reels do **not** get the intro.

## 5b. Shorts / Reels and Instagram carousel

- **Cut**: `python $SK/scripts/make_cut.py WORK SHORT_WORK 12.4-45.0 [60.2-71.0 ...]`. Cut at sentence ends from `transcript.txt`, then `fix_transcript.py SHORT_WORK fixes.txt` to correct misheard words (captions are burned in, so spelling matters).
- **Storyboard**: set `meta.width: 1080, height: 1920, captions: {words: 3, y: 0.79, size: 78}` and put the watermark top-right. Design for centre x = 540: stack elements vertically, keep big text above y ≈ 1350 (the caption band sits below it), open with a hook title in the first second, and end with a 3–4 s "Follow for more" card. Keep the same cast as the long video.
- **Carousel**: render each slide as a `meta.thumbnail` scene at 1080×1350 with `render.cjs --thumb`: one checklist point per slide, "CHECK n/7" tag, "Swipe →".
- Write `shorts_copy.md` (title, description and hashtags per Short) and `instagram_caption.md`.

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
| Phrase lookups fail after `fix_transcript.py` | Corrections merge words; match on the corrected text (e.g. `w("grey market premium")` now finds "Grey market premium") |
| Custom drawing needed | Use a `svg` element with your own inline SVG (thick `#111` strokes, width 6, flat fills) or an `image` element (PNG with transparent background) |
