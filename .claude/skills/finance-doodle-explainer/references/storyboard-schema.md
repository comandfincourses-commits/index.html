# Storyboard schema (`storyboard.json`)

The canvas is **1920×1080**. `x`/`y` give the **centre** of an element. Times inside a scene are **seconds from the scene's start**. Prefer `at_word`/`word`, which take indices from `transcript.txt`.

```jsonc
{
  "meta": {
    "title": "The Power of Compounding",   // used for output file names
    "author": "COMandFIN",
    "audio": "voice.wav",                   // relative to the storyboard folder
    "fps": 30,
    "bg": "yellow",                         // default scene background
    "music": "generated",                   // "generated" | "none" | "music/track.mp3"
    "music_db": -22,                        // music level relative to the voice
    "sfx": true, "sfx_db": -17,
    "lead": 0.08,                           // a scene cuts this many seconds before its first word
    "watermark": { "text": "COMandFIN", "position": "bottom-right", "opacity": 0.8 },
                                            // or { "image": "logo.png", "height": 56 }
    "thumbnail": { "bg": "yellow", "elements": [ ... ] }   // a scene object, rendered as a PNG
  },
  "include": ["part2.json"],                // optional: more files, each with {"scenes":[...]}
  "scenes": [ { ... }, ... ]
}
```

## Scene
| key | meaning |
|---|---|
| `id` | short unique name (shown in previews) |
| `word` **or** `start` | the transcript word index where the cut happens, or an absolute time in seconds. The scene runs until the next scene starts |
| `bg` | `yellow` `cream` `white` `navy` `room` `desk` `office` `street` `night`, any `#hex`, or `["street","office"]` for a split screen |
| `camera` | `none` (default) `push` `pull` `punch` `pan-left` `pan-right` `shake`, or `{"type":"push","amount":0.1,"focus":[x,y]}` |
| `chapter` | YouTube chapter title starting at this scene |
| `sfx` | an extra sound on the cut: `pop` `whoosh` `ding` `boom` `tick` |
| `elements` | an array drawn in order (later elements are on top) |

## Common element keys
| key | meaning |
|---|---|
| `type` | see below |
| `x`, `y` | centre position (defaults to the canvas centre) |
| `at` / `at_word` | when it enters (seconds into the scene, or a transcript word index) |
| `in` | `pop` (default) `fade` `grow` `slide-left` `slide-right` `slide-up` `slide-down` `drop` `wipe` `rise` `none` |
| `dur` | entrance duration (default 0.35 s; 0.6 s for `drop`) |
| `out` / `out_word`, `outAnim` | exit within the scene: `fade` (default) `pop` `slide-left` `slide-right` |
| `emph` | `{"type":"shake"|"pulse"|"bounce"|"spin","at":1.2,"dur":0.5}`, or a list of these |
| `float` | gentle bobbing amplitude in px (makes every frame unique, so it renders slower; use sparingly) |
| `rotate`, `flip` | static rotation in degrees; `flip: true` mirrors horizontally |
| `z` | z-index override |
| `sfx`, `sfx_gain` | override the automatic sound (`none` to silence it) |

## Element types

**character**: the recurring stick figure
`pose`: stand, point, pointUp, armsUp, think, shrug, hold, present, hips, headScratch, facepalm
`expr`: neutral, happy, smile, worried, shocked, sad, smirk, thinking, angry, tired, excited, confused
`outfit`: tshirt (default), suit, hoodie, uniform · `color` (shirt) · `pants` · `tie` · `logo` (text on shirt)
`hair`: curl (default), bald, old, spiky, bob, long, cap · `hairColor` · `glasses: true`
`h`: height in px (default 520) or `scale`. The figure faces the viewer; use `flip` to mirror pointing poses.

**prop**: `name` is one of the following. Use `w` for width in px (or `scale`).
coin, coins(`count`), note(`value`), cash_stack(`count`), money_bag, piggy_bank(`label`), bank(`label`), credit_card(`label`,`number`,`color`),
phone(`header`,`headerColor`,`title`,`big`,`bigColor`,`rows`:[[label,value,color?]]), calculator(`display`),
chart_up, chart_down, stock_screen(`trend`:"up"|"down",`label`), house, car, briefcase, calendar(`label`,`day`), clock(`hour`,`minute`), hourglass,
plant(`size` 0.5–1.6), money_tree, fire, lightbulb, scale(`tilt` -1..1, `left`, `right`), shield, vault, lock,
document(`title`,`rows`,`stamp`,`stampColor`), receipt(`title`,`rows`), arrow_up, arrow_down, arrow_right, check, cross, question, exclamation,
rupee, percent, office(`label`), factory, cart, grad_cap, target, rocket, umbrella, gold_bars, magnifier, gear, hand(`sleeve`), chain_ball, thought_money

