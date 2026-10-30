"""Warren Buffett | Part 1: credit-saving cut (37 shots, ~8 s each), timed to the 4:28 voiceover.
Writes the Flow prompt sheet (two-step format), a tracker CSV and episode.json for build_episode.py."""
import csv, json

VO_END = 269.9
CLIP = 7.8          # usable seconds in a Flow 8 s clip
STYLE = {"warm": "Warm golden-hour light, soft amber tones", "cold": "Cold overcast light, desaturated teal-grey tones",
         "night": "Low-key lamp light, deep shadows, warm practical lights", "neutral": "Natural daylight, gentle film colour"}
SUF = "Photorealistic period drama, cinematic, shallow depth of field, slow subtle camera movement, clean full-frame image with no borders, no film frame, no scratches, no text, no subtitles, no logos."
BLUR = " Any printed or handwritten text is out of focus and not legible."
TXT = ("newspaper", "letter", "form", "certificate", "chalkboard", "diary", "notebook", "notice", "sign", "deed", "brochure")

# (start, narration cue, super, characters, grade, visual incl. set)
S = [
 (0.0, "Socho, ek 11 saal ka bachcha… pehla share", "", "Boy 11", "warm",
  "In a 1940s brokerage office with a large chalkboard of stock prices, the boy counts his saved dollar bills and coins on the wooden counter and slides them to a clerk"),
 (5.8, "Share girne lagta hai… darr ke maare bech deta hai", "", "Boy 11", "cold",
  "In the same 1940s brokerage office, a clerk erases a chalk price and writes a lower one; the boy watches, anxious, biting his lip, then nods reluctantly"),
 (11.6, "Wahi share 5 guna ho gaya", "", "Boy 11", "cold", "DONE"),
 (15.5, "Us din ek lesson seekha… famous investor", "", "Boy 11", "warm",
  "The boy stands at an upstairs window of a 1940s Omaha family home at dusk, looking out over rooftops, thoughtful, silhouette with warm rim light"),
 (22.5, "Uska naam tha… Warren Buffett (title card)", "", "", "warm",
  "Slow push-in down a quiet 1930s Omaha brick street at golden hour, vintage cars parked, shop awnings, a few pedestrians"),
 (29.5, "Teen parts… Oracle of Omaha tak", "", "", "warm",
  "Aerial drone shot rising over the modern Omaha, Nebraska skyline and the Missouri river at sunset"),
 (35.0, "[CTA] Subscribe aur bell icon", "", "Boy 6", "warm",
  "On a leafy 1930s Omaha street, the small boy rides a bicycle toward camera and happily rings its shiny bell"),
 (43.8, "30 August 1930 — janam", "OMAHA, NEBRASKA • 30 AUGUST 1930", "Mother, Father", "warm",
  "In a 1930 hospital room with tall windows, the mother in bed tenderly holds a newborn wrapped in a white blanket while the father leans in with a proud smile"),
 (52.0, "1929 crash… Great Depression", "NEW YORK • 1929", "", "cold",
  "Panicked crowd of men in fedoras and overcoats outside a grand stock exchange building on Wall Street, ticker tape blowing in the wind"),
 (60.8, "Banks band… Howard ka bank bhi", "", "Father", "cold",
  "Outside a small 1930s Omaha bank with locked glass doors and a crowd knocking in the rain, the father stands still, hat in hand, stunned"),
 (68.9, "Paise ki tangi… Howard ne haar nahi maani", "", "Mother, Father", "night",
  "At night in a modest 1930s kitchen, the mother counts a few coins into a glass jar under an oil lamp while the father, determined, buttons his suit jacket"),
 (77.0, "Paise, mehnat aur risk… numbers se khelta", "", "Boy 6, Father", "warm",
  "In a small 1930s brokerage office, the boy sits on the floor beside his father's desk scribbling numbers in a little notebook while the father talks on a candlestick telephone"),
 (85.6, "6 saal… dadaji ki grocery shop", "OMAHA • 1936", "Boy 6, Grandfather", "warm",
  "Inside a 1930s grocery store with wooden shelves of tins and jars and a brass cash register, the grandfather hands the boy a six-pack of classic glass soda bottles across the counter, smiling"),
 (93.5, "Ek-ek bottle 5 cents mein becha", "", "Boy 6", "warm",
  "On a sunny 1930s residential street, the boy pulls a wooden wagon of soda bottles and sells one at a front door to a neighbour lady who hands him a nickel"),
 (100.1, "5 cent se kya hota hai…", "", "Boy 6", "night",
  "At a 1930s kitchen table by lamp light, the boy lines up six nickels and writes figures in a small notebook, concentrating"),
 (106.5, "Khareedo sasta… billions ki company", "", "", "warm",
  "Slow motion close-up of a nickel dropping into a glass jar already half full of coins on a sunlit windowsill"),
 (112.4, "11 saal mein pehla share (sister ke saath)", "OMAHA • 1942", "Boy 11, Sister", "warm",
  "At a broker's counter in a 1940s office, the boy and his elder sister count dollar bills together and hand them to a clerk who stamps a stock certificate"),
 (119.5, "Price gira… behen ki daant", "", "Boy 11, Sister", "night",
  "At a 1940s family dinner table, the sister scolds the boy, who stares down at his plate, guilty"),
 (126.5, "$40 pe bech diya… baad mein $200", "", "Boy 11", "warm",
  "The boy walks out of a 1940s brokerage office onto an Omaha street, pocketing a little money, relieved, then glances back at the building"),
 (133.1, "Do lessons… jaldbaazi mat karo", "", "Boy 11", "night",
  "In his 1940s bedroom at night, the boy sits on his bed writing slowly in a small diary by a bedside lamp, an hourglass on the shelf beside him"),
 (142.0, "Patience… [CTA] like & share", "", "Boy 11", "warm",
  "The boy sits on a wooden fence at sunset over golden Nebraska wheat fields, smiling calmly"),
 (150.5, "1942: pitaji Congress ke liye chune gaye", "1942", "Father", "neutral",
  "The father speaks at a podium draped with American flags at a 1940s election rally, crowd applauding"),
 (159.0, "Washington shift… Warren khush nahi tha", "WASHINGTON, D.C.", "Teen 14", "cold",
  "The teenager stares sadly out of a 1940s car window in the rain as the domed Capitol building in Washington passes by"),
 (166.3, "Subah-subah newspaper delivery", "", "Teen 14", "cold",
  "At blue dawn on a 1940s Washington residential street, the teenager rides a bicycle with a newspaper bag, tossing papers onto porches"),
 (173.5, "13 saal mein tax return… cycle business expense", "AGE 13", "Teen 14", "night",
  "In a 1940s kitchen at night, the teenager fills in a printed tax form with a fountain pen, his bicycle leaning against the wall behind him"),
 (180.7, "Pinball machine $25 mein", "", "Teen 14, Friend", "neutral",
  "In a cluttered 1940s junk shop, two teenagers inspect a dusty used pinball machine, then grin at each other"),
 (188.3, "Barber shop… ek se teen… $1,200", "", "", "warm",
  "Inside a 1940s barbershop, waiting customers play a glowing pinball machine, coins drop into the slot, a barber works in the background"),
 (196.5, "Us paise se… Nebraska mein farm", "NEBRASKA", "Teen 14", "warm",
  "The teenager stands in a vast Nebraska farm field at golden hour, wind moving the wheat, looking proudly over his land"),
 (205.0, "Farm kiraye pe… padhai", "", "", "warm",
  "A tenant farmer drives a vintage 1940s tractor across a Nebraska field at golden hour"),
 (212.0, "Pitaji ke kehne pe… 19 saal mein graduate", "UNIVERSITY OF NEBRASKA • 1950", "Young Man 20, Father", "warm",
  "On a 1950 university campus lawn on graduation day, the young man in cap and gown shakes hands with his proud father"),
 (218.7, "Harvard Business School mein apply", "HARVARD BUSINESS SCHOOL • 1950", "Young Man 20", "cold",
  "In a wood-panelled 1950 interview room, the young man sits across a desk from a stern professor in tweed, tense"),
 (224.5, "Harvard ne reject kar diya", "", "Young Man 20", "cold",
  "On a train by the window, the young man reads a rejection letter, his hands trembling slightly, grey countryside passing"),
 (230.4, "Woh toot sakta tha… turning point", "", "Young Man 20", "cold",
  "The young man walks alone along a rainy campus path, coat collar up, then stops and looks up as the rain eases and sunlight breaks through the clouds"),
 (238.9, "Ek kitaab… aur ek guru", "", "Young Man 20", "warm",
  "In an old library with tall shelves, the young man pulls a thick blue hardback book from a shelf, dust floating in a beam of light"),
 (245.3, "Woh kahani hai Part 2 mein… rejection ant nahi", "", "Young Man 20", "night",
  "In a small 1950 boarding-house room at night, the young man opens the blue book under a desk lamp, his face lit with fascination, slow push-in"),
 (252.5, "Sahi raste ki shuruaat… [CTA] comment", "", "Young Man 20", "warm",
  "The young man walks along an open Nebraska road toward the sunrise, suitcase in hand, back view, then turns with a confident small smile"),
 (261.0, "[CTA] Subscribe… Part 2: asli struggle", "", "Young Man 20", "neutral",
  "A steam train pulls out of a 1950 station; the young man looks out of the window, determined, as the train heads toward a distant city skyline"),
]

