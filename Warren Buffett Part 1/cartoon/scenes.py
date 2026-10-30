"""Warren Buffett | Part 1: 2D comic-style cartoon, 37 scenes timed to the 4:28 voiceover.
usage: python3 scenes.py out.mp4 [t0 t1]   or   python3 scenes.py --stills out.png t1,t2,..."""
import math, os, random, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *

DUR = 269.9


# ------------------------------------------------------------------ set helpers
def grad(d, box, top, bot):
    x0, y0, x1, y1 = box
    for y in range(int(y0), int(y1), 4):
        k = (y - y0) / max(1, y1 - y0)
        d.rectangle((x0, y, x1, y + 4), fill=tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)))


def wall(d, col, floor=None, fy=820):
    d.rectangle((0, 0, W, H), fill=col)
    if floor:
        d.rectangle((0, fy, W, H), fill=floor)
        d.line([(0, fy), (W, fy)], fill=INK, width=5)


def window(d, box, sky_top, sky_bot, frame=(120, 80, 50)):
    grad(d, box, sky_top, sky_bot)
    x0, y0, x1, y1 = box
    d.rectangle(box, outline=INK, width=6)
    rr(d, (x0 - 14, y0 - 14, x1 + 14, y1 + 14), 6, None, 14, frame)
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=frame, width=10)
    d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=frame, width=10)


def chalkboard(d, box, rows):
    x0, y0, x1, y1 = box
    rr(d, (x0 - 16, y0 - 16, x1 + 16, y1 + 16), 8, (125, 85, 50), 5)
    d.rectangle(box, fill=(45, 75, 60), outline=INK, width=4)
    for k, (name, price, col) in enumerate(rows):
        y = y0 + 50 + k * 70
        d.text((x0 + 40, y), name, font=hand(44), fill=(235, 235, 225), anchor="lm")
        d.text((x1 - 40, y), price, font=hand(50), fill=col, anchor="rm")


def counter(d, y=760, col=(140, 92, 55)):
    rr(d, (-20, y, W + 20, H + 20), 0, col, 6)
    d.rectangle((-20, y, W + 20, y + 34), fill=shade(col, 1.2), outline=INK, width=5)


def table(d, y=780, col=(150, 100, 60)):
    rr(d, (120, y, W - 120, y + 40), 10, shade(col, 1.15), 5)
    d.rectangle((120, y + 40, W - 120, H + 20), fill=col, outline=INK, width=5)


def brick_building(d, x, w, h, col, base=820, win_col=(255, 235, 170), seed=0):
    rnd = random.Random(seed)
    d.rectangle((x, base - h, x + w, base), fill=col, outline=INK, width=5)
    for r_ in range(int((h - 120) / 110)):
        for c_ in range(max(1, int((w - 40) / 110))):
            wx, wy = x + 30 + c_ * 110, base - h + 40 + r_ * 110
            lit = rnd.random() < 0.5
            d.rectangle((wx, wy, wx + 60, wy + 70), fill=win_col if lit else (90, 110, 140), outline=INK, width=4)


def old_car(d, x, y, col=(40, 40, 50), s=1.0):
    rr(d, (x - 150 * s, y - 60 * s, x + 150 * s, y + 10 * s), 30 * s, col, 5)
    rr(d, (x - 80 * s, y - 120 * s, x + 70 * s, y - 50 * s), 25 * s, col, 5)
    d.rectangle((x - 60 * s, y - 108 * s, x + 50 * s, y - 64 * s), fill=(170, 200, 220), outline=INK, width=3)
    for sx in (-1, 1):
        ell(d, x + sx * 90 * s, y + 10 * s, 34 * s, 34 * s, (30, 30, 30), 5)
        ell(d, x + sx * 90 * s, y + 10 * s, 12 * s, 12 * s, (190, 190, 190))


def rain(img, t, n=140, col=(200, 215, 235, 150)):
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(5)
    for _ in range(n):
        x0, y0, sp = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(700, 1100)
        y = (y0 + t * sp) % (H + 60) - 60
        x = (x0 - t * 60) % W
        d.line([(x, y), (x - 8, y + 34)], fill=col, width=3)


def crowd(img, t, n, y, R, seed=1, expr="shock", tops=((40, 42, 50), (70, 60, 50), (60, 70, 90))):
    rnd = random.Random(seed)
    for k in range(n):
        x = rnd.uniform(60, W - 60)
        key = "suit" if k % 3 else "clerk"
        C["tmp"] = dict(C[key]); C["tmp"]["top"] = tops[k % len(tops)]
        bust(img, "tmp", x, y + rnd.uniform(-30, 40), R * rnd.uniform(0.85, 1.1), t, expr, look=rnd.uniform(-1, 1), seed=k)


def coin(d, x, y, r=26):
    ell(d, x, y, r, r, (215, 175, 70), 4)
    ell(d, x, y, r * 0.65, r * 0.65, None, 3, (170, 130, 40))


def bottle(d, x, y, s=1.0):
    rr(d, (x - 16 * s, y - 70 * s, x + 16 * s, y + 40 * s), 10 * s, (120, 60, 50), 4)
    d.rectangle((x - 7 * s, y - 100 * s, x + 7 * s, y - 68 * s), fill=(120, 60, 50), outline=INK, width=3)
    d.rectangle((x - 16 * s, y - 20 * s, x + 16 * s, y), fill=(250, 250, 245), outline=INK, width=2)


def sixpack(d, x, y, s=1.0):
    for k in range(3):
        bottle(d, x - 50 * s + k * 50 * s, y - 20 * s, s)
    rr(d, (x - 90 * s, y - 30 * s, x + 90 * s, y + 40 * s), 8, (190, 150, 95), 4)


def newspaper(d, x, y, w=420, h=300, headline="", sub=""):
    rr(d, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), 6, (245, 240, 225), 5)
    if headline:
        d.text((x, y - h / 2 + 50), headline, font=bold(int(h * 0.15)), fill=INK, anchor="mm")
    for k in range(5):
        yy = y - h / 2 + 110 + k * 32
        d.line([(x - w / 2 + 30, yy), (x + (w / 2 - 30) * (0.3 if k == 4 else 1), yy)], fill=(150, 150, 150), width=8)
    if sub:
        d.text((x, y + h / 2 - 40), sub, font=hand(int(h * 0.14)), fill=(40, 120, 60), anchor="mm")


def sun_rays(img, cx, cy, t, a=1.0, col=(255, 225, 140)):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(14):
        ang = k / 14 * math.tau + t * 0.05
        d.polygon([(cx, cy), (cx + math.cos(ang - 0.06) * 2400, cy + math.sin(ang - 0.06) * 2400),
                   (cx + math.cos(ang + 0.06) * 2400, cy + math.sin(ang + 0.06) * 2400)], fill=col + (int(60 * a),))
    img.alpha_composite(lay)


