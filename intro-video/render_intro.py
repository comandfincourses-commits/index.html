"""COMandFIN 10-second channel intro — frame renderer + synthesized soundtrack.

Usage: python3 -I render_intro.py <images_dir> <out_dir>
Writes <out_dir>/frames/*.png and <out_dir>/audio.wav; ffmpeg muxes them afterwards.
"""
import math, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

IMG_DIR, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1920, 1080, 30, 10.0
N = int(FPS * DUR)

NAVY, GOLD, GREEN, WHITE = (11, 31, 58), (201, 154, 46), (15, 174, 131), (255, 255, 255)
FD = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(FD + f"Inter-{w}.otf", s)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, t1): return clamp((t - t0) / (t1 - t0))
def ease_out(p): return 1 - (1 - p) ** 3
def ease_in(p): return p ** 3
def ease_io(p): return 3 * p * p - 2 * p * p * p
def back_out(p, s=1.7):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2

# ---------- source photos (SSBF header bands cropped off 2.jpg and 3.jpg) ----------
def load(name, box=None):
    im = Image.open(os.path.join(IMG_DIR, name)).convert("RGB")
    return im.crop(box) if box else im

portrait = load("1.jpg", (0, 10, 1080, 1277))
group    = load("2.jpg", (0, 126, 728, 613))
lecture  = load("3.jpg", (6, 112, 736, 642))
airport  = load("4.jpg", (0, 0, 960, 1280))
speaking = load("5.jpg")

def cover(im, w, h, cx=0.5, cy=0.5):
    """Scale to cover w×h, cropping around focal point (cx, cy)."""
    s = max(w / im.width, h / im.height)
    r = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    x = int(clamp(cx * r.width - w / 2, 0, r.width - w))
    y = int(clamp(cy * r.height - h / 2, 0, r.height - h))
    return r.crop((x, y, x + w, y + h))

# Pre-scale with headroom for Ken Burns zoom
OVS = 1.18
def prep(im, cx, cy): return cover(im, int(W * OVS), int(H * OVS), cx, cy)
P_SPEAK   = prep(speaking, 0.48, 0.42)
P_LECTURE = prep(lecture, 0.70, 0.55)
P_GROUP   = prep(group, 0.50, 0.55)
P_AIRPORT = prep(airport, 0.33, 0.35)
P_PORT    = prep(portrait, 0.5, 0.33)

def kenburns(P, p, z0=1.0, z1=1.12, dx=0.0):
    z = z0 + (z1 - z0) * p
    w, h = W * OVS / z, H * OVS / z
    cx = P.width / 2 + dx * p * (P.width - w) / 2
    cy = P.height / 2
    w, h = min(w, P.width), min(h, P.height)
    cx = clamp(cx, w / 2, P.width - w / 2)
    box = (max(0, cx - w / 2), max(0, cy - h / 2), min(P.width, cx + w / 2), min(P.height, cy + h / 2))
    return P.resize((W, H), Image.BILINEAR, box=box)

def duotone(im, dark, light, amount):
    g = ImageOps.grayscale(im)
    tone = ImageOps.colorize(g, dark, light)
    return Image.blend(im, tone, amount)

def gradient_overlay(base, color, a0, a1, horizontal=True):
    ramp = np.linspace(a0, a1, W if horizontal else H)
    a = np.tile(ramp, (H, 1)) if horizontal else np.tile(ramp[:, None], (1, W))
    mask = Image.fromarray((a * 255).astype(np.uint8))
    return Image.composite(Image.new("RGB", (W, H), color), base, mask)