rows, md = [], ["# Warren Buffett Part 1: Flow Prompts (37-shot credit-saving cut)\n",
                "Never type real names into Flow. Name each clip exactly by its shot number (`w01.mp4` … `w37.mp4`).\n",
                "**Character shots, two steps:** (1) **Create image** with the listed characters attached and the IMAGE prompt; "
                "(2) **Frames to Video** with that image as the first frame and the MOTION prompt (16:9, 8 s).\n",
                "**Shots without characters:** **Text to Video** with the single VIDEO prompt (16:9, 8 s).\n",
                "Shots marked ★ are character close-ups: use Fast/Quality for them, and the cheaper setting for the rest.\n"]
for i, (st, cue, sup, chars, grade, vis) in enumerate(S):
    sid = f"w{i + 1:02d}"
    end = S[i + 1][0] if i + 1 < len(S) else VO_END
    dur = round(end - st, 2)
    slow = round(max(1.0, dur / CLIP), 3)
    rows.append(dict(shot=sid, start=st, end=end, dur=dur, slow=slow, cue=cue, super=sup, characters=chars, grade=grade, visual=vis))
    head = f"### {sid} · {int(st // 60)}:{st % 60:04.1f} · {dur:.1f}s" + (" · DONE (approved s043)" if vis == "DONE" else "")
    md.append(head + f"\nNarration: {cue}\n")
    if vis == "DONE":
        continue
    blur = BLUR if any(k in vis.lower() for k in TXT) else ""
    if chars:
        star = " ★" if "close" in vis.lower() or chars.count(",") == 0 and grade in ("cold", "night") else ""
        md.append(f"Characters to attach: **{chars}**{star}\n\nIMAGE:\n```\nCinematic film still: {vis}. Real, detailed period location with depth, "
                  f"not a studio backdrop, natural motivated light.{blur} {STYLE[grade]}. Photorealistic, cinematic, shallow depth of field, clean full-frame image with no borders, no film frame, no scratches, 16:9.\n```\n"
                  f"MOTION:\n```\n{vis}. Subtle natural movement, slow subtle camera movement, cinematic.{blur} Clean full frame, no borders, no film frame, no scratches, no text, no subtitles, no logos.\n```\n")
    else:
        md.append(f"Text to Video:\n```\n{vis}.{blur} {STYLE[grade]}. {SUF}\n```\n")

