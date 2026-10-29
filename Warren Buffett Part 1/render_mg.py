"""Warren Buffett | Part 1: motion-graphics documentary edit, timed to the 4:28 voiceover.
Renders a silent 1920x1080 / 30 fps story track; build_episode.py adds VO, teaser, intro and end card.
usage: python3 render_mg.py out.mp4 [start_s end_s]   (optional range for quick previews)"""
import math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
DUR = 270.0
CX, CY = W // 2, H // 2
NAVY, GOLD, GREEN, RED, WHITE, GREY = (13, 27, 52), (214, 170, 84), (40, 190, 130), (226, 72, 60), (245, 245, 245), (160, 170, 185)
F_SER = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
F_BLK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
F_BLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def app(lt, t0, d=0.5):
    return ease((lt - t0) / d)


def lerp(a, b, x):
    return a + (b - a) * x


def rgba(c, a):
    return (c[0], c[1], c[2], int(255 * clamp(a)))


# ---------- background: navy radial gradient, vignette, grain, drifting gold dust ----------
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - CX) / W) ** 2 + ((yy - CY) / H) ** 2)
g = np.clip(1 - r * 1.35, 0, 1)[..., None]
BG = (np.array([6, 12, 26]) + (np.array([24, 44, 78]) - np.array([6, 12, 26])) * g).astype(np.float32)
rng = np.random.default_rng(7)
GRAIN = [rng.normal(0, 5, (H, W, 1)).astype(np.float32) for _ in range(4)]
random.seed(3)
DUST = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4), random.uniform(6, 22), random.uniform(0, 6.28))
        for _ in range(45)]
BG_IMGS = [Image.fromarray(np.clip(BG + gr, 0, 255).astype(np.uint8)).convert("RGBA") for gr in GRAIN]


def background(t, tint=None):
    im = BG_IMGS[int(t * 12) % 4].copy()
    if tint:
        ov = Image.new("RGBA", (W, H), tint)
        im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im, "RGBA")
    for x, y, s, sp, ph in DUST:
        px, py = (x + t * sp * 0.6) % W, (y - t * sp) % H
        a = 0.25 + 0.2 * math.sin(t * 0.8 + ph)
        d.ellipse((px - s, py - s, px + s, py + s), fill=rgba(GOLD, a))
    return im


# ---------- drawing helpers ----------
def text(d, xy, s, f, col, a=1.0, anchor="mm", rise=0.0):
    if a <= 0:
        return
    x, y = xy
    d.text((x, y + rise * (1 - a) * 40), s, font=f, fill=rgba(col, a), anchor=anchor)


def fade_text(d, lt, t0, xy, s, f, col=WHITE, anchor="mm", d0=0.5):
    text(d, xy, s, f, col, app(lt, t0, d0), anchor, rise=1)


def pill(d, cx, cy, s, f, fg, bg, a=1.0, pad=(36, 16)):
    if a <= 0:
        return
    w = d.textlength(s, font=f)
    h = f.size
    d.rounded_rectangle((cx - w / 2 - pad[0], cy - h / 2 - pad[1], cx + w / 2 + pad[0], cy + h / 2 + pad[1] + 6),
                        radius=(h + 2 * pad[1]) // 2, fill=rgba(bg, a))
    d.text((cx, cy + 3), s, font=f, fill=rgba(fg, a), anchor="mm")


def card(d, box, a=1.0, border=GOLD, fill=(18, 34, 64)):
    if a <= 0:
        return
    d.rounded_rectangle(box, radius=22, fill=rgba(fill, 0.92 * a), outline=rgba(border, a), width=3)


def stamp(layer, lt, t0, s, col=RED, size=150, angle=-12, center=(CX, CY)):
    a = app(lt, t0, 0.25)
    if a <= 0:
        return
    sc = lerp(2.2, 1.0, a)
    f = font(F_BLK, int(size * sc))
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    w = td.textlength(s, font=f)
    hh = f.size
    td.rounded_rectangle((CX - w / 2 - 40, CY - hh / 2 - 20, CX + w / 2 + 40, CY + hh / 2 + 30), radius=18,
                         outline=rgba(col, a), width=int(12 * sc))
    td.text((CX, CY + 6), s, font=f, fill=rgba(col, a), anchor="mm")
    tmp = tmp.rotate(angle, center=(CX, CY), resample=Image.BICUBIC)
    if center != (CX, CY):
        tmp = tmp.transform((W, H), Image.AFFINE, (1, 0, CX - center[0], 0, 1, CY - center[1]))
    layer.alpha_composite(tmp)


def counter(lt, t0, t1, v0, v1):
    return v0 + (v1 - v0) * ease((lt - t0) / max(0.01, t1 - t0))


def line_chart(d, box, pts, prog, col, a=1.0, width=8, dashed=False):
    """pts: list of (x0..1, y0..1) in box space (y 0 = bottom). prog 0..1 draws along the polyline."""
    if a <= 0 or prog <= 0:
        return None
    x0, y0, x1, y1 = box
    P = [(x0 + px * (x1 - x0), y1 - py * (y1 - y0)) for px, py in pts]
    seg = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]
    total, goal = sum(seg), sum(seg) * clamp(prog)
    out, acc = [P[0]], 0
    for i, L in enumerate(seg):
        if acc + L >= goal:
            k = (goal - acc) / L if L else 0
            out.append((lerp(P[i][0], P[i + 1][0], k), lerp(P[i][1], P[i + 1][1], k)))
            break
        out.append(P[i + 1]); acc += L
    if dashed:
        for i in range(len(out) - 1):
            n = max(1, int(math.dist(out[i], out[i + 1]) / 26))
            for j in range(0, n, 2):
                pa = (lerp(out[i][0], out[i + 1][0], j / n), lerp(out[i][1], out[i + 1][1], j / n))
                pb = (lerp(out[i][0], out[i + 1][0], (j + 1) / n), lerp(out[i][1], out[i + 1][1], (j + 1) / n))
                d.line([pa, pb], fill=rgba(col, a), width=width)
    else:
        d.line(out, fill=rgba(col, a), width=width, joint="curve")
    ex, ey = out[-1]
    d.ellipse((ex - 12, ey - 12, ex + 12, ey + 12), fill=rgba(col, a))
    return out[-1]


