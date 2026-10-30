---
name: biopic-video-series
description: Produce COMandFIN's multi-part cinematic biopic YouTube series on business personalities (Ratan Tata, Warren Buffett, Rakesh Jhunjhunwala, etc.) from a supplied voiceover. Use whenever Ankit shares a narration audio/script for a personality story part, asks to create, assemble or edit a long video for the series, or asks for scene prompts / character sheets for one.
---

# COMandFIN Biopic Video Series

The house style comes from the reference series: AI-generated, photorealistic dramatised biopic clips with Hinglish narration and dialogue. Every new personality follows the same grammar, with that personality's characters swapped in.

## Standing rules from Ankit
- **Do not create Shorts unless Ankit supplies a separate Shorts audio** for that Short. Never cut Shorts from the long video on your own.
- **The voiceover drives the edit.** The video length follows the supplied audio (e.g. Warren Buffett Part 1 ≈ 4.5 min). Only flag a mismatch against the 8–9 min default; never pad or trim narration.
- Every long video must contain, in this order:
  1. **Teaser**, 8–10 s: 3 fast shots of the episode's biggest moments with "COMING UP IN THIS EPISODE".
  2. **COMandFIN intro**: `assets/Intro_Video.mp4`, unchanged.
  3. **Recap**, from Part 2 onwards, 20–40 s: key shots of the previous part with "PREVIOUSLY ON … PART N-1".
  4. **Story**: title card (series name + PART N) over the first 4 s, voiceover on top, clip audio ducked to 15%.
  5. **End card**, 6 s: "PART N+1 COMING NEXT • LIKE • SHARE • SUBSCRIBE" over the intro's branding.
- Replace characters to match the script. For a Rakesh Jhunjhunwala story, use Rakesh Jhunjhunwala and the people in *his* story, never characters from an earlier series.
- Start with an AI-dramatisation disclaimer card (as in the reference series), and remind Ankit to tick YouTube's "altered or synthetic content" disclosure.
- Stick to publicly documented events. No invented scandals, endorsements or defamatory scenes.
- Never reuse third-party footage (e.g. other channels' films) in a published episode. The reference clips are a style guide only.

- Ankit wants the **cinematic AI-character style** only. Do not make motion-graphics or animated-infographic versions in its place (he declined one for Warren Buffett Part 1).

## Visual grammar (from the reference edit)
- Shots last 3–5 s, with a hard cut on each new beat (about 12–15 cuts per minute).
- Coverage cycle: establishing wide or aerial → medium two-shot → emotional close-up → insert detail (hands, phone, newspaper, ticker).
- Grade: warm golden-hour for nostalgia and success; desaturated teal-grey for loss, conflict and crisis.
- Text: small white sans-serif location/year supers at top-left ("OMAHA, NEBRASKA • 1941"), and dialogue subtitles at lower-centre.
- Source footage is 16:9. The builder normalises everything to 1920×1080 at 30 fps.

## Workflow per part
1. **Transcribe the audio yourself.** Ankit expects you to work from the audio alone, so don't ask for the script. HuggingFace is blocked, so get Whisper-small (CTranslate2 int8) from npm:
   `@skillninja/shortmovie-telop-model-p0..p3`. Download each `dist.tarball`, concatenate `model.bin.part0..3` into `model.bin`, verify it against `model.sha256`, and copy over the json files. Then:
   `pip install faster-whisper` → `python3 -I scripts/transcribe.py vo.mp3 transcript.json <model_dir>` (word timestamps; run it in the background, as it takes several minutes on CPU).
2. **Time the script to the audio.** Use pause detection to find beat boundaries:
   `ffmpeg -i vo.mp3 -af silencedetect=n=-35dB:d=0.35 -f null -`
   Map the sentences to the gaps and produce a beat sheet with timecodes.
3. **Write the shot list** (see `reference/shot_list_template.md`): one row per 3–5 s shot with timecode, beat, shot type, and a ready-to-paste AI video prompt that includes the **character sheet** text, so faces stay consistent.
4. **Footage generation is done by Ankit** in an AI video tool (Veo / Kling / Runway / Hailuo). This environment has no image or video generation model. He names the clips `s001.mp4`, `s002.mp4`, … in shot-list order.
5. **Assemble** with `scripts/build_episode.py episode.json` (see the docstring for the schema; use `"target_minutes": [4, 5]` for shorter parts). Check frames at the teaser, title, recap and end card before delivering.

## Google Flow lessons (from Warren Buffett Part 1 tests)
- Never put real names in Flow prompts; describe look-alike characters instead (real public figures get blocked).
- Character ingredients made from plain-background portraits leak that grey backdrop into **Ingredients to Video** clips. Use the **two-step method**: first *Create image* with the character attached and a detailed period set, then *Frames to Video* with that still as the first frame and a short motion prompt.
- Some Flow models refuse character ingredients ("You cannot use character ingredients with this model"); switch the model, or use Frames to Video.
- AI-generated print is gibberish, so ask for newspapers, letters and signs to be "out of focus and not legible", and cut around readable text in the edit.
- Ankit's browser had a third-party "Flow Automation" extension that pasted prompts several times; tell him to turn it off.
- Flow clips come out at 1280×720, 24 fps, about 8 s. The builder upscales them; cut each clip to the strongest part of the action with the per-scene `start`.

- Never write "35mm film look" in Flow prompts. Flow draws literal film-strip borders, sprocket holes and edge codes. Say "cinematic, clean full-frame image, no borders, no film frame" instead.

- Ankit wants **realistic live-action characters**, not cartoon, 2D or 3D-animated. Realism cues that work: "ultra-realistic live-action period film, real actors, natural skin texture, shot on a cinema camera with a 50mm lens, not CGI, not plastic skin". Avoid "film still" and "35mm", which produce film-strip borders.

## Character sheet format
`<Name>, <age> in <year>, <build>, <face/hair>, <signature clothing>, <setting>, photorealistic, cinematic 35mm, <grade>`
Write one sheet per era (child / young / middle-aged / elder) and reuse it verbatim in every prompt.

## Files
- `scripts/build_episode.py`: the full assembler (teaser → intro → recap → story + VO/music/subs → end card).
- `scripts/transcribe.py`: timestamped transcription, decoded through ffmpeg.
- `scripts/make_short.sh`: 9:16 Short builder. Use it only when Ankit gives a dedicated Shorts audio.
- `assets/Intro_Video.mp4`: the COMandFIN 10 s intro.
- `reference/shot_list_template.md`: shot list and prompt template.