# ------------------------------------------------------------------ scenes
SC = []


def scene(t0, t1, zoom=(1.0, 1.06), focus=(W / 2, H / 2)):
    def deco(fn):
        SC.append(dict(t0=t0, t1=t1, fn=fn, zoom=zoom, focus=focus))
        return fn
    return deco


def talking(t, spans):
    return any(a <= t < b for a, b in spans)


STOCKS = [("STEEL CO.", "52", (235, 235, 225)), ("RAILWAY", "17", (235, 235, 225)), ("CITIES SVC PFD", "38", (255, 230, 120))]


@scene(0.0, 5.8, focus=(1250, 450))
def w01(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (205, 190, 160))
    chalkboard(d, (200, 90, 1100, 420), STOCKS)
    bust(img, "clerk", 560, 470, 130, t, "neutral", talk=False, seed=3)
    bust(img, "boy11", 1350, 500, 130, t, "neutral", talk=talking(t, [(1.0, 3.5)]), look=-0.6, arms="hold", seed=1)
    counter(d, 760)
    for k in range(6):
        cx = lerp = 1220 - min(1, max(0, (lt - 2.5) / 2)) * 500
        coin(d, cx + k * 30, 790 + (k % 2) * 6, 22)
    bubble(img, "All my savings...", 1350, 160, 56, tail=(1360, 320), a=pop(lt, 0.4))
    bubble(img, "...in ONE share!", 1350, 160, 56, tail=(1360, 320), a=pop(lt, 2.6)) if lt > 2.6 else None


@scene(5.8, 11.6, focus=(700, 300))
def w02(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (190, 185, 175))
    price = "38" if lt < 1.5 else ("31" if lt < 2.4 else "27")
    rows = STOCKS[:2] + [("CITIES SVC PFD", price, (255, 120, 110) if lt > 1.5 else (255, 230, 120))]
    chalkboard(d, (120, 90, 1020, 420), rows)
    if lt > 1.5:
        d.line([(780, 260), (850, 360)], fill=(255, 120, 110), width=8)
        poly(d, [(850, 375), (825, 340), (868, 345)], (255, 120, 110))
    bust(img, "boy11", 1400, 470, 150, t, "worried" if lt < 4.2 else "sad", talk=talking(lt, [(1.0, 2.2), (4.4, 5.4)]), look=-0.8, seed=1)
    bubble(img, "It's falling!", 1450, 150, 60, tail=(1430, 300), a=pop(lt, 1.2)) if lt < 4.2 else bubble(img, "Sell it! SELL!", 1450, 150, 60, tail=(1430, 300), a=pop(lt, 4.2))


@scene(11.6, 15.5, zoom=(1.0, 1.12), focus=(960, 380))
def w03(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (120, 140, 150))
    label(img, "A few years later...", 960, 90, 64, a=pop(lt, 0.1))
    bust(img, "boy11", 960, 380, 150, t, "shock" if lt > 1.0 else "neutral", seed=1)
    newspaper(d, 960, 860, 760, 360, "STOCK PAGE", "CITIES SVC PFD  $200")
    if lt > 1.2:
        label(img, "$200 !", 1500, 360, 120, (255, 220, 90), pop(lt, 1.2), font=bold(120))


@scene(15.5, 22.5, focus=(960, 420))
def w04(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (70, 60, 80))
    window(d, (560, 120, 1360, 700), (250, 150, 110), (90, 70, 130))
    for k in range(9):
        x = 560 + k * 95
        hh = 120 + (k * 37) % 90
        d.rectangle((x, 700 - hh, x + 90, 700), fill=(40, 35, 60))
        poly(d, [(x - 5, 700 - hh), (x + 45, 700 - hh - 50), (x + 95, 700 - hh)], (40, 35, 60))
    bust(img, "boy11", 960, 640, 150, t, "neutral", look=0.3, seed=1)
    bubble(img, "Lesson: be patient.", 1500, 260, 58, tail=(1100, 520), kind="thought", a=pop(lt, 1.5))


@scene(22.5, 29.5, focus=(960, 600))
def w05(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 820), (255, 200, 140), (250, 170, 120))
    cols = [(170, 80, 60), (150, 95, 70), (185, 110, 75), (140, 70, 55), (165, 100, 80)]
    x = -40
    for k in range(7):
        w_ = 260 + (k * 53) % 120
        brick_building(d, x, w_, 380 + (k * 71) % 220, cols[k % 5], seed=k)
        rr(d, (x + 20, 600, x + w_ - 20, 650), 6, ((200, 60, 60), (60, 120, 160), (230, 190, 80))[k % 3], 4)
        x += w_ + 10
    d.rectangle((0, 820, W, H), fill=(120, 115, 110)); d.line([(0, 820), (W, 820)], fill=INK, width=5)
    d.rectangle((0, 820, W, 860), fill=(170, 165, 160), outline=INK, width=4)
    old_car(d, 500 + lt * 40, 960, (40, 50, 70))
    old_car(d, 1500 - lt * 25, 970, (110, 30, 30), 0.9)


@scene(29.5, 35.0, zoom=(1.0, 1.04))
def w06(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (232, 222, 200))
    label(img, "The Warren Buffett Story", 960, 100, 76, (255, 225, 120), pop(lt, 0))
    items = [("boy11", "PART 1", "The Beginning"), ("young20", "PART 2", "The Struggle"), ("oldwb", "PART 3", "Oracle of Omaha")]
    for k, (key, p, ttl) in enumerate(items):
        a = pop(lt, 0.5 + k * 0.8)
        if a <= 0:
            continue
        x = 400 + k * 560
        rr(d, (x - 220, 200, x + 220, 860), 18, (255, 252, 240) if k == 0 else (245, 240, 228), 6)
        sub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bust(sub, key, x, 420, 120, t, "happy" if k != 1 else "neutral", seed=k)
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle((x - 214, 206, x + 214, 700), 14, fill=255)
        img.paste(sub, (0, 0), Image.composite(sub.getchannel("A"), Image.new("L", (W, H), 0), mask))
        d.rectangle((x - 214, 700, x + 214, 854), fill=(255, 252, 240))
        d.text((x, 745), p, font=bold(46), fill=(200, 140, 40) if k == 0 else (120, 120, 120), anchor="mm")
        d.text((x, 805), ttl, font=hand(48), fill=INK, anchor="mm")
    if lt > 2.5:
        bubble(img, "You are here!", 400, 940, 44, kind="caption", a=pop(lt, 2.5))