def axes(d, box, a=1.0):
    x0, y0, x1, y1 = box
    d.line([(x0, y1), (x1, y1)], fill=rgba(GREY, 0.5 * a), width=3)
    for k in range(1, 4):
        yy_ = y1 - (y1 - y0) * k / 4
        d.line([(x0, yy_), (x1, yy_)], fill=rgba(GREY, 0.12 * a), width=2)


def bottle(d, x, y, s=1.0, a=1.0, col=(150, 60, 50)):
    w, h = 44 * s, 150 * s
    d.rounded_rectangle((x - w / 2, y - h * 0.45, x + w / 2, y + h / 2), radius=int(16 * s), fill=rgba(col, a))
    d.polygon([(x - w / 2, y - h * 0.45), (x - w * 0.18, y - h * 0.75), (x + w * 0.18, y - h * 0.75), (x + w / 2, y - h * 0.45)],
              fill=rgba(col, a))
    d.rectangle((x - w * 0.18, y - h * 0.82, x + w * 0.18, y - h * 0.72), fill=rgba(GREY, a))
    d.rectangle((x - w / 2, y - h * 0.05, x + w / 2, y + h * 0.12), fill=rgba(WHITE, 0.85 * a))


def pin(d, x, y, col=RED, a=1.0, s=1.0):
    d.ellipse((x - 26 * s, y - 80 * s, x + 26 * s, y - 28 * s), fill=rgba(col, a))
    d.polygon([(x - 22 * s, y - 46 * s), (x + 22 * s, y - 46 * s), (x, y)], fill=rgba(col, a))
    d.ellipse((x - 10 * s, y - 64 * s, x + 10 * s, y - 44 * s), fill=rgba(WHITE, a))


def map_grid(d, a=1.0):
    for gx in range(160, W - 120, 80):
        d.line([(gx, 200), (gx, 900)], fill=rgba(GREY, 0.08 * a), width=1)
    for gy in range(200, 920, 80):
        d.line([(160, gy), (W - 160, gy)], fill=rgba(GREY, 0.08 * a), width=1)


def bank(d, x, y, a=1.0, s=1.0):
    col = rgba(GREY, a)
    d.polygon([(x - 150 * s, y - 120 * s), (x, y - 200 * s), (x + 150 * s, y - 120 * s)], fill=col)
    for k in range(5):
        px = x - 120 * s + k * 60 * s
        d.rectangle((px - 12 * s, y - 110 * s, px + 12 * s, y + 40 * s), fill=col)
    d.rectangle((x - 165 * s, y + 40 * s, x + 165 * s, y + 62 * s), fill=col)