def whip(im, amount):
    """Cheap horizontal motion blur: squash then stretch."""
    if amount <= 0.01: return im
    f = max(2, int(1 + amount * 40))
    return im.resize((W // f, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)

# ---------- text helpers ----------
def text_w(txt, fnt, track=0):
    return sum(fnt.getlength(c) for c in txt) + track * (len(txt) - 1)

def draw_tracked(d, xy, txt, fnt, fill, track=0):
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=fnt, fill=fill)
        x += fnt.getlength(c) + track

def label_box(img, txt, fnt, cx, cy, p, bg=NAVY, fg=WHITE, track=6, pad=(34, 18), from_left=True):
    """Text box that wipes open horizontally (p 0→1)."""
    tw = text_w(txt, fnt, track)
    asc, desc = fnt.getmetrics()
    bw, bh = int(tw + pad[0] * 2), int(asc + desc * 0.3 + pad[1] * 2)
    layer = Image.new("RGBA", (bw, bh), bg + (255,))
    d = ImageDraw.Draw(layer)
    draw_tracked(d, (pad[0], pad[1] - asc * 0.06), txt, fnt, fg, track)
    d.rectangle((0, bh - 6, bw, bh), fill=GOLD + (255,))
    vis = int(bw * ease_out(p))
    if vis <= 0: return
    if from_left: layer = layer.crop((0, 0, vis, bh))
    else: layer = layer.crop((bw - vis, 0, bw, bh))
    x = int(cx - bw / 2) + (0 if from_left else bw - vis)
    img.paste(layer, (x, int(cy - bh / 2)), layer)

def big_text(img, txt, fnt, cx, cy, fill, alpha=1.0, track=8, shadow=True):
    tw = text_w(txt, fnt, track)
    asc, desc = fnt.getmetrics()
    layer = Image.new("RGBA", (int(tw) + 60, asc + desc + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        draw_tracked(ImageDraw.Draw(sh), (34, 34), txt, fnt, (0, 0, 0, 150), track)
        layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(layer)
    draw_tracked(d, (30, 30), txt, fnt, fill + (255,), track)
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    img.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)

def streaks(img, t, color, seed, n=7, alpha=200):
    rnd = np.random.RandomState(seed)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(n):
        y = rnd.randint(60, H - 60); L = rnd.randint(180, 520); sp = rnd.uniform(2500, 4200)
        th = rnd.choice([6, 10, 16]); off = rnd.uniform(0, W)
        x = (off + sp * t) % (W + L) - L
        d.rounded_rectangle((x, y, x + L, y + th), radius=th // 2, fill=color + (alpha,))
    img.paste(ov, (0, 0), ov)

# ---------- end-card background + feathered portrait ----------
def endcard_bg():
    top, bot = np.array([176, 199, 203]), np.array([150, 175, 177])
    g = np.linspace(0, 1, H)[:, None, None]
    arr = (top * (1 - g) + bot * g) * np.ones((1, W, 1))
    # soft vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.18 * (((xx - W * 0.4) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
    return Image.fromarray(np.clip(arr * v[..., None], 0, 255).astype(np.uint8))
BG_END = endcard_bg()

PH = 1080
PORT_END = portrait.resize((int(portrait.width * PH / portrait.height), PH), Image.LANCZOS)
pm = np.ones((PORT_END.height, PORT_END.width))
fx = 260
pm[:, :fx] *= np.linspace(0, 1, fx)[None, :] ** 1.5
pm[:, -60:] *= np.linspace(1, 0.6, 60)[None, :]
PORT_MASK = Image.fromarray((pm * 255).astype(np.uint8))

# ---------- scenes ----------
F_HUGE = font("Black", 168)
F_BIG = font("Black", 120)
F_LBL = font("ExtraBold", 64)
F_MID = font("ExtraBold", 44)
F_SM = font("SemiBold", 34)

def s_open(t):
    """0.0–1.0  white canvas, rising green/navy peak, FINANCE label slams in."""
    img = Image.new("RGB", (W, H), (248, 249, 251))
    d = ImageDraw.Draw(img)
    p = ease_out(prog(t, 0.0, 0.55))
    peak = H * 0.62 + (1 - p) * 600
    d.polygon([(W / 2 - 330, H + 10), (W / 2, peak), (W / 2 + 330, H + 10)], fill=NAVY)
    d.polygon([(W / 2 - 140, H + 10), (W / 2, peak + 120), (W / 2 + 40, H + 10)], fill=GREEN)
    streaks(img, t, GREEN, 3, n=5, alpha=int(255 * prog(t, 0.1, 0.4)))
    pl = prog(t, 0.25, 0.6)
    if pl > 0:
        s = back_out(pl)
        lbl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        label_box(lbl, "FINANCE", F_HUGE, W / 2, H * 0.40, 1.0, track=18, pad=(50, 16))
        bb = lbl.getbbox()
        if bb:
            c = lbl.crop(bb)
            c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.BICUBIC)
            img.paste(c, (int(W / 2 - c.width / 2), int(H * 0.40 - c.height / 2)), c)
    return img

def photo_scene(P, t, t0, t1, word, dark, light, tone_amt, dx, align="center", label=True):
    p = prog(t, t0, t1)
    img = kenburns(P, p, 1.0, 1.10, dx)
    img = duotone(img, dark, light, tone_amt)
    img = gradient_overlay(img, NAVY, 0.55, 0.0) if align == "left" else img
    streaks(img, t * 1.3, GOLD if align == "left" else GREEN, int(t0 * 10), n=5, alpha=170)
    pw = prog(t, t0 + 0.08, t0 + 0.42)
    if label:
        cx = W * 0.30 if align == "left" else W / 2
        label_box(img, word, F_LBL, cx, H * 0.72 if align != "left" else H / 2, pw, track=8)
    else:
        x_off = (1 - ease_out(pw)) * -300
        big_text(img, word, F_BIG, W / 2 + x_off, H / 2, WHITE, alpha=ease_out(pw), track=10)
    return img

def s_shatter(t, t0=3.8, t1=4.6):
    """Angular shards reveal the airport photo on a white canvas."""
    p = prog(t, t0, t1)
    base = Image.new("RGB", (W, H), (248, 249, 251))
    photo = kenburns(P_AIRPORT, p, 1.05, 1.15)
    photo = duotone(photo, NAVY, (230, 240, 245), 0.25)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    shards = [
        [(0.18, 0.0), (0.62, 0.0), (0.45, 0.55), (0.10, 0.42)],
        [(0.10, 0.42), (0.45, 0.55), (0.35, 1.0), (0.0, 1.0), (0.0, 0.6)],
        [(0.62, 0.0), (0.85, 0.0), (0.70, 0.62), (0.45, 0.55)],
        [(0.45, 0.55), (0.70, 0.62), (0.62, 1.0), (0.35, 1.0)],
        [(0.85, 0.0), (1.0, 0.0), (1.0, 0.7), (0.70, 0.62)],
        [(0.70, 0.62), (1.0, 0.7), (1.0, 1.0), (0.62, 1.0)],
    ]
    for i, sh in enumerate(shards):
        q = ease_out(prog(p, i * 0.07, 0.35 + i * 0.07))
        if q <= 0: continue
        cx = sum(x for x, _ in sh) / len(sh); cy = sum(y for _, y in sh) / len(sh)
        ang = (1 - q) * (0.6 if i % 2 else -0.6)
        sc = 0.3 + 0.7 * q
        pts = []
        for x, y in sh:
            vx, vy = (x - cx) * sc, (y - cy) * sc
            rx = vx * math.cos(ang) - vy * math.sin(ang); ry = vx * math.sin(ang) + vy * math.cos(ang)
            pts.append(((cx + rx) * W, (cy + ry) * H))
        d.polygon(pts, fill=255)
    img = Image.composite(photo, base, mask)
    dl = ImageDraw.Draw(img)
    for i, sh in enumerate(shards[:4]):
        q = prog(p, i * 0.07, 0.35 + i * 0.07)
        if 0 < q < 1:
            dl.line([(x * W, y * H) for x, y in sh] + [(sh[0][0] * W, sh[0][1] * H)], fill=WHITE, width=10)
    label_box(img, "MENTORSHIP", F_LBL, W * 0.72, H * 0.80, prog(t, t0 + 0.25, t0 + 0.6), from_left=False)
    return img


CERTS = [
    # (name, awarding body, structure, focus area)
    ("US CMA", "IMA, USA", "2 PARTS", ["Management Accounting,", "FP&A & Strategy"]),
    ("ACCA", "ACCA, UK", "13 EXAMS", ["Global Accounting,", "IFRS, Audit & Tax"]),
    ("CFA", "CFA Institute, USA", "3 LEVELS", ["Investment Analysis &", "Portfolio Management"]),
]
F_CERT = font("Black", 104)
F_BODY = font("SemiBold", 32)
F_FACT = font("ExtraBold", 40)

def cert_card(name, body, fact, focus, w=500, h=480):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w, h), radius=26, fill=(250, 251, 253, 255))
    d.rounded_rectangle((0, 0, w, 26), radius=13, fill=GOLD + (255,))
    d.rectangle((0, 13, w, 26), fill=GOLD + (255,))
    d.text((w / 2, 125), name, font=F_CERT, fill=NAVY, anchor="mm")
    d.text((w / 2, 205), body, font=F_BODY, fill=(90, 104, 125), anchor="mm")
    d.rectangle((w / 2 - 60, 245, w / 2 + 60, 250), fill=GOLD)
    d.rounded_rectangle((w / 2 - 120, 280, w / 2 + 120, 340), radius=30, fill=GREEN)
    d.text((w / 2, 311), fact, font=F_FACT, fill=WHITE, anchor="mm")
    for i, line in enumerate(focus):
        d.text((w / 2, 392 + i * 44), line, font=F_BODY, fill=NAVY, anchor="mm")
    return c
