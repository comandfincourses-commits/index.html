"""Warren Buffett | Part 1: shot list timed to the ElevenLabs voiceover (4:28).
Generates: shot list (.md), prompts (.txt), tracker (.csv) and episode.json for build_episode.py."""
import csv, json, os

VO_END = 268.4 + 1.5
OUT = os.path.dirname(os.path.abspath(__file__))

STYLE = {
    "warm": "warm golden-hour light, soft amber tones",
    "cold": "cold overcast light, desaturated teal-grey tones",
    "night": "low-key lamp light, deep shadows, warm practical lights",
    "neutral": "natural daylight, gentle film colour",
}
SUFFIX = ("photorealistic period drama, cinematic 35mm film look, shallow depth of field, subtle slow camera "
          "movement, 16:9, 5 seconds, no on-screen text, no subtitles, no logos")

CHAR = {
    "WB6": "Warren as a 6-year-old American boy (1936): thin, short neatly combed light-brown hair, slightly large ears, "
           "bright curious eyes, white collared shirt, braces/suspenders, grey shorts",
    "WB11": "Warren as an 11-year-old boy (1941): slim, light-brown hair side-parted and combed flat, earnest serious face, "
            "white shirt under a knitted sweater vest, grey trousers",
    "WB14": "Warren as a lanky 13-15-year-old teenager (1943-45): thin face, short brown hair, checked flannel shirt, "
            "khaki trousers, canvas newspaper bag",
    "WB20": "Warren as a 19-20-year-old young man (1950): slim build, brown hair slicked back, white shirt, narrow dark tie, "
            "grey cardigan or tweed jacket",
    "HOW": "Howard Buffett, his father (age 27-39): tall, receding dark hair combed back, round wire-rim glasses, "
           "serious kind face, grey three-piece suit",
    "LEI": "Leila Buffett, his mother (late 20s-30s): dark wavy bob, modest 1930s floral cotton dress",
    "DOR": "Doris, his elder sister (age 13 in 1941): dark hair in two braids, cardigan and pleated skirt",
    "ERN": "Ernest Buffett, his grandfather (60s): white hair, round spectacles, white shirt, sleeves rolled, long grocer's apron",
    "DON": "Don, his school friend (15): stocky, curly dark hair, striped T-shirt",
}