@scene(35.0, 43.8)
def w07(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (250, 235, 205))
    bust(img, "boy6", 560, 480, 160, t, "happy", talk=talking(lt, [(0.5, 3.5)]), arms="raise", seed=2)
    s = 1 + 0.04 * math.sin(lt * 7)
    a = pop(lt, 0.8)
    if a > 0:
        rr(d, (1100 - 300 * s, 380 - 80 * s, 1100 + 300 * s, 380 + 80 * s), 80, (220, 30, 30), 6)
        d.text((1100, 385), "SUBSCRIBE", font=bold(int(80 * s)), fill=(255, 255, 255), anchor="mm")
    if lt > 2.0:
        ang = math.sin(lt * 18) * (18 if lt > 4.3 else 4)
        b = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
        bd.pieslice((50, 30, 250, 230), 180, 360, fill=(255, 205, 60), outline=INK, width=6)
        bd.polygon([(50, 130), (250, 130), (275, 220), (25, 220)], fill=(255, 205, 60), outline=INK)
        bd.line([(25, 220), (275, 220)], fill=INK, width=6)
        ell(bd, 150, 240, 26, 22, (255, 205, 60), 5)
        img.alpha_composite(b.rotate(ang, center=(150, 40), resample=Image.BICUBIC), (1500, 270))
    bubble(img, "Hit the bell for Part 2!", 1150, 720, 58, kind="caption", a=pop(lt, 4.3))


@scene(43.8, 52.0, focus=(960, 450))
def w08(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (205, 225, 210), (180, 200, 190), 860)
    window(d, (1380, 120, 1780, 520), (190, 220, 245), (240, 245, 250))
    rr(d, (200, 640, 1100, 900), 30, (250, 250, 250), 6)
    bust(img, "mother", 600, 430, 130, t, "happy", seed=4)
    def baby(dd, x, y, R):
        ell(dd, x + 20, y - 40, 120, 70, (250, 250, 255), 5)
        ell(dd, x + 80, y - 60, 40, 40, SKIN, 4)
        dd.arc((x + 65, y - 60, x + 95, y - 40), 20, 160, fill=INK, width=3)
    baby(d, 600, 780, 130)
    bust(img, "father", 1180, 400, 130, t, "happy", talk=talking(lt, [(3.0, 5.2)]), look=-0.7, seed=5)
    bubble(img, "OMAHA, NEBRASKA · 30 AUG 1930", 960, 70, 50, kind="caption", a=pop(lt, 0.2))
    bubble(img, "It's a boy!", 1450, 230, 58, tail=(1260, 330), a=pop(lt, 3.0))


@scene(52.0, 60.8, zoom=(1.0, 1.1), focus=(960, 500))
def w09(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, H), (150, 150, 160), (100, 100, 110))
    for k in range(6):
        x = 160 + k * 320
        d.rectangle((x, 120, x + 80, 820), fill=(205, 200, 190), outline=INK, width=5)
    d.rectangle((60, 60, W - 60, 130), fill=(215, 210, 200), outline=INK, width=5)
    d.text((960, 98), "STOCK EXCHANGE", font=bold(50), fill=INK, anchor="mm")
    pts = [(300, 220), (500, 260), (620, 240), (800, 380), (1000, 460), (1250, 600), (1600, 700)]
    k = clamp((lt - 0.5) / 3.5)
    n = max(2, int(len(pts) * k) + 1)
    d.line(pts[:n], fill=(230, 50, 50), width=18, joint="curve")
    crowd(img, t, 9, 820, 95, seed=3, expr="shock")
    label(img, "1929: THE CRASH", 960, 200, 90, (255, 90, 80), pop(lt, 1.0), font=bold(90))
    if lt > 4.5:
        bubble(img, "The Great Depression", 960, 330, 58, kind="caption", a=pop(lt, 4.5))


@scene(60.8, 68.9, focus=(960, 520))
def w10(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, H), (95, 105, 120), (70, 75, 85))
    d.rectangle((300, 150, 1620, 820), fill=(175, 170, 160), outline=INK, width=6)
    poly(d, [(250, 160), (960, 40), (1670, 160)], (185, 180, 170), 6)
    d.text((960, 120), "BANK", font=bold(70), fill=INK, anchor="mm")
    for k in range(6):
        d.rectangle((370 + k * 220, 210, 420 + k * 220, 820), fill=(200, 195, 185), outline=INK, width=4)
    rr(d, (820, 430, 1100, 820), 6, (80, 60, 45), 5)
    d.rectangle((790, 520, 1130, 610), fill=(250, 245, 230), outline=INK, width=5)
    d.text((960, 565), "CLOSED", font=bold(64), fill=(210, 40, 40), anchor="mm")
    d.rectangle((0, 820, W, H), fill=(80, 80, 85))
    bust(img, "father", 1450, 560, 140, t, "sad", look=-0.5, seed=5)
    rain(img, t)
    bubble(img, "Even his father's bank shut down", 620, 930, 50, kind="caption", a=pop(lt, 2.8))


@scene(68.9, 77.0, focus=(960, 460))
def w11(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (45, 55, 85))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((300, 50, 1100, 850), fill=(255, 200, 120, 70))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80)))
    d.line([(700, 0), (700, 110)], fill=INK, width=4)
    ell(d, 700, 140, 60, 40, (255, 220, 140), 5)
    bust(img, "mother", 640, 460, 130, t, "worried", look=0.2, seed=4)
    bust(img, "father", 1320, 430, 135, t, "neutral" if lt < 2.2 else "happy", talk=talking(lt, [(2.4, 6.0)]), look=-0.6, seed=5)
    table(d, 790)
    rr(d, (520, 700, 620, 800), 12, (220, 235, 245, 180), 4)
    for k in range(3):
        coin(d, 700 + k * 50, 805, 20)
    bubble(img, "Money is tight...", 640, 160, 52, kind="caption", a=pop(lt, 0.2)) if lt < 2.2 else None
    bubble(img, "I'll start my own firm.", 1400, 150, 56, tail=(1380, 280), a=pop(lt, 2.4))


