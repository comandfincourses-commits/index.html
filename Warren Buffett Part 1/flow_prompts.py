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
FIX = {}  # per-shot description overrides
SET = {  # explicit sets for character shots whose description has none
 "s001": "on a wooden kitchen table in a 1940s Omaha home",
 "s004": "standing in a 1940s brokerage office with a chalkboard of prices behind him",
 "s023": "in a modest 1930s bedroom with a wooden wardrobe",
 "s030": "inside a 1930s grocery store with wooden shelves of tins and jars, a brass cash register and sunlit front windows",
 "s064": "in the back room of a 1940s barbershop",
 "s068": "at a wooden desk in his 1940s bedroom",
 "s073": "in a dim, wood-panelled university corridor",
 "s076": "on a rainy campus path lined with bare trees",
 "s080": "in a small 1950 boarding-house room",
 "s083": "on an open Nebraska road at sunrise",
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
TXT = ("newspaper", "letter", "form", "certificate", "sign", "notice", "chalkboard", "blackboard", "diary", "notebook", "brochure", "deed", "passbook", "tag")
BLUR = " Any printed or handwritten text is out of focus and not legible."
out += ["## STEP 2: Generate the shots\n",
        "**Shots with characters (two steps, gives the real film look):**\n",
        "1. **Create image**: attach the listed character(s) and paste the **IMAGE** prompt. Regenerate until the set and face look right.\n",
        "2. **Frames to Video**: set that image as the **first frame** (no character needed now), paste the **MOTION** prompt, 16:9, 8 s.\n",
        "**Shots without characters:** use **Text to Video** with the single **VIDEO** prompt.\n",
        "Download each clip and rename it exactly as the shot number (e.g. `s001.mp4`). Use Fast/Quality for shots marked with a star, and the cheaper setting for the rest.\n",
        "Shot s043 is already done and approved.\n"]
for i, (st, cue, sup, chars, grade, vis) in enumerate(S):
    sid = f"s{i + 1:03d}"
    codes = [c for c in chars.split(",") if c]
    ings = ", ".join(ING[c][0] for c in codes)
    v = clean(FIX.get(vis, vis))
    if sid in SET:
        v = f"{v}, {SET[sid]}"
    blur = BLUR if any(k in v.lower() for k in TXT) else ""
    tone = STYLE[grade].capitalize()
    star = " ★" if codes and "close-up" in vis.lower() else ""
    head = f"**{sid}**{star} · Narration: {cue or '(continues)'}"
    if sid == "s043":
        out.append(head + " · DONE\n"); continue
    if codes:
        img = (f"Cinematic film still: {v}. Real, detailed period location with depth, not a studio backdrop, "
               f"natural motivated light.{blur} {tone}. Photorealistic, 35mm film look, shallow depth of field, 16:9.")
        mot = (f"{v}. Subtle natural movement, cinematic 35mm, slow subtle camera movement.{blur} No text, no subtitles, no logos.")
        out.append(f"{head} · Characters: *{ings}*\n\nIMAGE:\n```\n{img}\n```\nMOTION:\n```\n{mot}\n```\n")
    else:
        vid = f"{v}.{blur} {tone}. {SUF}"
        out.append(f"{head} · Text to Video\n\nVIDEO:\n```\n{vid}\n```\n")
open("WB_Part1_Flow_Prompts.md", "w").write("\n".join(out))
print("ok", len(S))
