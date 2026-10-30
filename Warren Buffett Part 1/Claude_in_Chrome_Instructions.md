# Instructions to paste into Claude in Chrome (37-shot version)

Before you start:
- Turn off the "Flow Automation – Auto Flow" extension (chrome://extensions → toggle it off).
- Open your Google Flow project (flow.google.com) in the active tab. The characters are already saved: Boy 6, Boy 11, Teen 14, Young Man 20, Father, Mother, Sister, Grandfather, Friend.
- Open `WB_Part1_Flow_Prompts_37.md` and copy its full contents. You will paste it into Message 1.

---

## Message 1: set-up and first batch (paste this, then paste the prompt file below it)

```
You are helping me generate video clips in Google Flow (the open tab) for my YouTube biopic series. Below this message is my prompt file with shots w01 to w37.

Rules:
- Use only the Flow tab. Do not change account settings, buy credits, upgrade, or change my plan.
- Never type real people's names into Flow.
- Before typing any prompt, clear the prompt box completely (select all, delete), then paste the prompt exactly once.
- Skip w03 (already done).

For a shot that lists "Characters to attach":
  Step 1: Switch the output to Image. Attach each listed character (type @ and pick the name). Paste the IMAGE prompt. Generate.
  Step 2: Use Frames to Video with the generated image as the first frame. No characters are needed in this step. Paste the MOTION prompt. Settings: 16:9, 8 seconds, 1 output. Generate.

For a shot marked "Text to Video":
  Paste the single prompt in Text to Video. Settings: 16:9, 8 seconds, 1 output.

After each video finishes, download it and name it with the shot number, e.g. w01.mp4.
If Flow shows an error, refuses a prompt, or says credits are low, stop and tell me the exact message.

Do the first batch only: w01, w02, w04, w05. Then stop and tell me the file names.

[PASTE THE CONTENTS OF WB_Part1_Flow_Prompts_37.md HERE]
```

## Message 2: next batches (after Claude Code approves the first batch)

```
The first batch is approved. Continue in order with the next 8 shots that are not yet downloaded, using the same rules. Stop after 8 and tell me the file names.
```
Repeat Message 2 until all shots up to w37 are done.

---

After each batch, zip the clips and upload the zip to the Claude Code session for review. When all 36 are approved, Claude Code assembles the final video with your voiceover, the COMandFIN intro, the teaser, the captions and the end card.