@scene(77.0, 85.6, focus=(900, 500))
def w12(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (200, 185, 150), (150, 110, 75), 860)
    d.rectangle((1200, 80, 1700, 380), fill=(250, 245, 230), outline=INK, width=5)
    d.text((1450, 140), "BUFFETT & CO.", font=bold(44), fill=INK, anchor="mm")
    d.line([(1260, 230), (1350, 200), (1450, 260), (1550, 170), (1640, 210)], fill=(40, 140, 70), width=8)
    def phone(dd, x, y, R):
        dd.rectangle((x - 8, y - 140, x + 8, y), fill=INK)
        ell(dd, x, y - 150, 26, 18, INK)
    bust(img, "father", 700, 380, 130, t, "neutral", talk=talking(lt, [(0.3, 8.6)]), arms="hold", seed=5, hold=phone)
    rr(d, (300, 640, 1100, 700), 8, (120, 80, 50), 5)
    d.rectangle((330, 700, 1070, 1100), fill=(110, 72, 45), outline=INK, width=5)
    bust(img, "boy6", 1350, 640, 120, t, "happy", look=-0.4, arms="hold", seed=2,
         hold=lambda dd, x, y, R: rr(dd, (x - 80, y - 60, x + 80, y + 40), 6, (250, 250, 240), 4))
    rnd = random.Random(int(lt * 3))
    for k in range(7):
        a = pop(lt, 0.6 + k * 0.4)
        label(img, rnd.choice(["5", "25", "30", "100", "7", "12"]), 1150 + (k * 97) % 600, 200 + (k * 73) % 300, 64, (255, 225, 120), a * 0.9)


def grocery(d):
    wall(d, (236, 214, 170), (150, 105, 70), 840)
    for row in range(3):
        y = 110 + row * 150
        d.rectangle((150, y + 110, 1770, y + 124), fill=(120, 80, 50), outline=INK, width=3)
        for k in range(26):
            px = 175 + k * 61
            col = [(200, 70, 60), (60, 120, 170), (230, 190, 70), (90, 150, 90), (210, 120, 60)][(k + row) % 5]
            rr(d, (px, y + 45, px + 44, y + 110), 6, col, 3)
            d.rectangle((px, y + 66, px + 44, y + 84), fill=(250, 240, 220))


@scene(85.6, 93.5, focus=(960, 520))
def w13(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grocery(d)
    bust(img, "grandpa", 1200, 400, 135, t, "happy", talk=talking(lt, [(0.8, 3.6)]), look=-0.7, seed=6)
    bust(img, "boy6", 640, 520, 125, t, "happy", look=0.7, seed=2)
    counter(d, 720)
    rr(d, (1500, 600, 1700, 720), 14, (205, 165, 80), 5)
    sixpack(d, 950 - min(1, max(0, (lt - 3.8) / 1.5)) * 230, 700)
    bubble(img, "OMAHA · 1936", 300, 70, 46, kind="caption", a=pop(lt, 0.1))
    bubble(img, "Six bottles... 25 cents.", 1450, 150, 56, tail=(1290, 280), a=pop(lt, 0.8))


@scene(93.5, 100.1, focus=(960, 520))
def w14(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 760), (170, 215, 245), (215, 235, 250))
    d.rectangle((0, 300, 1100, 820), fill=(235, 220, 190), outline=INK, width=5)
    poly(d, [(-40, 310), (550, 80), (1140, 310)], (170, 70, 60), 5)
    rr(d, (420, 420, 640, 820), 6, (120, 70, 45), 5)
    d.rectangle((0, 820, W, H), fill=(120, 180, 90)); d.rectangle((1100, 780, W, 860), fill=(190, 190, 185), outline=INK, width=4)
    bust(img, "lady", 530, 480, 115, t, "happy", look=0.7, seed=7)
    bust(img, "boy6", 1050, 560, 115, t, "happy", talk=talking(lt, [(0.4, 2.8)]), look=-0.7, seed=2)
    rr(d, (1200, 760, 1560, 840), 10, (180, 50, 40), 5)
    for k in range(5):
        bottle(d, 1250 + k * 65, 740, 0.9)
    for sx in (1260, 1500):
        ell(d, sx, 860, 34, 34, (40, 40, 40), 5)
    if lt > 3.0:
        coin(d, lerp_ := 640 + min(1, (lt - 3.0) / 1.0) * 330, 640, 26)
    bubble(img, "Only 5 cents each!", 1150, 160, 56, tail=(1080, 330), a=pop(lt, 0.4))


@scene(100.1, 106.5, focus=(960, 600))
def w15(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (55, 60, 90))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((400, 100, 1500, 1000), fill=(255, 200, 120, 70))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    bust(img, "boy6", 960, 380, 130, t, "happy", look=0.0, seed=2)
    table(d, 700)
    for k in range(6):
        if lt > 0.3 + k * 0.25:
            coin(d, 620 + k * 80, 760, 30)
    rr(d, (1080, 720, 1480, 860), 6, (250, 250, 240), 4)
    lines = ["6 x 5c = 30c", "cost  - 25c", "PROFIT = 5c"]
    for k, l in enumerate(lines):
        if lt > 2.0 + k * 0.9:
            d.text((1280, 748 + k * 38), l, font=hand(40), fill=(30, 130, 60) if k == 2 else INK, anchor="mm")