CARDS = [cert_card(*c) for c in CERTS]
BG_CERT = gradient_overlay(
    kenburns(P_LECTURE, 0.5, 1.05, 1.05).filter(ImageFilter.GaussianBlur(14)), NAVY, 0.88, 0.80)

def s_certs(t, t0=4.6, t1=6.6):
    """Global certification programmes: US CMA, ACCA, CFA."""
    img = BG_CERT.copy()
    streaks(img, t * 0.6, GOLD, 33, n=4, alpha=60)
    hp = ease_out(prog(t, t0 + 0.02, t0 + 0.35))
    if hp > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        f1, f2 = font("ExtraBold", 40), font("Medium", 34)
        h1, h2 = "PROFESSIONAL CERTIFICATION TRAINING", "Learn from a Chartered Accountant with 14+ years of experience"
        tw = text_w(h1, f1, 8)
        draw_tracked(dl, (W / 2 - tw / 2, 120 - (1 - hp) * 40), h1, f1, GOLD + (int(255 * hp),), 8)
        dl.text((W / 2, 205 - (1 - hp) * 40), h2, font=f2, fill=WHITE + (int(235 * hp),), anchor="mm")
        img.paste(lay, (0, 0), lay)
    cw, gap = CARDS[0].width, 70
    x0 = (W - (3 * cw + 2 * gap)) / 2
    for i, card in enumerate(CARDS):
        q = prog(t, t0 + 0.18 + i * 0.16, t0 + 0.68 + i * 0.16)
        if q <= 0: continue
        dy = (1 - back_out(q, 1.3)) * 420
        c = card.copy()
        c.putalpha(c.getchannel("A").point(lambda v: int(v * min(1, q * 2.5))))
        sh = Image.new("RGBA", (cw + 80, card.height + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((40, 52, cw + 40, card.height + 52), radius=26, fill=(0, 0, 0, int(120 * q)))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        x, y = int(x0 + i * (cw + gap)), int(320 + dy)
        img.paste(sh, (x - 40, y - 40), sh)
        img.paste(c, (x, y), c)
    fp = ease_out(prog(t, t0 + 1.0, t0 + 1.35))
    if fp > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.text((W / 2, 900 + (1 - fp) * 30), "Also: US CPA  •  FRM  •  DIP IFRS",
                font=font("SemiBold", 34), fill=WHITE + (int(220 * fp),), anchor="mm")
        img.paste(lay, (0, 0), lay)
    return img

CHIPS = ["US CMA", "ACCA", "CFA", "FRM", "US CPA"]
def s_end(t, t0=6.6):
    """Logo reveal end-card with portrait (holds to 10s)."""
    img = BG_END.copy()
    pp = ease_out(prog(t, t0, t0 + 0.7))
    px = int(W - PORT_END.width * 0.98 + (1 - pp) * 500)
    img.paste(PORT_END, (px, 0), PORT_MASK)
    cx = 600
    wp = ease_out(prog(t, t0 + 0.25, t0 + 0.85))
    if wp > 0:
        fW = font("Black", 124)
        parts = [("COM", NAVY), ("and", GOLD), ("FIN", NAVY)]
        tw = sum(fW.getlength(s_) for s_, _ in parts)
        layer = Image.new("RGBA", (int(tw) + 20, 160), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer); x = 0
        for s_, col in parts:
            dl.text((x, 0), s_, font=fW, fill=col + (255,)); x += fW.getlength(s_)
        layer = layer.crop((0, 0, max(1, int(layer.width * wp)), layer.height))
        img.paste(layer, (int(cx - tw / 2), 330), layer)
    d = ImageDraw.Draw(img)
    rp = ease_out(prog(t, t0 + 0.7, t0 + 1.2))
    if rp > 0:
        d.rectangle((cx - 330 * rp, 500, cx + 330 * rp, 506), fill=GOLD)
    tp = ease_out(prog(t, t0 + 0.9, t0 + 1.5))
    if tp > 0:
        tag = "FINANCIAL MODELLING  •  VALUATION  •  CORPORATE TRAINING"
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        fT = font("SemiBold", 28)
        tw = text_w(tag, fT, 3)
        draw_tracked(dl, (cx - tw / 2, 528 + (1 - tp) * 30), tag, fT, NAVY + (int(255 * tp),), 3)
        img.paste(lay, (0, 0), lay)
    # certification chips pop in one by one
    fC = font("ExtraBold", 28)
    widths = [fC.getlength(c) + 44 for c in CHIPS]
    total = sum(widths) + 16 * (len(CHIPS) - 1)
    x = cx - total / 2
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    for i, (c, w) in enumerate(zip(CHIPS, widths)):
        q = prog(t, t0 + 1.2 + i * 0.09, t0 + 1.5 + i * 0.09)
        if q > 0:
            s = back_out(q, 2.0)
            cy, hh, ww = 640, 26 * s, w / 2 * s
            dl.rounded_rectangle((x + w / 2 - ww, cy - hh, x + w / 2 + ww, cy + hh), radius=int(max(1, hh)),
                                 fill=(GREEN if i < 3 else NAVY) + (255,))
            if q > 0.5:
                dl.text((x + w / 2, cy), c, font=fC, fill=WHITE + (int(255 * min(1, (q - 0.5) * 2)),), anchor="mm")
        x += w + 16
    img.paste(lay, (0, 0), lay)
    wp2 = ease_out(prog(t, t0 + 1.7, t0 + 2.2))
    if wp2 > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        fU = font("Bold", 40)
        url = "www.COMandFIN.com"
        bw = fU.getlength(url) + 90
        y0 = 740 + (1 - wp2) * 30
        dl.rounded_rectangle((cx - bw / 2, y0, cx + bw / 2, y0 + 80), radius=40, fill=NAVY + (int(235 * wp2),))
        dl.text((cx, y0 + 40), url, font=fU, fill=WHITE + (int(255 * wp2),), anchor="mm")
        img.paste(lay, (0, 0), lay)
    return img

SCENES = [
    (0.0, 1.0, s_open),
    (1.0, 2.0, lambda t: photo_scene(P_SPEAK, t, 1.0, 2.0, "CORPORATE TRAINING", NAVY, (120, 230, 200), 0.45, 0.5)),
    (2.0, 3.0, lambda t: photo_scene(P_LECTURE, t, 2.0, 3.0, "FINANCIAL MODELLING", NAVY, (240, 220, 170), 0.35, -0.5, align="left")),
    (3.0, 3.8, lambda t: photo_scene(P_GROUP, t, 3.0, 3.8, "INDUSTRY-READY SKILLS", NAVY, (150, 235, 210), 0.5, 0.4, label=False)),
    (3.8, 4.6, s_shatter),
    (4.6, 6.6, s_certs),
    (6.6, 10.01, s_end),
]
CUTS = [s[0] for s in SCENES[1:]]

def frame(t):
    for t0, t1, fn in SCENES:
        if t0 <= t < t1:
            img = fn(t); break
    for c in CUTS:
        dt = t - c
        if -0.1 <= dt < 0.1:
            img = whip(img, 1 - abs(dt) / 0.1)
            if 0 <= dt < 0.067:
                img = Image.blend(img, Image.new("RGB", (W, H), WHITE), 0.55 * (1 - dt / 0.067))
    if t < 0.15: img = Image.blend(Image.new("RGB", (W, H), WHITE), img, t / 0.15)
    return img

# ---------- soundtrack: uplifting corporate pluck groove (synthesized; royalty-free) ----------
def soundtrack():
    sr = 48000; n = int(sr * DUR)
    out = np.zeros(n); rnd = np.random.RandomState(11)
    def add(sig, at, g=1.0):
        i = int(at * sr)
        if i >= n: return
        j = min(n, i + len(sig)); out[i:j] += g * sig[: j - i]
    def note(m): return 440.0 * 2 ** ((m - 69) / 12)
    def pluck(freq, dur=0.6, decay=0.994):
        """Karplus-Strong string, vectorised one period at a time."""
        N = max(2, int(sr / freq)); L = int(dur * sr)
        y = np.zeros(L + 2 * N + 2)
        y[:N + 1] = rnd.uniform(-1, 1, N + 1)
        s = N + 1
        while s < len(y):
            e = min(len(y), s + N)
            y[s:e] = decay * 0.5 * (y[s - N:e - N] + y[s - N - 1:e - N - 1])
            s = e
        y = y[:L] * np.minimum(1, np.linspace(1, 0, L) * 4)
        return y
    def kick():
        L = int(0.3 * sr); x = np.arange(L) / sr
        f = 48 + 120 * np.exp(-x * 35)
        return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 10)
    def clap():
        L = int(0.22 * sr); x = np.arange(L) / sr
        s = rnd.randn(L); s = s - np.convolve(s, np.ones(6) / 6, "same")
        env = sum(np.exp(-np.maximum(0, x - d) * 70) * (x >= d) for d in (0, 0.011, 0.022)) / 3
        return 0.6 * s * (env + 0.4 * np.exp(-x * 18))
    def shaker():
        L = int(0.05 * sr); x = np.arange(L) / sr
        s = rnd.randn(L); s = s - np.convolve(s, np.ones(3) / 3, "same")
        return 0.12 * s * np.sin(np.pi * x / x[-1])
    def bass(freq, dur):
        L = int(dur * sr); x = np.arange(L) / sr
        s = np.sin(2 * np.pi * freq * x) + 0.3 * np.sin(4 * np.pi * freq * x)
        return 0.45 * s * np.minimum(1, x / 0.01) * np.exp(-x * 2.5)
    def whoosh(L=0.35):
        m = int(L * sr); x = np.linspace(0, 1, m)
        s = np.convolve(rnd.randn(m), np.ones(20) / 20, "same")
        return 1.4 * s * np.sin(np.pi * x ** 0.7) ** 2

    beat = 60 / 112
    # I–V–vi–IV in C major, two beats per chord
    prog_ = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]), (45, [60, 64, 69, 72]), (41, [60, 65, 69, 72])]
    t = 0.0; k = 0
    while t < 6.55:
        root, ch = prog_[k % 4]
        for e in range(4):                      # 8th-note arpeggio
            at = t + e * beat / 2
            if at < 6.55: add(pluck(note(ch[[0, 2, 1, 3][e]] + 12), 0.55), at, 0.5)
        add(bass(note(root), beat * 2), t)
        for b in range(2):
            at = t + b * beat
            if at < 6.5:
                add(kick(), at, 0.85)
                if (k * 2 + b) % 2 == 1: add(clap(), at, 0.9)
        t += beat * 2; k += 1
    s = 0.0
    while s < 6.5:
        add(shaker(), s + beat / 4); s += beat / 2
    for c in CUTS[:-1]: add(whoosh(), c - 0.2, 0.8)
    # clap roll + rising noise into the logo reveal
    for i, at in enumerate(np.cumsum([0.16, 0.13, 0.11, 0.09, 0.08, 0.07, 0.06, 0.05])[:-1] + 5.95):
        add(clap(), at, 0.3 + 0.08 * i)
    m = int(0.9 * sr); x = np.linspace(0, 1, m)
    add(np.convolve(rnd.randn(m), np.ones(5) / 5, "same") * x ** 2.5 * 0.5, 5.7)
    # impact + bright C-major resolve under the end card
    L = int(2.4 * sr); x = np.arange(L) / sr
    boom = np.sin(2 * np.pi * (38 + 70 * np.exp(-x * 9)) * x) * np.exp(-x * 2.5)
    add(1.0 * boom, 6.6)
    add(kick(), 6.6, 1.0)
    pad_t = np.arange(int((DUR - 6.6) * sr)) / sr
    pad = sum(np.sin(2 * np.pi * note(m_) * pad_t) + 0.2 * np.sin(4 * np.pi * note(m_) * pad_t)
              for m_ in (48, 55, 60, 64, 67, 72)) / 6
    pad *= np.minimum(1, pad_t / 0.15) * np.exp(-pad_t * 0.35) * 0.55
    add(pad, 6.6)
    for i, m_ in enumerate((72, 76, 79, 84, 88)):           # rising sparkle arpeggio
        add(pluck(note(m_), 1.6, 0.997), 7.2 + i * 0.12, 0.35)
    out[-int(0.5 * sr):] *= np.linspace(1, 0, int(0.5 * sr))
    out = np.tanh(out * 1.2)
    out = out / np.max(np.abs(out)) * 0.89
    # gentle stereo width: delay right channel 12 ms on the plucks' energy
    r = np.concatenate([np.zeros(int(0.012 * sr)), out])[:n]
    st = np.stack([out, 0.85 * out + 0.15 * r], 1)
    with wave.open(os.path.join(OUT, "audio.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
    soundtrack()
    only = [float(a) for a in sys.argv[3:]]
    times = only if only else [i / FPS for i in range(N)]
    for i, t in enumerate(times):
        frame(t).save(os.path.join(OUT, "frames", f"{i:04d}.png"), compress_level=1)
    print("done", len(times))