def bell(d, x, y, ang, a=1.0, s=1.0):
    tmp = Image.new("RGBA", (int(300 * s), int(300 * s)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    c = 150 * s
    td.pieslice((c - 80 * s, c - 100 * s, c + 80 * s, c + 60 * s), 180, 360, fill=rgba(GOLD, a))
    td.polygon([(c - 80 * s, c - 20 * s), (c + 80 * s, c - 20 * s), (c + 100 * s, c + 60 * s), (c - 100 * s, c + 60 * s)], fill=rgba(GOLD, a))
    td.ellipse((c - 22 * s, c + 55 * s, c + 22 * s, c + 95 * s), fill=rgba(GOLD, a))
    return tmp.rotate(ang, center=(c, c - 100 * s), resample=Image.BICUBIC), (int(x - c), int(y - c))


def book(d, x, y, open_k, a=1.0):
    w, h = 230, 300
    ang = open_k * 0.9
    d.rectangle((x, y - h / 2, x + w, y + h / 2), fill=rgba((40, 70, 140), a), outline=rgba(GOLD, a), width=4)
    lw = w * math.cos(ang * math.pi / 2)
    d.polygon([(x, y - h / 2), (x - lw, y - h / 2 + 18 * open_k), (x - lw, y + h / 2 - 18 * open_k), (x, y + h / 2)],
              fill=rgba((40, 70, 140) if open_k < 0.5 else (235, 228, 210), a), outline=rgba(GOLD, a))
    if open_k > 0.5:
        for k in range(7):
            yy_ = y - h / 2 + 50 + k * 30
            d.line([(x - lw + 25, yy_), (x - 25, yy_)], fill=rgba(GREY, a * 0.8), width=4)


def pinball(d, x, y, a=1.0, s=1.0):
    d.polygon([(x - 70 * s, y - 120 * s), (x + 70 * s, y - 120 * s), (x + 90 * s, y + 60 * s), (x - 90 * s, y + 60 * s)],
              fill=rgba((120, 40, 140), a), outline=rgba(GOLD, a), width=3)
    d.rectangle((x - 80 * s, y - 190 * s, x + 80 * s, y - 120 * s), fill=rgba((40, 40, 70), a), outline=rgba(GOLD, a), width=3)
    for k, (ox, oy) in enumerate([(-30, -70), (30, -60), (0, -20)]):
        d.ellipse((x + (ox - 16) * s, y + (oy - 16) * s, x + (ox + 16) * s, y + (oy + 16) * s), fill=rgba(GOLD, a))
    d.rectangle((x - 80 * s, y + 60 * s, x - 66 * s, y + 140 * s), fill=rgba(GREY, a))
    d.rectangle((x + 66 * s, y + 60 * s, x + 80 * s, y + 140 * s), fill=rgba(GREY, a))


def thumbs(d, x, y, a=1.0, s=1.0):
    d.rounded_rectangle((x - 70 * s, y - 20 * s, x + 50 * s, y + 110 * s), radius=int(24 * s), fill=rgba(WHITE, a))
    d.rounded_rectangle((x - 30 * s, y - 110 * s, x + 10 * s, y), radius=int(18 * s), fill=rgba(WHITE, a))
    d.rectangle((x - 120 * s, y - 10 * s, x - 82 * s, y + 110 * s), fill=rgba(WHITE, a))


# ---------- scenes: (start, end, fn(layer, d, lt, dur, t)) — times are seconds of voiceover ----------
SCENES = []


def scene(t0, t1, tint=None):
    def deco(fn):
        SCENES.append((t0, t1, fn, tint))
        return fn
    return deco


@scene(0.0, 3.0)
def s_hook(L, d, lt, dur, t):
    a = app(lt, 0.0, 0.6)
    text(d, (CX, CY - 60), "11", font(F_BLK, int(lerp(380, 300, a))), GOLD, a)
    fade_text(d, lt, 0.5, (CX, CY + 150), "YEARS OLD", font(F_BLD, 64))
    fade_text(d, lt, 1.4, (CX, CY + 250), "All his savings. His first share.", font(F_SB, 44), GREY)


CH = (300, 280, 1620, 820)
PTS = [(0.0, 0.17), (0.28, 0.04), (0.5, 0.185), (1.0, 0.95)]  # $38, $27, $40, ~$200 on a 0-210 scale


@scene(3.0, 15.5)
def s_first_chart(L, d, lt, dur, t):
    a = app(lt, 0, 0.5)
    axes(d, CH, a)
    fade_text(d, lt, 0.0, (CH[0], 210), "HIS FIRST STOCK · 1942", font(F_BLD, 40), GOLD, anchor="lm")
    # buy -> panic -> sell
    if t < 11.6:
        p = (counter(t, 3.5, 7.0, 0, 1) * 0.5 + counter(t, 7.0, 10.0, 0, 1) * 0.5)
        line_chart(d, CH, PTS[:3], p, RED if t < 8.6 else GREEN, a)
    else:
        line_chart(d, CH, PTS[:3], 1, GREEN, a)
        line_chart(d, CH, PTS[2:], counter(t, 11.8, 14.0, 0, 1), GOLD, a, dashed=True)
    lab = font(F_BLD, 42)
    text(d, (CH[0] + 10, CH[3] - 0.17 * 540 - 50), "BUY $38", lab, WHITE, app(t, 3.6), "lm")
    text(d, (CH[0] + 0.28 * 1320, CH[3] + 50), "$27  PANIC", lab, RED, app(t, 6.6), "mm")
    if t >= 9.6:
        text(d, (CH[0] + 0.5 * 1320 - 30, CH[3] - 0.185 * 540 - 50), "SOLD $40", lab, GREEN, app(t, 9.6), "rm")
    if t >= 13.4:
        text(d, (CH[2] - 20, CH[1] - 10), "~$200", font(F_BLK, 76), GOLD, app(t, 13.4), "rm")
        text(d, (CX + 430, CY + 170), "5×", font(F_BLK, 200), GOLD, app(t, 13.0, 0.4) * 0.9)


@scene(15.5, 22.5)
def s_lesson_intro(L, d, lt, dur, t):
    fade_text(d, lt, 0.2, (CX, CY - 70), "That day, he learned one lesson…", font(F_SER, 76))
    fade_text(d, lt, 3.5, (CX, CY + 60), "…that made him the world's most famous investor.", font(F_SER, 60), GOLD)


@scene(22.5, 26.6)
def s_title_bg(L, d, lt, dur, t):
    pass  # the builder burns the series title card here (title_at = 22.6)


@scene(26.6, 35.0)
def s_three_parts(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 230), "THE WARREN BUFFETT STORY · IN 3 PARTS", font(F_BLD, 46), GOLD)
    items = [("PART 1", "The Beginning", "Birth → First struggle"), ("PART 2", "The Struggle", "Struggle → Breakthrough"),
             ("PART 3", "Oracle of Omaha", "The legend")]
    for k, (p, ttl, sub) in enumerate(items):
        a = app(lt, 0.6 + k * 0.6)
        x = CX + (k - 1) * 520
        hl = k == 0
        card(d, (x - 230, 360 - (1 - a) * 40, x + 230, 760 - (1 - a) * 40), a, border=GOLD if hl else GREY,
             fill=(30, 52, 92) if hl else (18, 34, 64))
        text(d, (x, 450), p, font(F_BLK, 54), GOLD if hl else GREY, a)
        text(d, (x, 560), ttl, font(F_SER, 50), WHITE, a)
        text(d, (x, 650), sub, font(F_SB, 32), GREY, a)
    if lt > 3:
        pill(d, CX - 520, 820, "YOU ARE HERE", font(F_BLD, 30), NAVY, GOLD, app(lt, 3))


@scene(35.0, 43.8)
def s_cta_sub(L, d, lt, dur, t):
    fade_text(d, lt, 0.1, (CX, 330), "Enjoy stories of how great investors were made?", font(F_SER, 58))
    s = 1 + 0.05 * math.sin(lt * 6) if lt > 1.5 else 1
    pill(d, CX - 120, 560, "SUBSCRIBE", font(F_BLK, int(70 * s)), WHITE, (200, 30, 30), app(lt, 0.8))
    if lt > 1.2:
        b, pos = bell(d, CX + 260, 560, 18 * math.sin(lt * 14) * (1 if lt > 4.3 else 0.2), app(lt, 1.2))
        L.alpha_composite(b, pos)
    fade_text(d, lt, 4.4, (CX, 760), "…and tap the bell so you don't miss Part 2", font(F_SB, 44), GREY)


@scene(43.8, 52.0)
def s_birth(L, d, lt, dur, t):
    s = "30 AUGUST 1930"
    n = int(clamp(lt / 1.6) * len(s))
    text(d, (CX, 300), s[:n], font(F_SER, 110), GOLD, 1)
    a = app(lt, 2.2)
    map_grid(d, a)
    if lt > 2.4:
        drop = ease((lt - 2.4) / 0.6)
        pin(d, CX, 640 - (1 - drop) * 200, RED, drop, 1.3)
        text(d, (CX, 700), "OMAHA, NEBRASKA · USA", font(F_BLD, 48), WHITE, drop)
    fade_text(d, lt, 4.2, (CX, 820), "Warren Edward Buffett is born", font(F_SER, 60))


DOW = [(0.0, 0.92), (0.06, 0.62), (0.15, 0.72), (0.3, 0.55), (0.45, 0.42), (0.6, 0.30), (0.75, 0.18), (0.9, 0.10), (1.0, 0.10)]


@scene(52.0, 61.0, tint=(60, 10, 10, 40))
def s_crash(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 200), "ONE YEAR EARLIER · OCTOBER 1929", font(F_BLD, 46), RED)
    box = (360, 300, 1560, 800)
    axes(d, box, app(lt, 0.3))
    line_chart(d, box, DOW, counter(lt, 0.8, 5.5, 0, 1), RED, app(lt, 0.3))
    text(d, (box[0], box[1] - 10), "Dow Jones: 381", font(F_BLD, 38), WHITE, app(lt, 0.8), "lm")
    if lt > 5:
        text(d, (box[2], box[3] - 90), "41  (1932)", font(F_BLD, 38), WHITE, app(lt, 5), "rm")
        text(d, (CX + 200, 470), "−89%", font(F_BLK, 190), RED, app(lt, 5.3, 0.3))
    fade_text(d, lt, 6.5, (CX, 920), "THE GREAT DEPRESSION", font(F_SER, 72), WHITE)