@scene(106.5, 112.4, zoom=(1.0, 1.1), focus=(960, 560))
def w16(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (250, 225, 170))
    window(d, (500, 60, 1420, 560), (255, 220, 150), (255, 240, 200))
    d.rectangle((300, 640, 1620, 700), fill=(200, 160, 110), outline=INK, width=5)
    fill = min(1, lt / 5)
    rr(d, (820, 330, 1100, 650), 30, (220, 240, 250, 140), 6)
    for k in range(int(4 + fill * 30)):
        coin(d, 850 + (k * 53) % 220, 625 - (k // 5) * 26, 20)
    yc = 120 + ((lt * 500) % 300)
    coin(d, 960, yc, 24)
    for k, txt in enumerate(["Buy cheap.", "Sell at value.", "Repeat."]):
        bubble(img, txt, 300 + k * 660, 900, 60, kind="caption", a=pop(lt, 0.5 + k * 1.3))


@scene(112.4, 119.5, focus=(960, 450))
def w17(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (205, 190, 160))
    chalkboard(d, (1150, 90, 1820, 380), STOCKS[1:])
    bust(img, "sister", 520, 470, 125, t, "happy", talk=talking(lt, [(3.6, 6.0)]), look=0.6, seed=8)
    bust(img, "boy11", 940, 480, 125, t, "happy", look=0.6, seed=1)
    bust(img, "clerk", 1500, 460, 125, t, "neutral", look=-0.6, seed=3)
    counter(d, 760)
    rr(d, (1060, 790, 1420, 1000), 6, (245, 235, 205), 5)
    d.text((1240, 850), "3 SHARES", font=bold(44), fill=INK, anchor="mm")
    d.text((1240, 920), "$38 each", font=hand(48), fill=(40, 100, 160), anchor="mm")
    bubble(img, "OMAHA · 1942", 300, 70, 46, kind="caption", a=pop(lt, 0.1))
    bubble(img, "Half of it is mine!", 520, 170, 54, tail=(540, 320), a=pop(lt, 3.6))


@scene(119.5, 126.5, focus=(960, 480))
def w18(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (90, 70, 70), (70, 50, 45), 900)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((300, -100, 1600, 700), fill=(255, 210, 140, 80))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    bust(img, "sister", 600, 430, 135, t, "angry", talk=talking(lt, [(0.4, 4.5)]), arms="cross", look=0.5, seed=8)
    bust(img, "boy11", 1320, 470, 130, t, "sad", look=-0.3, seed=1)
    table(d, 780, (130, 80, 50))
    for x in (600, 1320):
        ell(d, x, 830, 120, 34, (250, 250, 250), 5)
    label(img, "$38  ->  $27", 960, 120, 80, (255, 120, 110), pop(lt, 0.1))
    bubble(img, "You lost our money!", 820, 260, 58, tail=(680, 350), a=pop(lt, 0.4))


@scene(126.5, 133.1, focus=(960, 400))
def w19(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (200, 190, 165))
    price = "40" if lt < 3.0 else "200"
    chalkboard(d, (150, 90, 1050, 420), STOCKS[:2] + [("CITIES SVC PFD", price, (140, 240, 150) if lt < 3.0 else (255, 225, 90))])
    shock = lt > 3.0
    bust(img, "boy11", 1420, 480, 150, t, "shock" if shock else "happy", talk=talking(lt, [(0.3, 2.4)]), look=-0.8, seed=1)
    if not shock:
        bubble(img, "Sold at $40. Phew!", 1450, 140, 56, tail=(1430, 300), a=pop(lt, 0.3))
    else:
        bubble(img, "A few years later...", 600, 520, 50, kind="caption", a=pop(lt, 3.0))
        bubble(img, "$200?!", 1450, 140, 72, tail=(1430, 300), a=pop(lt, 3.3))


@scene(133.1, 142.0, focus=(960, 480))
def w20(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (40, 45, 75))
    window(d, (1450, 120, 1800, 480), (20, 30, 70), (40, 50, 100))
    ell(d, 1700, 200, 40, 40, (250, 245, 210))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((100, 100, 1100, 1000), fill=(255, 210, 130, 70))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    bust(img, "boy11", 600, 470, 135, t, "neutral", look=0.3, arms="hold", seed=1,
         hold=lambda dd, x, y, R: rr(dd, (x - 90, y - 70, x + 90, y + 50), 6, (130, 60, 50), 4))
    rr(d, (1000, 560, 1820, 1000), 8, (250, 248, 235), 5)
    d.text((1410, 610), "MY RULES", font=bold(46), fill=INK, anchor="mm")
    if lt > 3.9:
        d.text((1050, 700), "1. Don't fixate on the", font=hand(48), fill=INK, anchor="lm")
        d.text((1095, 755), "price you paid.", font=hand(48), fill=INK, anchor="lm")
    if lt > 6.9:
        d.text((1050, 850), "2. Don't rush.", font=hand(52), fill=(190, 40, 40), anchor="lm")


@scene(142.0, 150.5, focus=(960, 500))
def w21(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 640), (255, 170, 110), (255, 220, 150))
    ell(d, 1500, 560, 140, 140, (255, 235, 160))
    d.rectangle((0, 600, W, H), fill=(225, 175, 70))
    for k in range(60):
        x = (k * 37) % W
        d.line([(x, 640 + (k * 13) % 400), (x + 6, 600 + (k * 13) % 400)], fill=(200, 145, 50), width=4)
    d.rectangle((0, 780, W, 810), fill=(150, 100, 60), outline=INK, width=4)
    for k in range(8):
        d.rectangle((60 + k * 260, 700, 90 + k * 260, 960), fill=(150, 100, 60), outline=INK, width=4)
    bust(img, "boy11", 900, 430, 130, t, "happy", look=0.4, seed=1)
    bubble(img, "Patience = real money", 960, 110, 64, kind="caption", a=pop(lt, 0.2))
    if lt > 2.3:
        for k, (txt, col) in enumerate([("LIKE", (30, 110, 220)), ("SHARE", (40, 170, 110))]):
            a = pop(lt, 2.3 + k * 0.6)
            x = 1400 + k * 320
            rr(d, (x - 140, 820, x + 140, 920), 50, col + (int(255 * a),), 5)
            d.text((x, 872), txt, font=bold(52), fill=(255, 255, 255, int(255 * a)), anchor="mm")


@scene(150.5, 159.0, focus=(960, 450))
def w22(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, H), (150, 185, 225), (210, 225, 240))
    for x in (250, 1670):
        d.line([(x, 120), (x, 760)], fill=INK, width=8)
        sg = 1 if x < 900 else -1
        for k in range(7):
            xa, xb = sorted((x + 4 * sg, x + 260 * sg))
            d.rectangle((xa, 130 + k * 26, xb, 156 + k * 26), fill=(200, 40, 40) if k % 2 == 0 else (250, 250, 250))
        xa, xb = sorted((x + 4 * sg, x + 110 * sg))
        d.rectangle((xa, 130, xb, 234), fill=(40, 60, 140))
    bust(img, "father", 960, 330, 135, t, "happy", talk=talking(lt, [(0.5, 8.5)]), arms="raise", seed=5)
    rr(d, (720, 600, 1200, 1000), 10, (150, 100, 60), 6)
    d.rectangle((720, 640, 1200, 700), fill=(40, 60, 140))
    crowd(img, t, 8, 960, 90, seed=9, expr="happy")
    bubble(img, "1942: Elected to Congress", 960, 70, 54, kind="caption", a=pop(lt, 0.2))


@scene(159.0, 166.3, focus=(800, 500))
def w23(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, H), (110, 120, 135), (90, 95, 110))
    ox = (lt * 120) % 500
    d.rectangle((900, 200, 1800, 760), fill=(150, 160, 175))
    ell(d, 1380 - ox * 0.3, 470, 200, 140, (235, 235, 230), 5)
    d.rectangle((1180 - ox * 0.3, 470, 1580 - ox * 0.3, 640), fill=(235, 235, 230), outline=INK, width=5)
    d.rectangle((1360 - ox * 0.3, 280, 1400 - ox * 0.3, 340), fill=(235, 235, 230), outline=INK, width=4)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rain(lay, t, 90)
    img.alpha_composite(lay.crop((0, 0, W, H)))
    d.rectangle((0, 0, 900, H), fill=(60, 55, 60)); d.rectangle((1800, 0, W, H), fill=(60, 55, 60))
    d.rectangle((0, 0, W, 200), fill=(60, 55, 60)); d.rectangle((0, 760, W, H), fill=(60, 55, 60))
    d.rectangle((900, 200, 1800, 760), outline=INK, width=10)
    bust(img, "teen14", 520, 520, 140, t, "sad", look=0.9, seed=10)
    bubble(img, "WASHINGTON, D.C.", 1350, 120, 50, kind="caption", a=pop(lt, 0.2))
    if lt > 4.5:
        bubble(img, "Grades: D", 520, 180, 60, kind="thought", tail=(540, 360), a=pop(lt, 4.5))


