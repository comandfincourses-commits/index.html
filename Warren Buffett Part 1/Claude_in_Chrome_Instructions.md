# Instructions to paste into Claude in Chrome

Before you start:
- Turn off the "Flow Automation – Auto Flow" extension (chrome://extensions → toggle it off). It scrambles the prompt box.
- Open your Google Flow project (flow.google.com) in the active tab.
- Keep `WB_Part1_Flow_Prompts.md` open, or paste its contents into the chat when Claude in Chrome asks for it.

---

## Message 1: test run (paste this first)

```
You are helping me generate video clips in Google Flow (the tab that is open) for my YouTube biopic series.

Rules:
- Use only the Flow tab. Do not change account settings, buy credits, or change my plan.
- Before typing a prompt, always clear the prompt box completely (select all, delete).
- Put the character ingredient first by typing "@" and choosing it from the list, then paste the prompt text exactly once.
- Settings for every clip: Video, 16:9 landscape, 8 seconds, 1 output.
- After each generation finishes, download the clip and tell me its file name.
- If Flow shows an error or refuses a prompt, stop and tell me the exact message.

Task 1: A character called "Boy 11" already exists. Generate this clip with the ingredient @Boy 11:

The boy reads a newspaper stock page, eyes widen in shock, slow push-in on his face. Cold overcast light, desaturated teal-grey tones. Photorealistic period film, cinematic 35mm look, shallow depth of field, slow subtle camera movement, no text, no subtitles, no logos.

Download it and name it s043.mp4.
```

## Message 2: create the remaining characters

```
Now create these characters in Flow (Characters → New character), one at a time, using each portrait prompt from STEP 1 of the prompt file I give you: BOY 6, TEEN 14, YOUNG MAN 20, FATHER, MOTHER, SISTER, GRANDFATHER, FRIEND. Name each character exactly as written. For BOY 6, TEEN 14 and YOUNG MAN 20, make the face look like the same person as Boy 11 at a different age. Show me each result before saving it.
```

## Message 3: test shots

```
Generate shots s001, s013, s030, s073 and s080 from STEP 2 of the prompt file. For each, attach the ingredients listed for that shot, paste the prompt once, use the same settings, and download as sXXX.mp4. Then stop so I can review.
```

## Message 4: all remaining shots (only after the test shots are approved)

```
Generate all remaining shots from s001 to s085 in STEP 2 that are not yet downloaded, in order, with the listed ingredients. Download each as sXXX.mp4. Pause every 10 shots and give me a short status.
```

---

When the clips are downloaded, zip them and upload the zip to the Claude Code session. Claude Code then assembles the final video with your voiceover, the COMandFIN intro, the teaser, the captions and the end card.
