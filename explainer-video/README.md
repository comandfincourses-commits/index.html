# COMandFIN Explainer Video Format: Analysis, Template & Script

**Episode built:** Option Greeks, Episode 2: *Gamma, the speed at which Delta changes*
**Output:** `COMandFIN_Option_Gamma_Explainer.mp4` (1280×720, 25 fps, 1 min 53 s, no audio)

---

## 1. What the reference videos do

The four reference clips are segments of one long-form lesson on Option Delta. All four use the same production approach.

| Element | What the reference does |
|---|---|
| **Length per segment** | 99–117 s. Each clip covers one idea. |
| **Rhythm** | Presenter-to-camera and full-screen animation alternate roughly every 5–25 s. Animation takes about 65–75% of screen time. |
| **Measured timelines** | Clip 1: Anim 0–8, Presenter 8–14, Anim 14–22, Presenter 22–24, Anim 24–33, Presenter 33–44, Anim 44–112.<br>Clip 4: Anim 0–23, Presenter 23–47, Anim 47–77, Presenter 77–82, Anim 82–102, Presenter 102–117. |
| **Opening** | A URL is typed into a search bar, a cursor clicks, and a series-title window opens with a loading bar. |
| **Visual language** | Grid-paper background, flat retro "desktop window" frames with a hard offset shadow, label chips, hand-drawn doodles in the corners (coins, money bag, sparkles, mascot), and a cursor that "drives" the screen. |
| **Teaching sequence** | Concept, then analogy (film set or ticket counter), then visual model (moneyness ruler), then **twin charts** (underlying vs option, drawn live), then a **step-by-step calculation window**, then a **summary table** built row by row, then the presenter wraps up. |
| **Presenter set** | Dark studio, blue LED rim lights, desk with laptop, mid shot, lapel mic. Lower-third name tags slide in. |
| **Branding** | Small logo top-right on every frame, one accent colour throughout. |
| **Audio** | Continuous narration over a soft music bed, with no silent gaps. |

## 2. The COMandFIN version: same structure, own identity

- **Palette:** COMandFIN navy `#0B1F3A`, gold `#C99A2E`, mint `#0FAE83` and red `#C0392B` (taken from the existing COMandFIN Learning Lab page) instead of the reference's orange.
- **Original assets:** dial meter, driving analogy, Gamma bell curve, COMandFIN logo lock-up, and CA Ankit Bajaj lower-thirds. No Zerodha/Varsity artwork, names or content are used.
- **Reusable engine:** `gamma_explainer.html` draws every frame as a function of time. To make a new episode, duplicate the file and edit the `SCENES` array. The primitives are `windowFrame`, `chip`, `lineChart`, `calcRows`, `presenter` and `cursor`.

## 3. Scene-by-scene script (narration for recording)

`[CAM]` = record to camera; the dark placeholder in the video marks the slot. `[VO]` = voice-over across the animation.

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:06 | Search bar types comandfin.com/learn, click, logo reveal | *(music sting only)* |
| 0:06–0:12 | **[CAM]** Lower-third: CA Ankit Bajaj | "Delta tells you how fast an option moves. But Delta itself never sits still. Today, let's meet Gamma." |
| 0:12–0:18 | Title window: Option Greeks, Episode 2, GAMMA | [VO] "This is Episode 2 of our Option Greeks series." |
| 0:18–0:24 | **[CAM]** | "Quick recap: a Delta of 0.40 means the premium moves about 40 paise for every one-rupee move in the stock." |
| 0:24–0:40 | Delta meter; needle sweeps OTM, then ATM, then ITM; Speed and Acceleration cards; formula | [VO] "Think of it like driving. Delta is your speed: how fast the premium moves. Gamma is your acceleration: how fast that speed changes. Watch the meter. As the stock moves from out-of-the-money to in-the-money, Delta climbs from near zero towards one. Gamma measures that change: change in Delta per one-rupee move in the stock." |
| 0:40–0:46 | **[CAM]** | "Let's put numbers on it. Same stock, one trading morning: watch the price and watch the Delta." |
| 0:46–1:06 | Twin charts: ABC Ltd ₹100 to ₹110; 105 Call Delta 0.40 to 0.60 | [VO] "ABC Ltd opens at ₹100 and rallies to ₹110 by 10:30. On the right is the Delta of the 105 call. It doesn't stay at 0.40. It rises steadily to 0.60. This option has a Gamma of about 0.02. So a ten-rupee rally has added 0.20 to Delta." |
| 1:06–1:26 | Calculation window, row by row | [VO] "Let's calculate it. Change in underlying: 10 points. Gamma: 0.02. Change in Delta: 10 × 0.02 = 0.20. Old Delta was 0.40, so the new Delta is 0.60. Now the premium moves about 60 paise for every rupee, up from 40. The position has become more sensitive as the trade went your way." |
| 1:26–1:30 | **[CAM]** | "So which options have the highest Gamma? The answer matters for every trader." |
| 1:30–1:44 | Moneyness table; bell curve 30 days vs 2 days | [VO] "Deep out-of-the-money and deep in-the-money options have low Gamma. Their Delta barely changes. At-the-money options have the highest Gamma. And as expiry approaches, the curve becomes tall and narrow. ATM options in the last few days can swing from 0.2 to 0.8 Delta on a small move." |
| 1:44–1:49 | **[CAM]** Lower-third: Next episode, Theta | "That's why option buyers love Gamma and option sellers fear it. Next episode: Theta, the cost of time." |
| 1:49–1:53 | End card: Subscribe, comandfin.com, disclaimer | *(music out)* |

> **Technical note for viewers / interview angle:** Gamma is the second derivative of the option price with respect to the underlying. It is the same for calls and puts with the same strike and expiry, and it is always positive for long options. The 10 × 0.02 calculation is a linear approximation. In reality Gamma itself shifts as the price moves.

## 4. How to finish the video (in Premiere Pro, DaVinci Resolve, CapCut or Camtasia)

1. **Record the five `[CAM]` lines** on a dark backdrop with one or two blue or gold LED strips behind you. Use a mid shot, a lapel mic, and a laptop on the desk. Total presenter time is about 25 s.
2. Put this MP4 on track V1. Place your camera clips on V2 exactly over the dark "PRESENTER ON CAMERA" slots (0:06, 0:18, 0:40, 1:26, 1:44). Rebuild the two lower-thirds as text overlays, or keep them by masking the bottom-left of the placeholder.
3. **Record the `[VO]` lines** as voice-over and lay them on A1. Add a low music bed on A2 at about −24 dB, ducked under speech.
4. Optional sound effects: keyboard typing (0:01–0:03), mouse click (0:04), soft "pop" on each window or chip.
5. Export at 1080p H.264. For Shorts or Reels, the 1:06–1:26 calculation section works as a stand-alone vertical clip.

## 5. Re-rendering or making the next episode

```bash
cd explainer-video
node render.js                       # full MP4
node render.js --stills 30,60,90 .   # preview PNGs at chosen seconds
```
Open `gamma_explainer.html` in a browser to preview it live, or use `?t=75` to freeze at a given second.

**Suggested series using the same template:** Theta (time decay), Vega (volatility), Put-Call Parity, DCF in 2 minutes, WACC, EBITDA vs Cash Flow, Working Capital Cycle, Ratio Analysis (current ratio, ROE DuPont).