@scene(166.3, 173.5, zoom=(1.0, 1.0))
def w24(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 700), (120, 140, 200), (250, 190, 160))
    for k in range(5):
        x = k * 420
        d.rectangle((x + 20, 330, x + 380, 760), fill=(200, 205, 225), outline=INK, width=5)
        poly(d, [(x, 340), (x + 200, 200), (x + 400, 340)], (120, 90, 110), 5)
        rr(d, (x + 150, 560, x + 250, 760), 6, (110, 80, 60), 4)
    d.rectangle((0, 760, W, H), fill=(110, 110, 120)); d.line([(0, 760), (W, 760)], fill=INK, width=5)
    bx = -300 + lt * 330
    for sx in (-1, 1):
        ell(d, bx + sx * 110, 960, 80, 80, None, 10)
    d.line([(bx - 110, 960), (bx, 900), (bx + 110, 960), (bx + 20, 860), (bx - 40, 860)], fill=(200, 40, 40), width=10)
    bust(img, "teen14", bx, 620, 95, t, "neutral", look=1, seed=10)
    rr(d, (bx - 120, 780, bx - 30, 860), 8, (190, 170, 120), 4)
    for k in range(4):
        if lt > 1 + k * 1.3:
            p = (lt - 1 - k * 1.3)
            nx, ny = 420 + k * 420 - p * 40, 860 - p * 220 + p * p * 160
            if ny < 900:
                rr(d, (nx - 40, ny - 14, nx + 40, ny + 14), 6, (245, 240, 225), 4)
    label(img, "~500 newspapers every morning", 960, 120, 70, (255, 255, 255), pop(lt, 1.5))


@scene(173.5, 180.7, focus=(960, 520))
def w25(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (50, 60, 90))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((300, 100, 1400, 1000), fill=(255, 205, 130, 70))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    for sx in (-1, 1):
        ell(d, 1600 + sx * 120, 640, 90, 90, None, 10)
    d.line([(1480, 640), (1600, 560), (1720, 640), (1620, 480), (1560, 480)], fill=(200, 40, 40), width=10)
    bust(img, "teen14", 720, 400, 130, t, "happy", talk=talking(lt, [(3.5, 6.5)]), look=0.5, seed=10)
    table(d, 720)
    rr(d, (900, 740, 1340, 1000), 6, (250, 248, 235), 5)
    d.text((1120, 780), "TAX RETURN", font=bold(36), fill=INK, anchor="mm")
    if lt > 2.0:
        d.text((930, 850), "Bicycle .... $35", font=hand(44), fill=(30, 110, 60), anchor="lm")
    bubble(img, "Age 13: first tax return", 960, 70, 52, kind="caption", a=pop(lt, 0.1))
    bubble(img, "My bike is a business expense!", 700, 190, 50, tail=(720, 300), a=pop(lt, 3.5))


def pinball(d, x, y, s=1.0, lit=0.0):
    poly(d, [(x - 120 * s, y - 120 * s), (x + 120 * s, y - 120 * s), (x + 150 * s, y + 60 * s), (x - 150 * s, y + 60 * s)], (130, 50, 160), 5)
    rr(d, (x - 130 * s, y - 260 * s, x + 130 * s, y - 120 * s), 10, (40, 40, 80), 5)
    for k, (ox, oy) in enumerate([(-50, -80), (40, -60), (0, -10)]):
        on = int(lit * 3 + k) % 2
        ell(d, x + ox * s, y + oy * s, 26 * s, 26 * s, (255, 220, 80) if on else (200, 150, 60), 4)
    for sx in (-1, 1):
        d.rectangle((x + sx * 130 * s - 10, y + 60 * s, x + sx * 130 * s + 10, y + 200 * s), fill=(150, 150, 150), outline=INK, width=3)


@scene(180.7, 188.3, focus=(960, 500))
def w26(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (150, 135, 115), (110, 95, 80), 860)
    for k in range(6):
        rr(d, (80 + k * 300, 120 + (k % 2) * 60, 300 + k * 300, 360 + (k % 2) * 60), 8, (125, 110, 95), 4)
    pinball(d, 960, 620, 1.3)
    rr(d, (1100, 300, 1250, 380), 8, (250, 240, 200), 4)
    d.text((1175, 340), "$25", font=bold(48), fill=(200, 40, 40), anchor="mm")
    bust(img, "teen14", 450, 520, 130, t, "happy", talk=talking(lt, [(2.5, 5.0)]), look=0.6, seed=10)
    bust(img, "friend", 1480, 520, 130, t, "happy", look=-0.6, seed=11)
    bubble(img, "Let's buy it!", 450, 200, 58, tail=(460, 360), a=pop(lt, 2.5))


@scene(188.3, 196.5, focus=(960, 500))
def w27(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (230, 240, 240), (200, 200, 210), 860)
    for k in range(8):
        d.rectangle((k * 260, 860, k * 260 + 130, 900), fill=(40, 40, 40))
    rr(d, (1350, 120, 1800, 500), 12, (220, 235, 245), 6)
    n = 1 if lt < 3.6 else (3 if lt < 4.6 else 5)
    for k in range(n):
        pinball(d, 330 + k * 300 if n > 1 else 600, 640, 0.75 if n > 1 else 1.1, lt * 2)
    if n == 1:
        bust(img, "clerk", 1050, 450, 110, t, "happy", look=-0.8, seed=12)
        coin(d, 600, 360 + (lt * 300) % 200, 22)
    if lt > 6.4:
        label(img, "Sold for $1,200!", 960, 150, 96, (120, 230, 140), pop(lt, 6.4), font=bold(96))
    else:
        bubble(img, "Customers played while they waited", 960, 120, 50, kind="caption", a=pop(lt, 0.2))


@scene(196.5, 205.0, focus=(960, 500))
def w28(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 560), (255, 190, 120), (255, 230, 170))
    d.rectangle((0, 520, W, H), fill=(205, 170, 70))
    for k in range(90):
        x, y = (k * 47) % W, 560 + (k * 29) % 520
        d.line([(x, y), (x + 8 + math.sin(t * 2 + k) * 6, y - 40)], fill=(170, 130, 40), width=4)
    bust(img, "teen14", 960, 470, 140, t, "happy", look=0.2, arms="raise", seed=10)
    bubble(img, "His own 40-acre farm in Nebraska", 960, 110, 56, kind="caption", a=pop(lt, 0.3))


