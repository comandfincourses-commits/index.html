---
name: comandfin-finance-shorts
description: Create COMandFIN-style YouTube Shorts and Instagram Reels (1–2 minutes, played at 1.0x–1.2x), either as scripts or as finished MP4s edited from the user's own voice recordings, on finance, accounting, valuation, Excel, AI-in-finance, career and certification topics. Produces a timed, word-budgeted vertical-video script (hook, value beats, payoff, CTA) with on-screen text, B-roll/visual cues, captions, SEO title, description, hashtags and an ffmpeg speed/format pass. Use whenever the user asks for a short, reel, vertical video, 60-second/90-second explainer, "shorts script", or wants a topic turned into short-form content, even if they only name the topic. Also use when the user uploads voice/audio/screen recordings and asks to edit them into a short or reel.
---

# COMandFIN Finance Shorts & Reels

Turns one finance idea into a 1–2 minute vertical video that hooks viewers in the first 3 seconds, teaches a single practical idea, and ends with a clear CTA to COMandFIN.

## Hard constraints (never break)

| Parameter | Rule |
|---|---|
| Final duration | **60–120 seconds** (sweet spot 70–90s) |
| Playback speed | **1.0x–1.2x** (default 1.1x) |
| Format | 9:16 vertical, 1080×1920, 30 fps, burnt-in captions |
| Ideas per video | Exactly **one** core idea |
| Hook | Must land within **0–3 seconds** |
| Claims | Accurate, sourced where numeric, no misleading returns or salary promises |

### Word budget (do this math before writing)

Natural speaking pace is about **150 words per minute at 1.0x** (Hinglish: ~155 wpm). Speed-up raises the effective rate.

```
words_allowed = (final_seconds / 60) × 150 × speed
raw_recording_seconds = final_seconds × speed
```

| Final length | 1.0x | 1.1x | 1.2x |
|---|---|---|---|
| 60 s | 150 words | 165 words | 180 words |
| 75 s | 188 | 206 | 225 |
| 90 s | 225 | 248 | 270 |
| 120 s | 300 | 330 | 360 |

Always run `scripts/timing_check.py` on the finished voiceover and state the estimate in the output. If it falls outside 60–120s at the chosen speed, cut or expand before delivering.

## Workflow

1. **Clarify (only if missing):** topic, language (English / Hinglish, default Hinglish for YouTube, English for LinkedIn), target length (default 75s), speed (default 1.1x), audience (students / professionals). If the user just names a topic, assume the defaults and say so in one line.
2. **Pick the visual style.** For animated story videos (no presenter), follow `references/visual-style-animated.md` (story world → name the concept → numbered feature cards → slider scorecard; original Indian characters) and write the visual column as numbered animation scenes. This is the default for economics and concept explainers. Then **pick the format** from `references/formats.md` that fits the topic (Myth vs Fact, 3 Mistakes, Explain like a CFO, Real Company Case, Interview Question, Excel Hack, Number Breakdown, Career Roadmap, Concept Story).
3. **Write 3 hook options** using `references/hooks.md`, then choose the strongest and say why in one line.
4. **Write the script** with the beat structure below, inside the word budget.
5. **Check timing** with `python3 scripts/timing_check.py <script.md> --speed <x>`.
6. **Package it:** titles, description, hashtags, captions, thumbnail/cover text, pinned comment.
7. **Edit notes:** the ffmpeg pass in `scripts/speed_and_format.sh` to apply speed, convert to 9:16 and verify the final length.
8. **Save** to `shorts/<YYYY-MM-DD>-<slug>.md` in the working directory (the user's preferred local location is `D:\Certificate\claude ppts\ppts\`; tell them to copy it there if you can't write to it).

## Workflow B: user supplies voice recordings → finished Short (MP4)

Use when the user uploads audio/video recordings of themselves reading a script (e.g. screen recordings of a teleprompter, one file per script section) and asks you to edit them into Shorts.

1. **Inspect** each file (`ffprobe`). If the video track is just a screen recording, use the audio only; read the script text off a few frames (`ffmpeg -ss <t> -frames:v 1`) to learn the section order.
2. **Transcribe with word timings:** `python3 tools/asr.py <srt-stub-dir> <vosk-model-dir> in.mkv asr.json ...`. A small English Vosk model works offline. If Hugging Face is blocked, the npm package `transcribe2texts` ships `vosk-model-small-en-us-0.15` (unpack it and use only the model folder). `pip install --no-deps vosk` and give it an empty `srt.py` stub if the `srt` wheel won't build.
3. **Pick the Shorts.** Follow the script's own "SHORT" markers, but combine sections until each Short is a complete 60–120s piece at 1.0–1.2x. Strong opener first (hook/story), one idea, end on a CTA or a rule-of-thumb line. Look for retakes and false starts in the transcript and cut them.
4. **Write a spec** (`shorts/<topic>/<id>.json`): `segments` (source file, start/end seconds from the word timings, and the *corrected* transcript of exactly what is spoken), `scenes` (each starts at an anchor phrase from that transcript, with `items` for in-scene reveals), `header`, `theme`, `end_card`.
5. **Build:** `python3 tools/build_short.py spec.json out/` tightens pauses to ≤0.32s, joins segments, then cleans the voice (high-pass, FFT denoise, presence EQ, compression), applies the speed-up with atempo and normalises to −14 LUFS. It also aligns the corrected words to the recognised timings for word-by-word captions and writes `timeline.json`. Check the printed length is 60–120s.
6. **Preview, then render:** `node tools/render.mjs out/ --preview 3,20,40` writes PNG frames. Look at them and fix overlaps before `node tools/render.mjs out/` renders the 1080×1920 30 fps MP4 (Chromium + ffmpeg, with soft whooshes on scene changes).
7. **Deliver** the MP4s plus a publishing pack (title, description, hashtags, pinned comment), and flag any statistic in the voiceover that you could not verify.