@scene(61.0, 68.9, tint=(40, 10, 10, 30))
def s_banks(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 210), "Jobs lost. Banks shut.", font(F_SER, 70))
    v = int(counter(lt, 0.5, 2.8, 0, 9000))
    text(d, (CX - 380, 520), f"{v:,}+", font(F_BLK, 150), RED, app(lt, 0.5))
    text(d, (CX - 380, 640), "US banks failed, 1930–33", font(F_SB, 40), GREY, app(lt, 0.8))
    bank(d, CX + 420, 560, app(lt, 2.6), 1.2)
    if lt > 3.1:
        stamp(L, lt, 3.1, "CLOSED", RED, 90, -10, (CX + 420, 520))
    fade_text(d, lt, 4.3, (CX, 900), "…including the bank where his father, Howard Buffett, worked", font(F_SB, 44))


@scene(68.9, 81.4)
def s_howard(L, d, lt, dur, t):
    if lt < 2.1:
        fade_text(d, lt, 0, (CX, CY - 40), "Money was tight at home.", font(F_SER, 76))
        return
    fade_text(d, lt, 2.1, (CX, 230), "But Howard didn't give up.", font(F_SER, 70))
    a = app(lt, 3.8)
    card(d, (CX - 520, 330, CX + 520, 560), a)
    text(d, (CX, 400), "1931", font(F_BLK, 60), GOLD, a)
    text(d, (CX, 490), "Started his own stock-brokerage firm", font(F_SB, 46), WHITE, a)
    for k, wd in enumerate(["MONEY", "HARD WORK", "RISK"]):
        x = CX + (k - 1) * 480
        pill(d, x, 690, wd, font(F_BLK, 52), NAVY, GOLD, app(lt, 6.9 + k * 0.5))
    fade_text(d, lt, 9.8, (CX, 860), "Little Warren saw all three up close.", font(F_SB, 46), GREY)


