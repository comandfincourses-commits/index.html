# COMandFIN Video Studio

Turns a voice-over into a branded, animated explainer video in the style of
"X Explained Like You're 5" channels: flat cartoon characters, speech bubbles,
animated charts, big numbers, on-screen captions, COMandFIN branding and
repeated Like / Share / Subscribe call-outs.

| Format | Size | Length | Extras |
|---|---|---|---|
| `short` (YouTube Shorts / Instagram Reels) | 1080×1920 | 30 s – 2 min | branded header, bold captions, progress bar, 9:16 cover + 16:9 thumbnail |
| `long` (YouTube) | 1920×1080 | up to ~6 min | teaser hook + channel intro, watermark, subtitles, 8 s end screen with "Watch Next" slots |

### Long-form running order

1. **Teaser hook (optional, off by default)**: `"teaser": true` (auto-pick) or
   `{"start", "end"}` adds a 5–10 s "COMING UP" replay before the intro.
2. **Channel intro**: `assets/intro.mp4` (the 10 s COMandFIN intro), conformed to the
   video's size and loudness.
3. **Main video** → **end screen**.

Every video gets: logo branding throughout, 1–3 animated **Like · Share · Subscribe**
pop-ups (with click + "ding"), a branded end card, a thumbnail, and a publish kit
(titles, description/caption, hashtags, tags, pinned comment).

## Workflow

1. Ankit sends the voice-over (MP3/WAV/M4A) + says **short** or **long**.
2. Claude writes `spec.json`: splits the narration into scenes (`line` = exact words
   spoken in that scene), picks visuals, and writes thumbnail text + publish kit.
3. Render:
   ```bash
   python3 studio.py render path/to/spec.json --out out/ --draft   # quick half-res preview
   python3 studio.py render path/to/spec.json --out out/           # final 1080p
   ```
4. Output in `out/`: `<slug>.mp4`, `<slug>_thumbnail.jpg`, (`<slug>_cover_9x16.jpg`),
   `<slug>_publish_kit.md`.

Scene timing is taken from the audio automatically: the engine finds the pauses
in the voice-over and snaps scene changes and captions to them. If a scene starts
late or early, add `"at": 12.4` (seconds into the voice-over) to that scene.

Characters' mouths move with the loudness of the voice-over.

## Requirements

`ffmpeg`, Python 3 with `pillow`, `numpy`, `fonttools`. Fonts (Poppins, Kalam,
Caveat, Noto Sans Devanagari — SIL OFL) are bundled in `fonts/`.
`tools/placeholder_voice.py` (needs `pip install espeakng-loader`) makes a robotic
test voice from a spec, for checking timing before the real recording arrives.

## spec.json reference

```jsonc
{
  "format": "short",                 // or "long"
  "slug": "ebitda-in-60-seconds",    // output file name
  "title": "EBITDA in 60 Seconds",
  "series": "Finance Explained Simply", // header line on Shorts
  "audio": "voice.mp3",              // relative to the spec file
  "music": "bed.mp3", "music_volume": 0.08,   // optional background music
  "teaser": {"start": 92.0, "end": 100.5},   // long only, optional; voice-over seconds, or true
                                             // to auto-pick. Omitted = no teaser
  "tighten_pauses": true,            // default: every pause > 0.4 s shortened to 0.3 s;
                                     // false = keep the recording as is. Times in the spec
                                     // ("at", captions, cta_times) stay in original voice-over seconds
  "intro_after": 25.0,               // long only, optional: cold open. Play the first 25 s of the
                                     // voice-over, then the channel intro, then the rest
  "intro_video": "my_intro.mp4",     // long only; default assets/intro.mp4, false = none
  "cta_times": [8, 30],              // optional; default 1–2 for shorts, 3 for long
  "cta_lines": ["Found this useful? *Like* & *Subscribe*!"],
  "end_message": "Share this with someone who is learning *finance*!",
  "scenes": [ ... ],
  "thumbnail": {"text": "*EBITDA* explained", "tag": "Interview must-know",
                "who": "prof", "mood": "surprised", "pose": "point", "icon": "up"},
  "meta": {"titles": [], "description": "", "caption": "", "hashtags": [],
           "tags": [], "pinned_comment": "", "chapters": []}
}
```

Wrap words in `*asterisks*` to highlight them (gold in captions/titles, red in bubbles).
Use `\n` for a forced line break.

### Scene types

Every scene has `line` (the narration spoken during it — drives timing and captions).
Long videos: add `"chapter": "Name"` to the scenes that start a chapter. The publish kit then
lists YouTube chapter timestamps, already shifted for the teaser and intro.

| type | fields | looks like |
|---|---|---|
| `title` | `text`, `sub`, `tag`, `icon` | hook / chapter card on a dark studio background |
| `character` | `cast`, `speaker`, `say`, `think`, `prop`, `board`, `bg` | 1–3 characters, speech or thought bubble, floating prop |
| `chart` | `kind` (`bar`/`line`), `title`, `values`, `labels`, `prefix`, `suffix`, `decimals`, `color`/`colors`, `note` | animated bar growth or line draw-on |
| `bignumber` | `value` (e.g. `"₹4,250 Cr"`, counts up), `label`, `icon`, `color` | one big stat |
| `list` | `title`, `items`, `icon` (optional; numbered otherwise) | items pop in one by one |
| `compare` | `title`, `left`/`right` = `{title, points, color}` | two cards with a VS badge |
| `formula` | `text` (use `\n`), `note`, `cast` | chalk formula written on a blackboard |
| `quote` | `text`, `by` | big quote on a dark background |
| `flow` | `title`, `steps` = `[{title, text, icon}]`, `note`, `vertical` | process / timeline boxes joined by arrows, revealed one by one |

- `cast`: `[{"who": "prof", "mood": "happy", "pose": "point", "x": 0.3, "label": "*Priya* · Pune"}]`
  (`label` = name badge on the character)
  - `who`: `prof` (CA / teacher, navy suit), `student`, `investor`, `boss`, `woman`, `generic`
  - `mood`: `neutral`, `happy`, `worried`, `sad`, `angry`, `serious`, `surprised`
  - `pose`: `idle`, `point`, `wave`, `shrug`, `think`, `cheer`
- `bg`: `office`, `classroom`, `city`, `studio`, `dark`, `paper`, `brand`
- `icon` / `prop`: `up`, `down`, `coin`, `bag`, `bulb`, `bank`, `chart`, `warning`,
  `check`, `cross`, `target`, `doc`, `like`, `share`, `bell`, `phone`, `shield`, `lock`,
  `calendar`, `clock`, `people`, `exchange`

## Transcribing a voice-over

```bash
pip install sherpa-onnx
# models (GitHub releases of k2-fsa/sherpa-onnx, tag asr-models):
#   sherpa-onnx-whisper-small.tar.bz2  and  silero_vad.onnx  -> MODELS/
python3 tools/transcribe.py voice.wav transcript.json --models MODELS --lang en
```

Correct any misheard words in the JSON (and add `*highlights*`), then point the spec at it
with `"captions_file": "captions.json"`: captions then follow each spoken phrase exactly.
Give every scene an `"at"` (seconds) taken from the transcript for frame-accurate cuts.

## Projects

- `projects/stock-market-one-trade/`: "Journey of One Trade" (long, 9:04). The voice-over
  (`voice.wav`) is not committed; put it back next to `spec.json` to re-render.

See `examples/ebitda-short/spec.json` and `examples/long-demo/spec.json`.