Scene types in `tools/template.html`: `stockdrop`, `question` (optional `icon`: coins, warn, rupee, doc, q, ok, no), `split`, `stat`, `lines`, `doc`, `bars` (supports negative bars), `phone` (chat), `stamp`, `vanish`, `meter`, `end`. Add new types there in the same pattern.

## Beat structure (scale timings to chosen length)

| Beat | Time (75s video) | Purpose |
|---|---|---|
| 1. Hook | 0–3 s | Pattern interrupt: surprising number, bold claim, direct question or relatable pain |
| 2. Stakes | 3–10 s | Why this matters to the viewer (marks, interview, salary, money, career) |
| 3. Value beat 1 | 10–28 s | Core concept in plain language with an Indian business example |
| 4. Value beat 2 | 28–46 s | The "how": steps, formula or framework |
| 5. Value beat 3 / twist | 46–60 s | Real company number, common mistake or interview angle |
| 6. Payoff | 60–68 s | One-line takeaway viewers can repeat |
| 7. CTA | 68–75 s | Single action: follow, comment a keyword, or link to the COMandFIN course |

Retention rules:
- Change the visual every **2–4 seconds** (cut, zoom, text pop, B-roll, chart).
- Open a loop early ("…and the 3rd one costs freshers the most") and close it near the end.
- Use short sentences, around 8–12 words each. Spoken, not written.
- Put the key number or term on screen as **bold on-screen text** the moment it is spoken.
- No intro, no "Hi guys, welcome back". Start with the hook.
- End so the final line flows back into the hook for loop replays where possible.

## Output template

Produce exactly this structure:

```markdown
# <Working title>

**Format:** <format> | **Language:** <English/Hinglish> | **Target:** <N>s @ <speed>x | **Words:** <count> | **Est. final length:** <s>s
**Audience:** <...> | **One-line idea:** <...>

## Hook options
1. ...
2. ...
3. ...
**Chosen:** #<n> because <reason>.

## Script
| Time | Voiceover (spoken) | On-screen text | Visual / B-roll / Edit |
|---|---|---|---|
| 0:00–0:03 | ... | ... | ... |
| ... | ... | ... | ... |

## Voiceover only (for teleprompter)
<plain paragraph(s) of spoken lines only; this is what timing_check.py measures>

## Captions (burnt-in style)
- 2–5 word chunks, key words in CAPS or highlighted colour

## Publishing pack
- **YouTube Shorts title (≤60 chars, keyword first):** ...
- **Instagram Reel cover text (≤6 words):** ...
- **Description (2–3 lines + CTA + course link placeholder):** ...
- **Hashtags (YouTube 3–5, Instagram 8–12):** ...
- **Pinned comment / comment-keyword CTA:** ...
- **LinkedIn repost caption (English, 3–5 lines):** ...

## Edit notes
- Speed: <x>x | Raw recording ≈ <s>s → final ≈ <s>s
- Music: low, royalty-free, ducked under voice (–18 to –22 dB)
- Sources for any numbers: ...
```

## Content standards

- **Accuracy:** Use verifiable data (annual reports, RBI, SEBI, NSE/BSE, ICAI, IFRS Foundation, CFA Institute). Name the source in edit notes. If a figure isn't verified, give a rounded illustrative number and label it "illustrative".
- **Examples:** Prefer Indian companies and situations (Reliance, TCS, HDFC Bank, Zomato, Asian Paints, a kirana store, a startup founder) and add a global example when it helps.
- **Tone:** Confident senior-professor/consultant voice, conversational, never hype. No "guaranteed placement", "get rich", or stock tips.
- **Compliance:** No buy/sell recommendations. Add "Educational content, not investment advice" to the description for any market topic.
- **Brand:** Mention COMandFIN once, in the CTA, not in the hook.

## Series & batching

When asked for multiple shorts (e.g. "10 shorts on valuation"), produce a series plan table first (episode, format, hook, one-line idea), keep a consistent series name and visual style, and cross-link via "Part 2 is on my profile".

## Files in this skill

- `references/formats.md`: 8 proven short-form formats with skeletons and finance examples
- `references/hooks.md`: hook formulas and banned openings
- `references/visual-style-animated.md`: animated concept-story style (from the Econ Lowdown "Economics Explained" reference videos): story world, continuum board, numbered cards, slider scorecard, palette, 9:16 layout
- `scripts/timing_check.py`: word count → duration estimate at 1.0x/1.1x/1.2x, flags anything outside 60–120s
- `scripts/speed_and_format.sh`: ffmpeg speed-up (1.0–1.2x), 9:16 conversion, final-length verification
- `tools/asr.py`, `tools/build_short.py`, `tools/render.mjs`, `tools/template.html`: voice-recording → edited, captioned, animated Short (Workflow B)
- `assets/fonts/`: Poppins (SIL OFL) used by the renderer