@scene(81.4, 85.6)
def s_numbers(L, d, lt, dur, t):
    d.line([(CX, 220), (CX, 860)], fill=rgba(GREY, 0.4 * app(lt, 0)), width=3)
    fade_text(d, lt, 0.1, (CX - 480, 260), "Other kids played with toys", font(F_SB, 46), GREY)
    for k in range(4):
        a = app(lt, 0.4 + k * 0.15)
        x, y = CX - 600 + (k % 2) * 240, 470 + (k // 2) * 220
        d.rounded_rectangle((x - 70, y - 50, x + 70, y + 50), radius=16, fill=rgba((90, 110, 140), a))
        d.ellipse((x - 60, y + 30, x - 20, y + 70), fill=rgba(GREY, a)); d.ellipse((x + 20, y + 30, x + 60, y + 70), fill=rgba(GREY, a))
    fade_text(d, lt, 2.1, (CX + 480, 260), "Warren played with numbers", font(F_SB, 46), GOLD)
    random.seed(int(t * 8))
    for k in range(22):
        a = app(lt, 2.2 + k * 0.03) * 0.9
        text(d, (CX + 160 + (k * 137) % 640, 360 + (k * 97) % 460), str(random.choice([5, 25, 30, 38, 40, 1930, 100, 12])),
             font(F_BLD, 40 + (k % 3) * 14), GOLD if k % 3 == 0 else WHITE, a)


@scene(85.6, 112.4)
def s_coke(L, d, lt, dur, t):
    pill(d, 230, 140, "AGE 6", font(F_BLK, 46), NAVY, GOLD, app(lt, 0))
    if t < 104.8:
        fade_text(d, lt, 0.4, (CX, 200), "From his grandfather's grocery store…", font(F_SER, 56))
        for k in range(6):
            x = CX - 375 + k * 150
            bottle(d, x, 450, 1.2, app(lt, 2.6 + k * 0.12))
            if t > 93.6 + k * 0.3:
                pill(d, x, 600, "5¢", font(F_BLK, 40), NAVY, GREEN, app(t, 93.6 + k * 0.3), (18, 8))
        if t < 93.6:
            fade_text(d, lt, 3.2, (CX, 700), "bought a 6-pack of Coca-Cola for 25¢", font(F_BLD, 50), GOLD)
        else:
            fade_text(d, lt, 8.2, (CX, 700), "…and sold each bottle for 5¢", font(F_BLD, 50), GREEN)
        if t > 96.1:
            a = app(t, 96.1)
            card(d, (CX - 520, 770, CX + 520, 960), a)
            text(d, (CX, 820), "6 × 5¢ = 30¢    −    25¢ cost", font(F_BLD, 48), WHITE, a)
            text(d, (CX, 905), "= 5¢ PROFIT  (20% return)", font(F_BLK, 54), GREEN, app(t, 97.4))
    else:
        if t < 108.9:
            fade_text(d, lt, 19.3, (CX, 240), "5 cents? The amount didn't matter. The idea did.", font(F_SER, 58))
            steps = ["BUY CHEAP", "SELL AT VALUE", "KEEP ADDING PROFITS"]
            for k, s in enumerate(steps):
                x = CX + (k - 1) * 560
                a = app(t, 105.4 + k * 0.9)
                card(d, (x - 250, 430, x + 250, 640), a)
                text(d, (x, 535), s, font(F_BLK, 44), GOLD, a)
                if k < 2:
                    text(d, (x + 280, 535), "→", font(F_BLK, 60), WHITE, a)
        else:
            box = (380, 260, 1540, 820)
            axes(d, box, app(t, 108.9))
            pts = [(k / 40, (math.exp(k / 40 * 4.2) - 1) / (math.exp(4.2) - 1)) for k in range(41)]
            line_chart(d, box, pts, counter(t, 109.0, 111.6, 0, 1), GOLD, app(t, 108.9))
            text(d, (box[2], box[1] - 20), "BILLIONS", font(F_BLK, 72), GOLD, app(t, 111.0), "rm")
            text(d, (box[0], box[1] - 20), "The same thinking, compounded", font(F_SB, 40), WHITE, app(t, 109.0), "lm")


CH2 = (300, 330, 1620, 820)
PTS2 = [(0.0, 0.17), (0.3, 0.04), (0.55, 0.185), (1.0, 0.95)]


@scene(112.4, 133.1)
def s_first_stock(L, d, lt, dur, t):
    pill(d, 290, 140, "AGE 11 · 1942", font(F_BLK, 44), NAVY, GOLD, app(lt, 0))
    if t < 119.5:
        a = app(t, 113.6)
        card(d, (CX - 560, 330, CX + 560, 720), a)
        text(d, (CX, 410), "3 SHARES", font(F_BLK, 90), GOLD, a)
        text(d, (CX, 520), "Cities Service Preferred", font(F_SER, 60), WHITE, a)
        text(d, (CX, 610), "$38 per share", font(F_BLD, 52), WHITE, app(t, 115.2))
        fade_text(d, t, 116.6, (CX, 820), "(bought together with his elder sister, Doris)", font(F_SB, 40), GREY)
        return
    axes(d, CH2, app(t, 119.5))
    if t < 126.5:
        line_chart(d, CH2, PTS2[:2], counter(t, 119.7, 121.8, 0, 1), RED, app(t, 119.5))
        text(d, (CH2[0] + 0.3 * 1320, CH2[3] + 50), "$27   (−29%)", font(F_BLD, 46), RED, app(t, 121.6))
        fade_text(d, t, 123.0, (CX, 230), "Doris reminded him of the loss every day.", font(F_SER, 54))
    else:
        line_chart(d, CH2, PTS2[:3], 1, GREEN)
        text(d, (CH2[0] + 0.55 * 1320 - 30, CH2[3] - 0.185 * 490 - 50), "SOLD $40  (+$5)", font(F_BLD, 46), GREEN, app(t, 126.5), "rm")
        if t > 129.5:
            line_chart(d, CH2, PTS2[2:], counter(t, 129.6, 131.6, 0, 1), GOLD, 1, dashed=True)
            text(d, (CH2[2], CH2[1] - 20), "~$200 a few years later", font(F_BLK, 58), GOLD, app(t, 131.0), "rm")
            fade_text(d, t, 131.6, (CX, 230), "Profit missed: about $480", font(F_SER, 56), RED)
    text(d, (CH2[0] + 10, CH2[3] - 0.17 * 490 - 50), "BUY $38", font(F_BLD, 42), WHITE, 1, "lm")


@scene(133.1, 144.3)
def s_two_lessons(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 210), "TWO LESSONS HE KEPT FOR LIFE", font(F_BLD, 52), GOLD)
    for k, (n, s, t0) in enumerate([("1", "Don't anchor to the price you paid.", 137.0), ("2", "Don't rush.", 140.0)]):
        a = app(t, t0)
        y = 400 + k * 200
        card(d, (CX - 700, y - 75, CX + 700, y + 75), a)
        text(d, (CX - 620, y), n, font(F_BLK, 80), GOLD, a)
        text(d, (CX - 540, y), s, font(F_SER, 58), WHITE, a, "lm")
    fade_text(d, t, 142.0, (CX, 860), "Patience is what makes the real money.", font(F_SER, 66), GOLD)