**text**: kinetic caption (Mali Bold, uppercase)
`text`, `size` (64), `maxWidth` (1500), `align`, `color`, `highlight`: ["word", ...] (shown red), `highlightColor`, `bg` (puts it in a boxed panel).
Words reveal in sync with the voice when they match the transcript. `reveal: "all"` shows them at once; `words: [t0, t1, ...]` gives manual times.

**title**: big punch text (Luckiest Guy); same keys as text, `size` 150, appears all at once.

**label**: a single-line caption, `text`, `size` (40), `color`, `bg` (pill with border).

**card**: `text`, `style`: `box` (cardboard box, default) | `sticky` | `plain`, `w`, `h`, `fill`, `size`.

**bubble**: speech or thought balloon: `text`, `style`: speech | thought, `tail`: bottom-left | bottom-right, `w`, `h`, `size`.

**arrow** / **line**: `from`: [x,y], `to`: [x,y] (absolute), `bend` (−0.5..0.5 curve), `color`, `width`, `drawDur`. A line is dashed unless `dashed: false`.

**bars**: `values`, `labels`, `colors`, `prefix`/`suffix`, `format`: inr | intl | plain, `decimals`, `max`, `w`, `h`, `stagger`, `growDur`, `valueSize`, `labelSize`, `showValues`.

**linechart**: `values`, `labels` (use "" to skip one), `color`, `width`, `min`, `max`, `endLabel`, `w`, `h`, `drawDur`.

**pie**: `values`, `labels`, `colors`, `w`, `drawDur` (a donut is not supported; use pie).

**gauge**: `value`, `segments`: [[from, to, color, label?], ...] (default CIBIL 300–900 bands), `caption`, `w`, `drawDur`.

**counter**: animated number: `from`, `to`, `prefix` ("₹"), `suffix` ("%"), `format` (inr default), `decimals`, `size` (140), `color`, `countDur`. A ding plays when it lands.

**table**: `header`, `rows`, `colColors`, `size`, `stagger` or `row_words` (a word index per row).

**image**: `src` (PNG/SVG path relative to the storyboard), `w`, `h`, `fit`. Use for logos, screenshots or your own illustrations.

**svg**: `svg` (an inline `<svg viewBox=...>...</svg>` string), `w`, `h`. For one-off drawings, match the house style: `stroke="#111" stroke-width="6" stroke-linejoin="round"` with flat fills.

## Layout cheat-sheet (1920×1080)
- Title text row: y ≈ 120–160. Main subject: y ≈ 540–640. Bottom caption: y ≈ 880–940. Keep the watermark corner (bottom-right) clear.
- Two-up comparison: x = 560 and x = 1360 (or 480 and 1440). Three-up: x = 420, 960, 1500.
- Character at h 560–640 stands with feet near y ≈ 900 when y ≈ 600.
- Character + prop: character x ≈ 560, prop x ≈ 1300 (point pose aims right; use `flip` to aim left).
- Floor backgrounds (`room`, `desk`): the floor line is at y ≈ 842 (room) or 778 (desk). Rest objects so their bottom edge sits on it.

## Minimal examples
```json
{ "id": "deal", "word": 30, "elements": [ { "type": "text", "text": "Here's the deal", "size": 76 } ] }

{ "id": "emi", "word": 212, "bg": "room", "elements": [
  { "type": "character", "pose": "hold", "expr": "worried", "x": 600, "y": 600, "h": 600 },
  { "type": "prop", "name": "calendar", "label": "EMI DUE", "day": "5", "x": 1300, "y": 480, "w": 320, "at_word": 215 },
  { "type": "label", "text": "₹18,500 every month", "x": 1300, "y": 720, "size": 52, "color": "#E53935", "at_word": 217 } ] }

{ "id": "score", "word": 300, "elements": [
  { "type": "gauge", "value": 780, "caption": "CIBIL score", "x": 960, "y": 560, "w": 900 } ] }
```
