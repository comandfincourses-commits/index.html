# Style guide — the editing grammar of the reference video

Source analysed: "Explaining Basic Financial Concepts YOU Should Understand" (12:14, 1280×720, 30 fps). I sampled frames every 10 s, inspected key sections at 2–8 fps and ran ffmpeg scene-cut detection. These are the rules the video follows. Copy the grammar, not the artwork.

## 1. Pacing (the most important rule)
- **344 hard cuts in 12.2 min → average shot of 2.1 s.** Many shots are 0.5–1.5 s; few run past 5 s.
- Cuts land on **phrase boundaries**: a new clause or idea means a new picture.
- **Transitions are hard cuts.** No dissolves, wipes or zoom transitions between scenes. The energy comes from cutting, not from effects.
- Within a shot, things **build**: a label appears, an arrow draws, a second object pops in on the spoken word. A long shot is acceptable only if it keeps building.

## 2. Shot types and mix (approximate share of runtime)
| Shot type | Share | What it looks like | Use for |
|---|---|---|---|
| **Kinetic text card** | ~25% | Plain yellow, black hand-lettered caps, words appear one at a time *as spoken*, key word in red | Transitions ("Here's the deal", "Now comes…"), punchlines, definitions, rhetorical questions |
| **Character + prop** | ~35% | Recurring stick figure (round white head, dot eyes) with 1–2 props, expression matches the line | Personal-finance situations: earning, spending, worrying, deciding |
| **Metaphor scene** | ~20% | Full illustrated scene: vault with sleeping dragon, burning cash, money plant being watered | Abstract ideas made concrete (risk, growth, inflation, debt) |
| **Data visual** | ~10% | Gauge (credit score), price tags, phone screen (pay stub, bank balance), boxes labelled "Simple" vs "Compound" | Numbers, comparisons, ranges |
| **Split / comparison** | ~10% | Two panels or a left-vs-right layout (Gucci $3000 vs Target $30; lender ↔ you) | Contrasts and trade-offs |

## 3. Visual language
- **Background:** flat yellow `#FDCF3F` is home base (about 60% of shots). Use a different background only to change mood: navy at night (stress or late-night thoughts), room or desk (a domestic situation), street or office (the world outside).
- **Line art:** uniform thick black outlines (about 6 px at 1080p), round joins, flat fills, no gradients, almost no shadows.
- **Character:** one recurring everyman with a white round head, big round eyes with black pupils, a small curl of hair and a coloured T-shirt. Keep the outfit consistent; supporting cast are distinguished by hair and clothes (pink bob, suit, cap). The expression always matches the line: worried at bills, happy when compounding pays off, shocked at big numbers.
- **Typography:** rounded hand-lettered ALL CAPS (we use **Mali Bold**). Black on yellow, with **one or two key words in red `#E53935`**. Text sits centred, or in the top third above an illustration. Big single-word punches ("BOOM", "OPEN") use a heavier display face (we use **Luckiest Guy**).
- **Colour accents:** money green `#43A047`, warning red `#E53935`, trust blue `#2F6FD6`, gold `#F5B800`. Use few colours per frame.
- **Composition:** one focal subject, generous empty space and centred framing. Labels sit directly above the object they name.

## 4. Motion
- **Pop-in** (scale overshoot, about 0.35 s) is the default entrance for props, characters and cards.
- **Slide in from the edge** for things that arrive: a hand passing money, a phone rising into view, a person walking in.
- **Word-by-word reveal** for text cards, synced to the voice. Keep earlier words on screen so the sentence accumulates.
- **Progressive builds:** "Q1 Q2 Q3 Q4" appear one by one, an arrow points to a second image, a gauge needle swings to the value.
- **Camera:** mostly locked off. Use an occasional slow push for drama or a quick punch-in for a shock line. Don't move the camera constantly.
- **Life:** characters blink. Avoid constant wobble; the style is calm between cuts.

## 5. Audio
- Voice is up front and clear, with compression and a loudness of about -14 LUFS integrated.
- A light, cheerful background music bed runs continuously (the reference never drops below -45 dB in its pauses), ducked under speech.
- Subtle cartoon SFX: pops on entrances, whooshes on slides, a ding on reveals and a soft boom on punch titles. Keep SFX roughly 15–20 dB under the voice and never stack them.

## 6. Writing on screen
- Never put the whole narration on screen. Show the **keyword phrase** ("SOME PEOPLE PAY EVERY FEW MONTHS"), or a question ("NOW COMES FILING YOUR TAXES?"), or a number.
- Keep it under 12 words, and keep the on-screen words identical to the spoken ones so they sync.
- Treat numbers as heroes: show them big, animate them with a counter, and format them in the Indian system (₹3,10,585 / ₹1.2 crore).

## 7. Adapting for COMandFIN (finance education)
- Indian context by default: salary slips, EMI, SIP, PPF, CIBIL (300–900), GST, ITR filing, Sensex/Nifty, lakh/crore.
- Professional-level topics (valuation, IFRS, ratios) still use the same grammar: a character facing a real business situation, then the concept card, then the number build, then a takeaway text card.
- End with a takeaway card ("START EARLY. STAY INVESTED.") followed by the CTA (course or next video).