@scene(144.3, 152.7)
def s_cta_like(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 260), "Found this lesson useful?", font(F_SER, 66))
    bob = math.sin(lt * 5) * 10 if lt > 1 else 0
    thumbs(d, CX - 260, 520 + bob, app(lt, 0.6), 1.2)
    pill(d, CX + 160, 540, "LIKE", font(F_BLK, 80), WHITE, (30, 110, 220), app(lt, 0.9))
    fade_text(d, lt, 4.2, (CX, 790), "Share it with the friend who panics when the market falls", font(F_SB, 46), GREY)


@scene(152.7, 166.3)
def s_washington(L, d, lt, dur, t):
    if t < 161.5:
        pill(d, 200, 140, "1942", font(F_BLK, 46), NAVY, GOLD, app(lt, 0))
        fade_text(d, lt, 0.3, (CX, 220), "Howard Buffett is elected to the US Congress", font(F_SER, 58))
        map_grid(d, app(lt, 0.8))
        ox, oy, wx, wy = 520, 640, 1420, 560
        pin(d, ox, oy, GOLD, app(lt, 1.0), 1.1)
        text(d, (ox, oy + 50), "OMAHA", font(F_BLD, 40), WHITE, app(lt, 1.0))
        k = counter(t, 157.2, 159.4, 0, 1)
        if k > 0:
            pts = [(lerp(ox, wx, i / 30), lerp(oy, wy, i / 30) - math.sin(math.pi * i / 30) * 160) for i in range(int(30 * k) + 1)]
            if len(pts) > 1:
                d.line(pts, fill=rgba(GOLD, 0.9), width=6)
        pin(d, wx, wy, RED, app(t, 159.2), 1.1)
        text(d, (wx, wy + 50), "WASHINGTON, D.C.", font(F_BLD, 40), WHITE, app(t, 159.2))
        fade_text(d, t, 157.3, (CX, 900), "The whole family moves to Washington, D.C.", font(F_SB, 46), GREY)
    else:
        fade_text(d, t, 161.5, (CX, 330), "Warren hated it.", font(F_SER, 90))
        a = app(t, 163.5)
        text(d, (CX - 200, 620), "GRADES", font(F_BLK, 90), WHITE, a)
        dy = ease((t - 163.6) / 1.2) * 60
        d.polygon([(CX + 140, 560 + dy), (CX + 260, 560 + dy), (CX + 200, 680 + dy)], fill=rgba(RED, a))
        fade_text(d, t, 164.4, (CX, 820), "His heart wasn't in school.", font(F_SB, 46), GREY)