@scene(205.0, 212.0, zoom=(1.0, 1.0))
def w29(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 560), (255, 200, 140), (255, 235, 180))
    d.rectangle((0, 520, W, H), fill=(190, 160, 70))
    for k in range(12):
        d.line([(0, 560 + k * 45), (W, 540 + k * 45)], fill=(160, 125, 50), width=5)
    tx = -300 + lt * 330
    rr(d, (tx - 160, 640, tx + 120, 780), 16, (200, 50, 40), 5)
    rr(d, (tx + 40, 560, tx + 120, 660), 8, (200, 50, 40), 5)
    ell(d, tx - 120, 820, 110, 110, (40, 40, 40), 6); ell(d, tx - 120, 820, 40, 40, (230, 190, 70))
    ell(d, tx + 90, 840, 70, 70, (40, 40, 40), 6); ell(d, tx + 90, 840, 25, 25, (230, 190, 70))
    bust(img, "suit", tx - 60, 520, 85, t, "happy", seed=13)
    bubble(img, "Rented out: income while he studied", 960, 110, 52, kind="caption", a=pop(lt, 0.4))


@scene(212.0, 218.7, focus=(960, 450))
def w30(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 640), (160, 200, 240), (220, 235, 250))
    d.rectangle((0, 600, W, H), fill=(110, 170, 90))
    d.rectangle((200, 200, 800, 600), fill=(190, 110, 80), outline=INK, width=5)
    poly(d, [(170, 210), (500, 80), (830, 210)], (170, 90, 70), 5)
    bust(img, "young20", 900, 420, 135, t, "happy", seed=14)
    poly(d, [(900 - 170, 290), (900, 230), (900 + 170, 290), (900, 340)], INK)
    d.line([(1050, 290), (1080, 380)], fill=(230, 190, 60), width=6)
    bust(img, "father", 1450, 430, 130, t, "happy", talk=talking(lt, [(2.2, 4.5)]), look=-0.7, seed=5)
    bubble(img, "1950: Graduated at 19", 960, 70, 54, kind="caption", a=pop(lt, 0.2))
    bubble(img, "Proud of you, son!", 1500, 200, 52, tail=(1480, 300), a=pop(lt, 2.2))


@scene(218.7, 224.5, focus=(960, 480))
def w31(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (120, 80, 55))
    for k in range(7):
        d.rectangle((k * 280, 0, k * 280 + 18, H), fill=(100, 65, 45))
    rr(d, (700, 110, 1220, 220), 10, (180, 30, 40), 5)
    d.text((960, 165), "HARVARD", font=bold(60), fill=(255, 255, 255), anchor="mm")
    bust(img, "prof", 500, 470, 135, t, "angry", talk=talking(lt, [(1.0, 4.5)]), look=0.7, seed=15)
    bust(img, "young20", 1420, 480, 135, t, "worried", look=-0.7, seed=14)
    table(d, 780, (90, 60, 40))
    bubble(img, "Hmm. We'll let you know.", 640, 300, 50, tail=(560, 380), a=pop(lt, 1.0))


@scene(224.5, 230.4, zoom=(1.0, 1.12), focus=(960, 560))
def w32(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=(70, 60, 55))
    ox = (lt * 400) % 600
    grad(d, (1100, 120, 1800, 600), (150, 160, 170), (120, 130, 140))
    for k in range(5):
        x = 1100 + ((k * 260 - ox) % 900)
        ell(d, x, 560, 90, 60, (90, 110, 90))
    d.rectangle((1100, 120, 1800, 600), outline=INK, width=12)
    bust(img, "young20", 700, 430, 135, t, "sad", look=0.3, arms="hold", seed=14,
         hold=lambda dd, x, y, R: rr(dd, (x - 140, y - 110, x + 140, y + 90), 6, (250, 248, 235), 5))
    d2 = ImageDraw.Draw(img, "RGBA")
    d2.text((700, 760), "We regret to inform you...", font=hand(34), fill=INK, anchor="mm")
    if lt > 1.0:
        a = pop(lt, 1.0, 0.2)
        s_ = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(s_)
        rr(sd, (420, 600, 1000, 720), 12, None, 10, (220, 40, 40, int(255 * a)))
        sd.text((710, 662), "REJECTED", font=bold(int(90 + (1 - a) * 60)), fill=(220, 40, 40, int(255 * a)), anchor="mm")
        img.alpha_composite(s_.rotate(-10, center=(710, 660), resample=Image.BICUBIC))


@scene(230.4, 238.9, focus=(960, 500))
def w33(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    k = clamp((lt - 4.0) / 1.5)
    grad(d, (0, 0, W, 700), (int(100 + 150 * k), int(110 + 110 * k), int(130 + 40 * k)), (int(130 + 120 * k), int(135 + 100 * k), int(150 + 40 * k)))
    d.rectangle((0, 700, W, H), fill=(90, 120, 80))
    poly(d, [(800, H), (1120, H), (1000, 700), (920, 700)], (170, 160, 150))
    for x in (200, 500, 1450, 1750):
        d.rectangle((x - 15, 420, x + 15, 760), fill=(90, 65, 45), outline=INK, width=3)
        for j in range(5):
            d.line([(x, 470 + j * 40), (x + (-1) ** j * 90, 420 + j * 40)], fill=(90, 65, 45), width=6)
    if k > 0:
        sun_rays(img, 1500, 0, t, k)
    bust(img, "young20", 960, 520, 140, t, "sad" if k < 0.5 else "neutral", look=0 if k < 0.5 else 0.5, seed=14)
    if k < 1:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rain(lay, t, int(160 * (1 - k)))
        img.alpha_composite(lay)
    bubble(img, "He could have given up...", 960, 120, 56, kind="caption", a=pop(lt, 0.3)) if lt < 4.0 else \
        bubble(img, "...but it became his turning point.", 960, 120, 56, kind="caption", a=pop(lt, 4.0))


@scene(238.9, 245.3, focus=(1100, 500))
def w34(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (90, 60, 45))
    for row in range(4):
        y = 120 + row * 220
        d.rectangle((0, y + 190, W, y + 205), fill=(70, 45, 30))
        for k in range(30):
            x = 10 + k * 64
            col = [(150, 50, 50), (60, 90, 140), (60, 120, 80), (170, 130, 60), (110, 70, 110)][(k * 7 + row) % 5]
            rr(d, (x, y + 40 + (k % 3) * 12, x + 54, y + 190), 4, col, 3)
    glow = pop(lt, 0.8, 1.0)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse((1150, 250, 1550, 650), fill=(255, 230, 140, int(150 * glow)))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(50)))
    rr(d, (1290, 330, 1410, 570), 6, (40, 70, 160), 5)
    bust(img, "young20", 700, 520, 140, t, "shock" if lt > 1.5 else "neutral", look=0.9, arms="point", seed=14)
    bubble(img, "A book...", 1350, 140, 64, kind="caption", a=pop(lt, 1.0))
    if lt > 3.0:
        bubble(img, "...and a guru who changed everything", 1400, 950, 52, kind="caption", a=pop(lt, 3.0))