# (start_sec, narration cue, super/caption, characters, grade, visual)
S = [
    (0.0, "Socho, ek 11 saal ka bachcha…", "", "WB11", "night", "Extreme close-up of a boy's small hands counting coins and folded dollar bills on a wooden table, lamp light"),
    (3.0, "…pehla share khareedta hai", "", "WB11,HOW", "warm", "1940s brokerage office: the boy pushes a small stack of bills across a wooden counter to a clerk; a chalkboard of stock prices behind"),
    (5.8, "…share girne lagta hai", "", "", "cold", "Close-up of a clerk's hand erasing a chalk stock price and writing a lower number on a blackboard"),
    (8.4, "Darr ke maare bech deta hai", "", "WB11", "cold", "Close-up of the boy's anxious face, he bites his lip and nods reluctantly"),
    (11.6, "…wahi share 5 guna ho gaya", "", "", "warm", "Macro shot of a 1940s newspaper stock table, a finger traces a line to a much higher price, slow push-in"),
    (15.5, "Us din ek lesson seekha…", "", "WB11", "warm", "The boy stands at a window at dusk looking out at Omaha rooftops, thoughtful, silhouette with rim light"),
    (19.0, "…duniya ka sabse famous investor", "", "", "warm", "Back view silhouette of an elderly man in a dark suit walking onto a stage before a huge applauding arena audience, spotlight, face not visible"),
    (22.5, "Uska naam tha… Warren Buffett", "", "", "warm", "Slow push-in down a quiet 1930s Omaha brick street at golden hour, vintage Ford cars parked, title-card background"),
    (25.0, "Teen parts mein poori kahani", "", "", "warm", "An old leather photo album opens on a wooden table, sepia family photographs inside, dust in the light"),
    (29.5, "Janam se… Oracle of Omaha tak", "", "", "warm", "Aerial drone shot rising over the modern Omaha, Nebraska skyline and Missouri river at sunset"),
    (35.0, "[CTA] Motivational stories pasand…", "", "", "night", "Close-up of a glowing 1930s wooden valve radio dial being turned in a cosy living room"),
    (39.3, "[CTA] Subscribe aur bell icon…", "", "WB6", "warm", "Close-up of a small boy's thumb ringing a shiny bicycle bell, playful, shallow focus"),
    (43.8, "30 August 1930", "OMAHA, NEBRASKA • 30 AUGUST 1930", "", "neutral", "Aerial establishing shot of 1930 downtown Omaha, brick buildings, Model A cars, streetcar, morning haze"),
    (46.1, "…Warren Edward Buffett ka janam", "", "LEI", "warm", "1930 hospital room, the mother in bed tenderly holds a newborn wrapped in a white blanket, soft window light"),
    (49.0, "", "", "HOW", "warm", "The father looks through hospital nursery glass at the newborn, proud gentle smile, hat in hand"),
    (52.0, "1929 mein stock market crash", "NEW YORK • 1929", "", "cold", "Panicked crowd of men in fedoras and overcoats outside a grand stock exchange building on Wall Street"),
    (55.3, "", "", "", "cold", "Close-up of a brass ticker-tape machine spitting tape, anxious hands grabbing the paper strip"),
    (58.5, "Poora desh Great Depression mein", "", "", "cold", "Long breadline of men in caps and coats outside a 1930s soup kitchen, grey winter street"),
    (61.0, "Naukri kho rahe the, bank band…", "", "", "cold", "Desperate crowd pressing against the locked glass doors of a small bank with a CLOSED sign, light rain"),
    (63.8, "Howard ka bank bhi band", "", "HOW", "cold", "The father stands alone outside a shuttered small-town bank, holding his hat, stunned, rain"),
    (66.5, "", "", "", "cold", "Close-up of a hand-written notice taped to a bank door, raindrops running down the glass"),
    (68.9, "Ghar mein paise ki tangi", "", "LEI", "night", "Night kitchen table, the mother counts a few coins into a glass jar under an oil lamp, worried"),
    (71.0, "Howard ne haar nahi maani", "", "HOW", "warm", "The father buttons his suit jacket in front of a mirror, determined jaw, morning light"),
    (73.6, "Apni brokerage firm shuru ki", "", "HOW", "warm", "A sign painter finishes gold lettering on a frosted glass office door while the father watches proudly"),
    (75.8, "Paise, mehnat aur risk…", "", "WB6,HOW", "warm", "A small boy sits under his father's desk watching him talk on a candlestick telephone, papers everywhere"),
    (78.5, "", "", "WB6", "warm", "Macro close-up of the small boy's eyes, numbers and paper slips reflected, curious"),
    (81.4, "Baaki bachche khilono se khelte…", "", "", "warm", "Children play with tin toy trucks and a ball in a 1930s backyard, soft focus"),
    (83.5, "…Warren numbers se", "", "WB6", "warm", "The small boy sits alone on a porch step writing numbers in a tiny notebook, counting passing cars"),
    (85.6, "6 saal ki umar mein…", "OMAHA • 1936", "", "warm", "Exterior of a 1930s neighbourhood grocery store with striped awning and produce crates, sunny street"),
    (88.5, "Dadaji ki grocery shop se…", "", "WB6,ERN", "warm", "Behind the counter the grandfather hands the boy a six-pack of glass Coca-Cola bottles, smiling"),
    (91.0, "…25 cents mein khareeda", "", "WB6", "warm", "Macro: a small hand places a silver quarter on a worn wooden shop counter"),
    (93.5, "Ek-ek bottle 5 cents mein becha", "", "WB6", "warm", "The boy at a front door sells a Coke bottle to a neighbour lady who hands him a nickel"),
    (96.0, "6 bottles se 30 cents…", "", "WB6", "warm", "The boy pulls a wooden wagon of soda bottles along a leafy sidewalk, men buying from him"),
    (98.5, "…profit 5 cents", "", "WB6", "warm", "Close-up: small fingers line up six nickels on a porch step one by one"),
    (100.1, "Aap bolenge 5 cent se kya hota hai…", "", "WB6", "night", "The boy writes figures in a notebook at the kitchen table by lamp light, tongue out in concentration"),
    (104.8, "Khareedo sasta, becho value pe", "", "", "warm", "Slow motion: a nickel drops into a glass jar already half-full of coins"),
    (108.9, "…billions ki company bani", "", "", "warm", "Time-lapse of golden sunlight sweeping across a modern Omaha office tower, sky moving"),
    (112.4, "11 saal ki umar mein pehla share", "OMAHA • 1941", "WB11,DOR", "warm", "The boy and his sister count dollar bills together at a broker's counter in their father's office"),
    (116.0, "3 shares Cities Service Preferred", "", "", "warm", "Macro: a rubber stamp presses onto an ornate 1940s stock certificate on a desk"),
    (119.5, "Price $38 se $27", "", "", "cold", "Chalkboard: a price is erased and rewritten lower; the boy's worried reflection in a window"),
    (123.0, "Behen ki daant", "", "WB11,DOR", "night", "Dinner table: the sister scolds the boy, who stares down at his plate, guilty"),
    (126.5, "$40 pe bech diya", "", "WB11", "warm", "The boy at the broker's counter, relieved, pockets a small profit and walks away"),
    (129.5, "Kuch saal baad ~$200", "", "WB11", "cold", "The boy reads a newspaper stock page, eyes widen in shock, slow push-in on his face"),
    (133.1, "Do lessons, zindagi bhar yaad", "", "WB11", "night", "The boy sits on his bed at night writing in a small diary by a bedside lamp"),
    (137.0, "Purchase price pe mat atko", "", "", "night", "Extreme close-up of a pencil writing in a diary, page lit by lamp, handwriting blurred"),
    (140.0, "Jaldbaazi mat karo", "", "", "warm", "An antique hourglass on a desk, sand flowing in slow motion"),
    (142.0, "Patience hi asli paisa banata hai", "", "", "warm", "Time-lapse of a seedling growing into a small plant in a clay pot on a sunny windowsill"),
    (144.3, "[CTA] Lesson pasand aaya…", "", "WB11", "warm", "The boy sits on a wooden fence at sunset over Nebraska wheat fields, smiling"),
    (148.5, "[CTA] Us dost ke saath share karo…", "", "", "warm", "Two 1940s friends share a newspaper on a park bench, one laughs and points at a page"),
    (152.7, "1942 mein pitaji Congress ke liye chune gaye", "1942", "HOW", "neutral", "The father speaks at a podium draped with American flags, crowd applauding, 1940s election rally"),
    (155.4, "", "WASHINGTON, D.C.", "", "neutral", "Establishing shot of the US Capitol dome in the 1940s, cloudy sky, vintage cars"),
    (157.0, "Family Washington shift ho gayi", "", "WB14,LEI", "cold", "The family loads suitcases into a 1940s sedan outside a modest Omaha house, the teenager reluctant"),
    (159.8, "Warren bilkul khush nahi tha", "", "WB14", "cold", "The teenager stares out of a car window, rain streaking the glass, sad"),
    (163.5, "School mein grades gir gaye", "", "WB14", "cold", "1943 classroom: the teenager slumps at a back desk, a report card with low marks in front of him"),
    (166.3, "Dukh ko ek kaam mein badal diya", "", "WB14", "night", "The teenager lying on his bed staring at the ceiling, then sitting up with sudden determination"),
    (168.9, "Subah-subah newspaper delivery", "", "WB14", "cold", "Blue dawn: the teenager on a bicycle with a newspaper bag tosses papers onto porches of a 1940s street"),
    (171.6, "Roz saikdon akhbaar", "", "WB14", "cold", "Close-up of fast hands folding a tall stack of newspapers on the floor at dawn"),
    (173.5, "13 saal mein pehla tax return", "AGE 13", "WB14", "night", "The teenager fills in a printed tax form with a fountain pen at the kitchen table"),
    (177.6, "Cycle ko business expense dikhaya", "", "WB14", "neutral", "Slow pan from a bicycle leaning against a wall to the tax form on the table beside it"),
    (180.7, "Pinball machine $25 mein", "", "WB14,DON", "neutral", "Two teenagers inspect a dusty used pinball machine in a junk shop, a $25 price tag hangs on it"),
    (184.0, "", "", "WB14,DON", "warm", "The two teenagers wheel the pinball machine on a hand truck into a 1940s barbershop"),
    (188.3, "Customers wait karte-karte khelte", "", "", "warm", "Men waiting in a barbershop play pinball, coins drop into the slot, close-up of flashing lights"),
    (191.8, "Ek machine se teen, teen se zyada", "", "", "warm", "Montage-style shot: several pinball machines lined up in different barbershops, quick pans"),
    (194.7, "Business $1,200 mein bika", "", "WB14,DON", "warm", "A handshake with a businessman across a table, an envelope of cash slides across"),
    (198.2, "Us paise se… Nebraska mein", "NEBRASKA", "WB14", "warm", "The teenager stands in a vast Nebraska farm field at golden hour, wind moving the wheat"),
    (202.0, "Farm khareeda", "", "WB14", "warm", "The teenager signs a land deed with an old farmer at a wooden farmhouse table"),
    (206.0, "", "", "", "warm", "A tenant farmer drives a vintage tractor across the field while the teenager watches from the fence"),
    (210.0, "", "", "WB14", "night", "Close-up of the teenager entering rent money into a savings passbook, coins and bills beside it"),
    (214.0, "Pitaji ke kehne pe padhai", "", "WB20,HOW", "warm", "Father and son talk in a study lined with books, the father hands him a college brochure"),
    (216.5, "19 saal mein graduate", "UNIVERSITY OF NEBRASKA • 1950", "WB20", "warm", "Graduation day on a 1950 campus lawn, the young man in cap and gown smiles at his parents"),
    (218.7, "Harvard Business School mein apply", "HARVARD BUSINESS SCHOOL • 1950", "", "neutral", "Establishing shot of a red-brick Ivy League campus with a white cupola, autumn leaves"),
    (222.0, "", "", "WB20", "cold", "Interview room: the young man sits across a desk from a stern professor in tweed, tense"),
    (224.5, "…Harvard ne reject kar diya", "", "WB20", "cold", "Close-up of a rejection letter trembling slightly in his hands"),
    (227.0, "Bachpan se business kar raha tha…", "", "WB20", "cold", "The young man sits by a train window staring at the folded letter, grey countryside passing"),
    (230.4, "…top school ne mana kar diya", "", "WB20", "cold", "He walks alone along a rainy campus path, coat collar up, hands in pockets"),
    (233.1, "Woh toot sakta tha", "", "WB20", "cold", "Tight close-up of his face, eyes glistening, rain on his cheeks"),
    (234.4, "Lekin yahi rejection turning point bana", "", "WB20", "warm", "He stops and looks up as the rain eases and sunlight breaks through the clouds"),
    (238.9, "Haath lagi ek kitaab", "", "", "warm", "Library: a hand pulls a thick blue hardback book from a shelf, dust floating in a light beam, title not visible"),
    (241.8, "…aur ek aisa guru", "", "", "warm", "Back-view silhouette of an older professor in a three-piece suit writing at a lecture-hall blackboard"),
    (245.3, "Woh kahani hai Part 2 mein", "", "WB20", "night", "The young man opens the blue book under a desk lamp at night, his face lit with fascination, slow push-in"),
    (247.5, "Aaj ka lesson: rejection ant nahi", "", "", "warm", "Sunrise over a long empty Nebraska road stretching to the horizon"),
    (250.3, "…sahi raste ki shuruaat", "", "WB20", "warm", "The young man walks forward along the road toward the sunrise, back view, suitcase in hand"),
    (253.4, "[CTA] Comment: main rukunga nahi", "", "WB20", "warm", "Close-up of his determined face in golden light, a small confident smile"),
    (258.3, "[CTA] Like, share, subscribe", "", "WB20", "neutral", "A steam train pulls out of a 1950 station; he looks out of the window, determined"),
    (262.8, "Part 2: asli struggle", "", "", "night", "Wide shot of the 1950s New York skyline at dusk, lights coming on, steam rising from streets"),
]