open("WB_Part1_Flow_Prompts_37.md", "w").write("\n".join(md))
with open("WB_Part1_Tracker_37.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]) + ["status"]); w.writeheader()
    for r in rows:
        w.writerow({**r, "status": "Done" if r["visual"] == "DONE" else "To generate"})

scenes = []
for r in rows:
    src = "clips/s043.mp4" if r["visual"] == "DONE" else f"clips/{r['shot']}.mp4"
    start = 4.0 if r["visual"] == "DONE" else 0.0
    scenes.append({"src": src, "start": start, "dur": r["dur"], **({"slow": r["slow"]} if r["slow"] > 1 else {})})
ep = {"series": "Warren Buffett", "part": 1, "intro": "assets/Intro_Video.mp4", "title_at": 22.6, "target_minutes": [4, 5.5],
      "teaser": [{"src": "clips/s043.mp4", "start": 4.5, "dur": 3}, {"src": "clips/w26.mp4", "start": 3.0, "dur": 3},
                 {"src": "clips/w32.mp4", "start": 2.0, "dur": 3}],
      "scenes": scenes,
      "supers": [{"at": r["start"], "dur": 3.0, "text": r["super"]} for r in rows if r["super"]],
      "voiceover": "audio/WB_Part1_VO.mp3", "voiceover_delay": 0, "output": "out/WarrenBuffett_Part1.mp4"}
json.dump(ep, open("episode_37.json", "w"), indent=1)
todo = [r for r in rows if r["visual"] != "DONE"]
print(len(rows), "shots;", len(todo), "to generate;", sum(1 for r in todo if r["characters"]), "with characters;",
      "max slow", max(r["slow"] for r in rows), "max dur", max(r["dur"] for r in rows))