@scene(245.3, 252.5, focus=(960, 520))
def w35(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    wall(d, (35, 40, 65))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((450, 250, 1450, 1150), fill=(255, 215, 130, 100))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    bust(img, "young20", 960, 420, 140, t, "happy", seed=14)
    table(d, 760, (110, 75, 50))
    rr(d, (780, 700, 1140, 800), 8, (40, 70, 160), 5)
    d.line([(960, 700), (960, 800)], fill=(250, 248, 235), width=8)
    d.line([(1300, 760), (1400, 560), (1300, 520)], fill=INK, width=8)
    poly(d, [(1260, 520), (1360, 480), (1380, 560)], (60, 60, 60), 5)
    a = pop(lt, 1.5)
    if a > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ell(ld, 1500, 260, 150, 120, (255, 255, 255, int(230 * a)), 5, INK + (int(255 * a),))
        ell(ld, 1500, 240, 45, 45, (130, 130, 140, int(255 * a)))
        rr(ld, (1440, 285, 1560, 345), 30, (130, 130, 140, int(255 * a)))
        ld.text((1500, 236), "?", font=bold(60), fill=(255, 255, 255, int(255 * a)), anchor="mm")
        for k, s in enumerate((24, 14)):
            ell(ld, 1360 - k * 60, 380 + k * 40, s, s * 0.8, (255, 255, 255, int(230 * a)), 4, INK + (int(255 * a),))
        img.alpha_composite(lay)
    if lt > 2.2:
        label(img, "THAT STORY IS IN PART 2", 960, 950, 76, (255, 225, 120), pop(lt, 2.2), font=bold(70))


@scene(252.5, 261.0, focus=(960, 520))
def w36(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 620), (255, 175, 110), (255, 225, 160))
    ell(d, 960, 600, 160, 160, (255, 240, 170))
    sun_rays(img, 960, 600, t, 0.8)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 600, W, H), fill=(170, 150, 80))
    poly(d, [(600, H), (1320, H), (990, 600), (930, 600)], (90, 90, 95))
    bust(img, "young20", 960, 560, 150, t, "happy", seed=14)
    if lt < 3.6:
        bubble(img, "Rejection is not the end.", 960, 140, 64, kind="caption", a=pop(lt, 0.2))
    else:
        bubble(img, "Faced rejection? Comment:", 960, 110, 48, kind="caption", a=pop(lt, 3.6))
        bubble(img, "“Main rukunga nahi!”", 1420, 330, 64, tail=(1080, 470), a=pop(lt, 4.1))


@scene(261.0, 269.9, zoom=(1.0, 1.0))
def w37(img, lt, t):
    d = ImageDraw.Draw(img, "RGBA")
    grad(d, (0, 0, W, 700), (60, 70, 120), (240, 150, 120))
    for k in range(14):
        x = 900 + k * 75
        hh = 150 + (k * 61) % 260
        d.rectangle((x, 640 - hh, x + 65, 640), fill=(50, 50, 80))
        for j in range(int(hh / 50)):
            d.rectangle((x + 15, 640 - hh + 20 + j * 50, x + 30, 640 - hh + 35 + j * 50), fill=(255, 220, 140))
    d.rectangle((0, 640, W, H), fill=(80, 70, 70))
    d.line([(0, 780), (W, 780)], fill=(150, 150, 150), width=10)
    tx = 200 + lt * 120
    rr(d, (tx - 700, 560, tx, 760), 20, (40, 60, 90), 6)
    for k in range(5):
        rr(d, (tx - 660 + k * 130, 600, tx - 560 + k * 130, 670), 8, (255, 225, 150), 4)
    for k in range(6):
        ell(d, tx - 640 + k * 120, 770, 34, 34, (30, 30, 30), 5)
    ell(d, tx - 80 - lt * 30, 480 - lt * 10, 60 + lt * 6, 40 + lt * 4, (230, 230, 230, 160))
    for k, (s, col) in enumerate([("LIKE", (30, 110, 220)), ("SHARE", (40, 170, 110)), ("SUBSCRIBE", (210, 30, 30))]):
        a = pop(lt, 0.2 + k * 0.4)
        x = 480 + k * 480
        rr(d, (x - 190, 830, x + 190, 940), 55, col + (int(255 * a),), 5)
        d.text((x, 886), s, font=bold(52), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    if lt > 1.8:
        label(img, "PART 2: The real struggle begins", 960, 150, 84, (255, 225, 120), pop(lt, 1.8), font=bold(76))


# ------------------------------------------------------------------ render
def frame(t):
    for s in SC:
        if s["t0"] <= t < s["t1"]:
            lt = t - s["t0"]
            img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            s["fn"](img, lt, t)
            z = s["zoom"][0] + (s["zoom"][1] - s["zoom"][0]) * clamp(lt / (s["t1"] - s["t0"]))
            if z > 1.001:
                fx, fy = s["focus"]
                cw, ch = W / z, H / z
                x0 = clamp(fx - cw / 2, 0, W - cw); y0 = clamp(fy - ch / 2, 0, H - ch)
                img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
            return img.convert("RGB")
    return Image.new("RGB", (W, H), (0, 0, 0))


if __name__ == "__main__":
    if sys.argv[1] == "--stills":
        ts = [float(v) for v in sys.argv[3].split(",")]
        cols = 4
        rows = (len(ts) + cols - 1) // cols
        sheet = Image.new("RGB", (480 * cols, 270 * rows))
        for i, tt in enumerate(ts):
            sheet.paste(frame(tt).resize((480, 270)), ((i % cols) * 480, (i // cols) * 270))
        sheet.save(sys.argv[2]); sys.exit()
    out = sys.argv[1]
    a, b = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, DUR)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for n in range(int(a * FPS), int(b * FPS)):
        p.stdin.write(frame(n / FPS).tobytes())
        if n % (FPS * 30) == 0:
            print(f"{n / FPS:.0f}s", flush=True)
    p.stdin.close(); p.wait()