@scene(166.3, 180.7)
def s_papers(L, d, lt, dur, t):
    if t < 173.4:
        fade_text(d, lt, 0, (CX, 230), "He turned his unhappiness into work.", font(F_SER, 62))
        fade_text(d, t, 168.9, (CX, 380), "Delivering newspapers before dawn", font(F_BLD, 50), GOLD)
        v = int(counter(t, 171.6, 173.2, 0, 500))
        text(d, (CX, 600), f"~{v}", font(F_BLK, 200), WHITE, app(t, 171.6))
        text(d, (CX, 760), "papers every morning", font(F_SB, 46), GREY, app(t, 171.8))
    else:
        pill(d, 220, 140, "AGE 13", font(F_BLK, 46), NAVY, GOLD, app(t, 173.4))
        fade_text(d, t, 173.5, (CX, 230), "Filed his first income-tax return", font(F_SER, 62))
        a = app(t, 174.2)
        d.rounded_rectangle((CX - 420, 320, CX + 420, 900), radius=10, fill=rgba((236, 230, 214), a))
        text(d, (CX, 380), "INCOME TAX RETURN", font(F_BLK, 44), NAVY, a)
        for k in range(5):
            d.line([(CX - 360, 470 + k * 60), (CX + 360, 470 + k * 60)], fill=rgba((150, 150, 150), a), width=3)
        if t > 177.6:
            a2 = app(t, 177.6)
            d.rectangle((CX - 380, 760, CX + 380, 850), fill=rgba((255, 236, 150), a2))
            text(d, (CX - 360, 805), "Bicycle — business expense", font(F_BLD, 40), NAVY, a2, "lm")
            text(d, (CX + 360, 805), "$35", font(F_BLK, 44), NAVY, a2, "rm")


@scene(180.7, 198.2)
def s_pinball(L, d, lt, dur, t):
    pill(d, 290, 140, "HIGH SCHOOL", font(F_BLK, 44), NAVY, GOLD, app(lt, 0))
    if t < 191.8:
        pinball(d, CX - 350, 580, app(t, 181.0), 1.4)
        fade_text(d, t, 181.4, (CX + 300, 430), "A used pinball machine", font(F_SER, 58), WHITE)
        text(d, (CX + 300, 560), "$25", font(F_BLK, 150), GOLD, app(t, 182.2))
        fade_text(d, t, 184.0, (CX + 300, 680), "bought with a school friend", font(F_SB, 42), GREY)
        fade_text(d, t, 188.3, (CX, 920), "Placed in a barber shop: customers played while they waited", font(F_SB, 44), WHITE)
    else:
        n = 1 if t < 192.6 else (3 if t < 193.6 else 7)
        for k in range(n):
            x = CX + (k - (n - 1) / 2) * 220
            pinball(d, x, 560, app(t, 191.8 + k * 0.08), 0.9 if n > 3 else 1.1)
        text(d, (CX, 230), f"1  →  3  →  more machines", font(F_BLD, 52), WHITE, app(t, 191.9))
        if t > 194.8:
            a = app(t, 194.8)
            card(d, (CX - 500, 780, CX + 500, 960), a)
            text(d, (CX, 870), "Business sold for $1,200", font(F_BLK, 62), GREEN, a)


@scene(198.2, 214.0, tint=(30, 25, 0, 20))
def s_farm(L, d, lt, dur, t):
    fade_text(d, lt, 0.2, (CX, 220), "With that money, he bought land", font(F_SER, 62))
    a = app(lt, 1.6)
    for r_ in range(6):
        for c in range(10):
            x, y = CX - 500 + c * 100, 360 + r_ * 70
            k = clamp((lt - 1.6 - (r_ + c) * 0.04) / 0.5)
            d.rectangle((x, y, x + 92, y + 62), fill=rgba((70 + (r_ + c) % 2 * 25, 110 + (r_ + c) % 2 * 20, 50), k * 0.9))
    text(d, (CX, 860), "40-ACRE FARM · NEBRASKA", font(F_BLK, 66), GOLD, app(lt, 3.0))
    fade_text(d, lt, 8.0, (CX, 960), "Rented to a tenant farmer: income while he studied", font(F_SB, 42), GREY)


@scene(214.0, 218.7)
def s_college(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 250), "On his father's advice, he went to college", font(F_SER, 58))
    steps = ["Wharton", "University of Nebraska", "Graduated at 19"]
    d.line([(CX - 560, 560), (CX + 560, 560)], fill=rgba(GREY, 0.5 * app(lt, 0.8)), width=4)
    for k, s in enumerate(steps):
        x = CX + (k - 1) * 560
        a = app(lt, 0.8 + k * 0.9)
        pill(d, x, 560, s, font(F_BLD, 44), NAVY if k == 2 else WHITE, GOLD if k == 2 else (40, 70, 120), a)
    fade_text(d, lt, 3.4, (CX, 720), "1950", font(F_BLK, 80), GOLD)


