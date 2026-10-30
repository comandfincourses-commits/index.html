"""Flow-ready, name-free prompts: character portraits (ingredients) + 85 shot prompts."""
import runpy
m = runpy.run_path("shots.py")
S, STYLE = m["S"], m["STYLE"]

ING = {  # code: (ingredient name to save in Flow, portrait prompt)
 "WB6":  ("BOY 6", "a 6-year-old American boy in 1936, thin build, short neatly combed light-brown hair, slightly large ears, bright curious blue-grey eyes, gentle smile, white collared shirt, dark braces/suspenders, grey shorts, knee socks"),
 "WB11": ("BOY 11", "an 11-year-old American boy in 1942, slim, light-brown hair side-parted and combed flat, earnest serious face, slightly large ears, white shirt under a knitted navy sweater vest, grey wool trousers"),
 "WB14": ("TEEN 14", "a lanky 14-year-old American teenager in 1944, thin face, short brown hair, slightly large ears, alert eyes, red-and-brown checked flannel shirt, khaki trousers, canvas newspaper bag across the chest"),
 "WB20": ("YOUNG MAN 20", "a slim 20-year-old American man in 1950, brown hair slicked back, slightly large ears, intelligent eyes, white shirt, narrow dark tie, grey cardigan"),
 "HOW":  ("FATHER", "an American man aged 35 in the 1930s, tall, receding dark hair combed back, round wire-rim glasses, serious kind face, grey three-piece suit with pocket watch chain"),
 "LEI":  ("MOTHER", "an American woman aged 30 in the 1930s, dark wavy bob haircut, warm tired eyes, modest blue floral cotton dress"),
 "DOR":  ("SISTER", "a 13-year-old American girl in 1942, dark hair in two braids, confident bossy expression, beige cardigan and pleated skirt"),
 "ERN":  ("GRANDFATHER", "an American grocer aged 65 in 1936, white hair, round spectacles, white shirt with rolled sleeves, long white grocer's apron"),
 "DON":  ("FRIEND", "a 15-year-old American teenager in 1945, stocky, curly dark hair, cheerful grin, striped T-shirt"),
}
PORTRAIT = ("Photorealistic character reference portrait of {d}. Waist-up, facing camera, neutral expression, "
            "plain soft-grey studio background, soft even light, cinematic 35mm film look, period-accurate details, high detail face, 16:9.")
REPL = {"glass Coca-Cola bottles": "classic glass soda bottles", "Coca-Cola": "soda", "Coke bottle": "glass soda bottle", "US Capitol dome": "the domed Capitol building in Washington", "Ford ": ""}
LOC = ("Filmed on a real, detailed period location (not a studio backdrop, not a plain wall), "
       "with natural motivated light from windows or lamps and depth in the background. ")
FIX = {  # shots whose description needs an explicit set
 "The boy reads a newspaper stock page, eyes widen in shock, slow push-in on his face":
 "In a 1940s Omaha family living room with patterned wallpaper, a wooden bookshelf and a window behind him, the boy sits at a wooden table reading a newspaper stock page; his eyes widen in shock; slow push-in on his face",
}
SUF = "Photorealistic period film, cinematic 35mm look, shallow depth of field, slow subtle camera movement, no text, no subtitles, no logos."

def clean(s):
    for a, b in REPL.items():
        s = s.replace(a, b)
    return s

out = ["# Warren Buffett Part 1: Google Flow Prompts\n",
       "Never type real names into Flow. These prompts describe look-alike characters so Flow does not block them.\n",
       "## STEP 1: Create character ingredients (images)\n",
       "In Flow, generate each portrait as an **image**, choose the best result, and save it as an ingredient with the name shown. "
       "Generate the four ages of the main character (BOY 6 → YOUNG MAN 20) one after another, and reuse the same face for each, so he looks like the same person growing up.\n"]
for code, (name, desc) in ING.items():
    out.append(f"### {name}\n```\n{PORTRAIT.format(d=desc)}\n```\n")
out += ["## STEP 2: Generate the shots (video)\n",
        "Use **Ingredients to Video**. Attach the ingredients listed for each shot, paste the prompt, and generate at **16:9, 8 s**. "
        "Download the clip and rename it exactly as the shot number (e.g. `s001.mp4`). "
        "Use **Fast** quality for close-ups of characters (marked ★) and **Lite/standard** for the rest.\n"]
for i, (st, cue, sup, chars, grade, vis) in enumerate(S):
    sid = f"s{i + 1:03d}"
    codes = [c for c in chars.split(",") if c]
    ings = ", ".join(ING[c][0] for c in codes) or "none"
    v = clean(FIX.get(vis, vis))
    if codes:
        v = v + ". " + LOC.strip().rstrip(".")
    for c in codes:  # refer to characters by ingredient name
        pass
    star = " ★" if codes and "close-up" in vis.lower() else ""
    out.append(f"**{sid}**{star} · Ingredients: *{ings}* · Narration: {cue or '(continues)'}\n```\n{v}. {STYLE[grade].capitalize()}. {SUF}\n```\n")
open("WB_Part1_Flow_Prompts.md", "w").write("\n".join(out))
print("ok", len(S))
