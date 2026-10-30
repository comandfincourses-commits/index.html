"""ChatGPT (image) + Sora (video) prompt sheet for Warren Buffett Part 1, 37-shot cut."""
import runpy
m = runpy.run_path("shots37.py")
S, STYLE, REAL = m["S"], m["STYLE"], m["REAL"]
BLUR = " Any printed or handwritten text is blurred and not legible."
TXT = m["TXT"]
out = ["# Warren Buffett Part 1: ChatGPT + Sora Prompts (37 shots)\n",
       "## How it works\n",
       "1. **Create the 9 characters first** in one ChatGPT chat, using `WB_Character_Bible.md`. Keep using that same chat.\n",
       "2. **For each shot, Step 1 (ChatGPT image):** paste the IMAGE prompt into the same chat. It refers to the characters by name, so ChatGPT reuses their faces. Download the image.\n",
       "3. **Step 2 (Sora video):** open Sora (sora.com, or Sora inside ChatGPT), upload the Step 1 image, paste the VIDEO prompt, choose **16:9 landscape, 10 seconds**, and generate. Download it as `wNN.mp4` (e.g. `w01.mp4`).\n",
       "4. **Shots without characters** go straight to Sora with the VIDEO prompt (no image needed).\n",
       "5. Never type real names. If Sora won't animate an image of a realistic person, use the text-only video prompt instead and send me the result. I'll check consistency.\n",
       "Shot w03 is already done.\n"]
for i, (st, cue, sup, chars, grade, vis) in enumerate(S):
    sid = f"w{i + 1:02d}"
    end = S[i + 1][0] if i + 1 < len(S) else m["VO_END"]
    head = f"---\n### {sid} · {int(st // 60)}:{st % 60:04.1f} · {end - st:.1f}s on screen\nNarration: {cue}\n"
    if vis == "DONE":
        out.append(head + "\n**DONE** (your approved newspaper clip)\n"); continue
    blur = BLUR if any(k in vis.lower() for k in TXT) else ""
    vid = (f"{vis}.{blur} {STYLE[grade]}. Ultra-realistic live-action period film, real actors and real locations, natural human "
           f"movement and expressions, shot on a cinema camera with a 50mm lens, slow subtle camera movement, subtle film grain, "
           f"not CGI, not animation. 16:9, no text, no subtitles, no logos, no borders.")
    if chars:
        img = (f"Using the characters we created in this chat ({chars}), create a new image with the same faces, hair and clothes: "
               f"{vis}. Real, detailed period location with depth, not a studio backdrop.{blur} {STYLE[grade]}. {REAL}. "
               f"Shallow depth of field, 16:9 landscape, clean full-frame image with no borders, no text.")
        out.append(head + f"Characters: **{chars}**\n\n**Step 1: ChatGPT IMAGE prompt**\n```\n{img}\n```\n**Step 2: Sora VIDEO prompt** (upload the Step 1 image)\n```\n{vid}\n```\n")
    else:
        out.append(head + f"No characters: **Sora only**\n\n**Sora VIDEO prompt**\n```\n{vid}\n```\n")
open("WB_Part1_ChatGPT_Sora_Prompts.md", "w").write("\n".join(out))
print("ok")