shots, md, prompts = [], [], []
for i, (st, cue, sup, chars, grade, vis) in enumerate(S):
    end = S[i + 1][0] if i + 1 < len(S) else VO_END
    sid = f"s{i + 1:03d}"
    who = "; ".join(CHAR[c] for c in chars.split(",") if c) if chars else ""
    prompt = vis + (f". Characters: {who}" if who else "") + f". {STYLE[grade]}, {SUFFIX}."
    if end - st > 4.7:  # longer slot: ask for a 10 s clip
        prompt = prompt.replace("5 seconds", "10 seconds")
    shots.append({"shot": sid, "start": st, "end": round(end, 1), "dur": round(end - st, 2), "cue": cue,
                  "super": sup, "characters": chars, "grade": grade, "prompt": prompt})

mmss = lambda x: f"{int(x // 60)}:{x % 60:04.1f}"
with open(f"{OUT}/WB_Part1_ShotList.md", "w") as f:
    f.write("# Warren Buffett | Part 1: Shot List\n\n")
    f.write(f"Voiceover: 4:28 · {len(shots)} shots · Generate each clip at 16:9 and 5 s (trimmed to its slot at assembly). "
            "Shots marked 10 s in the prompt need a 10 s clip. Save the files as `s001.mp4`, `s002.mp4`, … in this order.\n\n")
    f.write("## Character sheets (already included in every prompt)\n\n")
    for k, v in CHAR.items():
        f.write(f"- **{k}**: {v}\n")
    f.write("\n## Teaser (8–10 s, before the intro)\ns043 (shocked face, 3 s) → s060 (pinball, 3 s) → s073 (rejection letter, 3 s)\n\n")
    f.write("## Shots\n\n| Shot | VO time | Slot | Narration cue | On-screen super |\n|---|---|---|---|---|\n")
    for s in shots:
        f.write(f"| {s['shot']} | {mmss(s['start'])}–{mmss(s['end'])} | {s['dur']:.1f}s | {s['cue']} | {s['super']} |\n")
    f.write("\n## Prompts (copy-paste)\n\n")
    for s in shots:
        f.write(f"**{s['shot']}** ({s['dur']:.1f}s): {s['prompt']}\n\n")

