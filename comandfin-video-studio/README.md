# COMandFIN Video Studio

You send a voice-over. You get back a branded, captioned, animated video for **Shorts/Reels (9:16)** or **long-form YouTube (16:9)**, with its **thumbnail, captions and hashtags**.

---

## 1. How we work together

**You send:**
1. The voice-over file (`.mp3`, `.wav` or `.m4a`; a phone recording is fine)
2. One line saying the format: **"Short"** (30 s – 2 min) or **"Long"**
3. *(Optional)* your script or notes, plus any numbers or examples you want shown on screen exactly

**I do:**
1. Transcribe the audio with an offline Whisper model, which handles Indian English and Hinglish
2. Write the storyboard: each visual is timed to the exact word you say it on
3. Render, add the brand intro, teaser, captions and like/share/subscribe prompts, mix the audio and normalise loudness
4. Create the thumbnail, plus a cover for Shorts
5. Write the publishing pack: titles, description with chapters, captions for YouTube, Instagram and LinkedIn, hashtags and a pinned comment

---

## 2. What every video contains

| Element | Long-form (16:9) | Shorts / Reels (9:16) |
|---|---|---|
| **Teaser** | 8–15 s "Coming up in this video" montage of the best moments, ending on a cliffhanger | 1–3 s flash-forward ("Watch till the end"), then a hook banner over the first 3 s |
| **Brand intro** | Your full 10 s COMandFIN intro, right after the teaser | Your intro's logo-reveal ending (last 3.4 s) as the closing sting, so viewers don't scroll away at the start. Set `"intro_mode": "full"` to put the whole intro at the start instead |
| **Branding** | COMandFIN wordmark, topic tag, gold progress bar, your photo badge that pulses with your voice | Same, laid out for mobile safe zones |
| **Captions** | Subtitle bar, current word in gold | Large bold captions in the centre, word by word |
| **Like / Share / Subscribe** | Animated prompt 2–3 times (≈25%, ≈60%, and at your closing line) + 12 s end screen | Animated prompt 2 times + Like/Share/Save/Follow end card |
| **Chapters** | Chapter tag on screen + `chapters.txt` for the description | n/a |
| **Sound** | Your voice + subtle sound effects on reveals and clicks (+ optional music bed) | Same |
| **Loudness** | −14 LUFS (the YouTube/Instagram target) | Same |

**Visual library** (used in the storyboard): title · bullets · statistic counter · formula · calculation window · table · bar chart · waterfall bridge · comparison (A vs B) · process steps · key statement · interview Q&A.

---

## 3. Your brand intro: analysis

`assets/intro.mp4`: 10 s, 1920×1080, 30 fps, with its own music (peaks at −0.4 dB).

| Time | Content |
|---|---|
| 0.0–1.0 s | Brand motion lines, navy/green triangle, **FINANCE** title |
| 1.0–5.5 s | Footage montage with lower-thirds: **Corporate Training**, **Financial Modelling**, **Industry-Ready Skills**, **Mentorship** |
| 5.5–6.6 s | Kinetic text strip: Valuation • Equity Research • FP&A • Investment… |
| 6.6–10.0 s | Logo reveal: **COMandFIN** wordmark, tagline, certification pills (US CMA, ACCA, CFA, FRM, US CPA), www.COMandFIN.com, and your portrait |

**Brand system taken from it** (used everywhere in the studio): navy `#091D39`, gold `#C89A2D` (the "and"), green `#10B07F` (pills and motion lines), off-white `#F7F8FB`, heavy Inter-style sans serif. Your portrait was cut out from the final frame for the avatar badge, thumbnails and end screens (`assets/presenter_cutout.png`).

---

## 4. Folder layout

```
comandfin-video-studio/
├── assets/            intro.mp4, presenter_cutout.png, presenter_avatar.png, music/ (optional bed)
├── studio/
│   ├── make.py        one-command build (transcribe → render → mix → assemble → thumbnails)
│   ├── transcribe.py  offline Whisper + VAD → transcript.json (timed words)
│   ├── find.py        prints when each word/phrase is spoken (for timing the storyboard)
│   ├── engine.html    the animation engine (both formats)
│   ├── thumbnail.html YouTube thumbnail + Reels cover
│   ├── render.js      parallel frame renderer (Playwright + ffmpeg)
│   ├── glossary.json  caption corrections for finance terms (EBITDA, COMandFIN, Ind AS, …)
│   └── setup.sh       installs the speech models on a fresh machine
└── projects/<video>/
    ├── voiceover.wav  your audio
    ├── project.json   storyboard (format, scenes, teaser, CTAs, thumbnail text)
    ├── transcript.json / transcript.txt
    └── output/        final .mp4, thumbnail.png, cover.png, chapters.txt, publish.md
```

## 5. Commands

```bash
bash studio/setup.sh                                   # once per new machine
python3 studio/transcribe.py projects/NAME/voiceover.mp3
python3 studio/find.py projects/NAME                   # word timings
python3 studio/make.py projects/NAME --preview         # fast body-only check
python3 studio/make.py projects/NAME                   # final build
```

## 6. Recording tips for your voice-overs
- Record in a quiet room, phone 15–20 cm from your mouth. Use one take per video if you can.
- Leave a half-second pause between ideas. The engine uses pauses to time the visuals.
- Say numbers clearly ("ninety crore"). They become on-screen figures.
- Shorts: open with the hook in the first sentence, and keep it under 60–90 s for the best completion rate.
- Long: start with "In this video you'll learn…". That sentence becomes the agenda slide.
- Optional: add your own royalty-free music to `assets/music/`. It is automatically lowered under your voice.

## 7. Demo projects
`projects/demo-ebitda-short` and `projects/demo-ebitda-long` were built from a **synthetic stand-in voice**, only to show the format before your real recordings arrive.