@scene(218.7, 234.4, tint=(10, 10, 20, 30))
def s_harvard(L, d, lt, dur, t):
    if t < 227.0:
        text(d, (CX, 220), "HARVARD BUSINESS SCHOOL · 1950", font(F_BLD, 52), WHITE, app(lt, 0))
        for k, s in enumerate(["Application", "Interview"]):
            a = app(lt, 0.8 + k * 1.2)
            pill(d, CX + (k - 0.5) * 520, 420, s, font(F_BLD, 46), WHITE, (40, 70, 120), a)
        if t > 224.2:
            stamp(L, t, 224.2, "REJECTED", RED, 170, -12, (CX, 640))
    else:
        fade_text(d, t, 227.0, (CX, 360), "A boy who had run businesses since childhood…", font(F_SER, 60))
        fade_text(d, t, 230.4, (CX, 500), "…turned down by the world's top business school.", font(F_SER, 60), RED)
        fade_text(d, t, 233.1, (CX, 700), "He could have given up.", font(F_SB, 50), GREY)


@scene(234.4, 247.5)
def s_turning(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 210), "Instead, it became the turning point of his life.", font(F_SER, 60), GOLD)
    if t > 238.9:
        book(d, CX - 300, 570, ease((t - 239.2) / 1.2), app(t, 238.9))
        fade_text(d, t, 239.4, (CX - 300, 800), "A book…", font(F_SER, 56))
    if t > 241.8:
        a = app(t, 241.8)
        d.ellipse((CX + 260, 400, CX + 400, 540), fill=rgba(GREY, a * 0.8))
        d.rounded_rectangle((CX + 200, 550, CX + 460, 760), radius=60, fill=rgba(GREY, a * 0.8))
        text(d, (CX + 330, 480), "?", font(F_BLK, 90), NAVY, a)
        fade_text(d, t, 242.0, (CX + 330, 800), "…and a mentor", font(F_SER, 56))
    if t > 245.3:
        pill(d, CX, 940, "THAT STORY IS IN PART 2", font(F_BLK, 46), NAVY, GOLD, app(t, 245.3))


@scene(247.5, 258.3)
def s_final_lesson(L, d, lt, dur, t):
    fade_text(d, lt, 0, (CX, 140), "TODAY'S LESSON", font(F_BLD, 44), GOLD)
    fade_text(d, lt, 0.3, (CX, 330), "Rejection is not the end.", font(F_SER, 96))
    fade_text(d, t, 250.3, (CX, 470), "Sometimes it's the start of the right path.", font(F_SER, 66), GOLD)
    if t > 253.4:
        a = app(t, 253.4)
        d.rounded_rectangle((CX - 520, 640, CX + 520, 860), radius=30, fill=rgba(WHITE, a))
        d.polygon([(CX - 380, 860), (CX - 300, 860), (CX - 400, 930)], fill=rgba(WHITE, a))
        text(d, (CX, 700), "Faced rejection? Comment:", font(F_SB, 40), (60, 60, 60), a)
        text(d, (CX, 785), "“Main rukunga nahi”", font(F_SER, 64), NAVY, app(t, 254.0))


@scene(258.3, 270.0)
def s_outro(L, d, lt, dur, t):
    for k, (s, c) in enumerate([("LIKE", (30, 110, 220)), ("SHARE", GREEN), ("SUBSCRIBE", (200, 30, 30))]):
        pill(d, CX + (k - 1) * 450, 330, s, font(F_BLK, 58), WHITE, c, app(lt, 0.2 + k * 0.5))
    fade_text(d, t, 262.8, (CX, 560), "PART 2", font(F_BLK, 120), GOLD)
    fade_text(d, t, 263.6, (CX, 690), "The real struggle of Warren Buffett begins", font(F_SER, 60))
    fade_text(d, t, 266.8, (CX, 860), "See you in the next part", font(F_SB, 46), GREY)


def frame(t):
    for t0, t1, fn, tint in SCENES:
        if t0 <= t < t1:
            im = background(t, tint)
            L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(L, "RGBA")
            fn(L, d, t - t0, t1 - t0, t)
            env = min(clamp((t - t0) / 0.35), clamp((t1 - t) / 0.35))
            if env < 1:
                L.putalpha(L.getchannel("A").point(lambda v: int(v * env)))
            im.alpha_composite(L)
            return im.convert("RGB")
    return background(t).convert("RGB")


if __name__ == "__main__":
    out = sys.argv[1]
    a, b = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, DUR)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out],
                         stdin=subprocess.PIPE)
    n0, n1 = int(a * FPS), int(b * FPS)
    for n in range(n0, n1):
        p.stdin.write(frame(n / FPS).tobytes())
        if n % 900 == 0:
            print(f"{n / FPS:.0f}s", flush=True)
    p.stdin.close(); p.wait()