with open(f"{OUT}/WB_Part1_Prompts.txt", "w") as f:
    for s in shots:
        f.write(f"{s['shot']}  [{s['dur']:.1f}s]\n{s['prompt']}\n\n")

with open(f"{OUT}/WB_Part1_Tracker.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["shot", "start", "end", "dur", "cue", "super", "characters", "grade", "prompt", "status"])
    w.writeheader()
    for s in shots:
        w.writerow({**s, "status": "To generate"})

ep = {
    "series": "Warren Buffett", "part": 1, "intro": "assets/Intro_Video.mp4", "title_at": 22.6,
    "target_minutes": [4, 5.5],
    "teaser": [{"src": "clips/s043.mp4", "start": 0.5, "dur": 3}, {"src": "clips/s060.mp4", "start": 0.5, "dur": 3},
               {"src": "clips/s073.mp4", "start": 0.5, "dur": 3}],
    "scenes": [{"src": f"clips/{s['shot']}.mp4", "start": 0.3, "dur": s["dur"]} for s in shots],
    "supers": [{"at": s["start"], "dur": min(3.0, s["dur"]), "text": s["super"]} for s in shots if s["super"]],
    "voiceover": "audio/WB_Part1_VO.mp3", "voiceover_delay": 0,
    "output": "out/WarrenBuffett_Part1.mp4",
}
json.dump(ep, open(f"{OUT}/episode.json", "w"), indent=1)
print(len(shots), "shots; total", round(sum(s["dur"] for s in shots), 1), "s; max slot",
      max(s["dur"] for s in shots), "min slot", min(s["dur"] for s in shots))
