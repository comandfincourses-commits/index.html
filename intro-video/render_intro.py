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

# ---------- logo ----------
def logo(size):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = S / 100
    d.ellipse((2 * k, 2 * k, 98 * k, 98 * k), fill=NAVY, outline=GOLD, width=int(3 * k))
    fC, fF = font("ExtraBold", int(30 * k)), font("Bold", int(13 * k))
    d.text((50 * k, 33 * k), "C", font=fC, fill=WHITE, anchor="mm")
    d.text((50 * k, 55 * k), "FIN", font=fF, fill=GOLD, anchor="mm")
    pts = [(20, 82), (35, 74), (50, 79), (65, 68), (82, 60)]
    d.line([(x * k, y * k) for x, y in pts], fill=GREEN, width=int(4 * k), joint="curve")
    for x, y in (pts[0], pts[-1]):
        r = 2 * k; d.ellipse((x * k - r, y * k - r, x * k + r, y * k + r), fill=GREEN)
    return im.resize((size, size), Image.LANCZOS)
LOGO = logo(300)

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

def s_shatter(t, t0=4.0, t1=4.8):
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

TICKER = "  VALUATION  •  EQUITY RESEARCH  •  FP&A  •  INVESTMENT BANKING  •  "
def s_ticker(t, t0=4.8, t1=5.8):
    p = prog(t, t0, t1)
    img = Image.new("RGB", (W, H), (248, 249, 251))
    d = ImageDraw.Draw(img)
    tw = text_w(TICKER, F_HUGE, 4)
    x = W * 0.35 - p * (tw * 0.55)
    draw_tracked(d, (x, H / 2 - 120), TICKER, F_HUGE, NAVY, 4)
    for i, (yy, L, sp) in enumerate([(0.24, 520, 1.0), (0.30, 260, 1.6), (0.72, 420, 1.3), (0.78, 680, 0.8)]):
        xx = W - ((p * sp * 2400 + i * 330) % (W + L))
        d.rounded_rectangle((xx, H * yy, xx + L, H * yy + 18), radius=9, fill=GREEN if i % 2 == 0 else GOLD)
    return img

def s_name(t, t0=5.8, t1=6.6):
    """Tilted portrait, gold-tinted, with diagonal name sweep."""
    p = prog(t, t0, t1)
    img = kenburns(P_SPEAK, 0.4 + p * 0.6, 1.08, 1.18, -0.6)
    img = duotone(img, NAVY, GOLD, 0.35)
    img = gradient_overlay(img, NAVY, 0.15, 0.55, horizontal=False)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    q = ease_out(prog(t, t0, t0 + 0.4))
    big_text(layer, "CA ANKIT BAJAJ", F_BIG, W / 2 - (1 - q) * 900, H / 2, WHITE, alpha=q, track=10)
    layer = layer.rotate(8, resample=Image.BICUBIC, center=(W / 2, H / 2))
    img.paste(layer, (0, 0), layer)
    streaks(img, t, GOLD, 21, n=6, alpha=200)
    return img

def s_end(t, t0=6.6):
    """Logo reveal end-card with portrait (holds to 10s)."""
    img = BG_END.copy()
    # portrait slides in from the right
    pp = ease_out(prog(t, t0, t0 + 0.7))
    px = int(W - PORT_END.width * 0.98 + (1 - pp) * 500)
    img.paste(PORT_END, (px, 0), PORT_MASK)
    d = ImageDraw.Draw(img)
    cx = 600
    # logo: scale-in with rotation
    lp = prog(t, t0 + 0.15, t0 + 0.75)
    if lp > 0:
        s = back_out(lp, 1.4)
        sz = max(1, int(260 * s))
        lg = LOGO.resize((sz, sz), Image.LANCZOS).rotate((1 - ease_out(lp)) * -90, resample=Image.BICUBIC)
        img.paste(lg, (int(cx - sz / 2), int(360 - sz / 2)), lg)
        # expanding ring pulse
        rp = prog(t, t0 + 0.55, t0 + 1.2)
        if 0 < rp < 1:
            r = 150 + 200 * ease_out(rp)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse((cx - r, 360 - r, cx + r, 360 + r), outline=GOLD + (int(255 * (1 - rp)),), width=6)
            img.paste(ov, (0, 0), ov)
    # wordmark wipe
    wp = ease_out(prog(t, t0 + 0.6, t0 + 1.2))
    if wp > 0:
        fW = font("Black", 132)
        parts = [("COM", NAVY), ("and", GOLD), ("FIN", NAVY)]
        tw = sum(fW.getlength(s) for s, _ in parts)
        layer = Image.new("RGBA", (int(tw) + 20, 170), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer); x = 0
        for s_, col in parts:
            dl.text((x, 0), s_, font=fW, fill=col + (255,)); x += fW.getlength(s_)
        layer = layer.crop((0, 0, max(1, int(layer.width * wp)), layer.height))
        img.paste(layer, (int(cx - tw / 2), 520), layer)
    d = ImageDraw.Draw(img)
    # gold rule
    rp = ease_out(prog(t, t0 + 1.0, t0 + 1.5))
    if rp > 0:
        d.rectangle((cx - 330 * rp, 700, cx + 330 * rp, 706), fill=GOLD)
    # tagline + founder line fade/slide
    tp = ease_out(prog(t, t0 + 1.2, t0 + 1.8))
    if tp > 0:
        tag = "FINANCIAL MODELLING  •  VALUATION  •  CORPORATE TRAINING"
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        fT = font("SemiBold", 28)
        tw = text_w(tag, fT, 3)
        draw_tracked(dl, (cx - tw / 2, 730 + (1 - tp) * 30), tag, fT, NAVY + (int(255 * tp),), 3)
        img.paste(lay, (0, 0), lay)
    np_ = ease_out(prog(t, t0 + 1.5, t0 + 2.1))
    if np_ > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        f1, f2 = font("ExtraBold", 46), font("Medium", 34)
        n1, n2 = "CA Ankit Bajaj", "Founder, COMandFIN Edutech"
        bw = max(f1.getlength(n1), f2.getlength(n2)) + 80
        x0, y0 = cx - bw / 2, 820 + (1 - np_) * 30
        dl.rounded_rectangle((x0, y0, x0 + bw, y0 + 130), radius=14, fill=NAVY + (int(235 * np_),))
        dl.rectangle((x0, y0, x0 + 10, y0 + 130), fill=GOLD + (int(255 * np_),))
        dl.text((cx + 5, y0 + 40), n1, font=f1, fill=WHITE + (int(255 * np_),), anchor="mm")
        dl.text((cx + 5, y0 + 95), n2, font=f2, fill=GOLD + (int(255 * np_),), anchor="mm")
        img.paste(lay, (0, 0), lay)
    return img

SCENES = [
    (0.0, 1.0, s_open),
    (1.0, 2.0, lambda t: photo_scene(P_SPEAK, t, 1.0, 2.0, "CORPORATE TRAINING", NAVY, (120, 230, 200), 0.45, 0.5)),
    (2.0, 3.0, lambda t: photo_scene(P_LECTURE, t, 2.0, 3.0, "FINANCIAL MODELLING", NAVY, (240, 220, 170), 0.35, -0.5, align="left")),
    (3.0, 4.0, lambda t: photo_scene(P_GROUP, t, 3.0, 4.0, "INDUSTRY-READY SKILLS", NAVY, (150, 235, 210), 0.5, 0.4, label=False)),
    (4.0, 4.8, s_shatter),
    (4.8, 5.8, s_ticker),
    (5.8, 6.6, s_name),
    (6.6, 10.01, s_end),
]
CUTS = [s[0] for s in SCENES[1:]]

def frame(t):
    for t0, t1, fn in SCENES:
        if t0 <= t < t1:
            img = fn(t); break
    # whip blur + white flash around each cut
    for c in CUTS:
        dt = t - c
        if -0.1 <= dt < 0.1:
            img = whip(img, 1 - abs(dt) / 0.1)
            if 0 <= dt < 0.067:
                img = Image.blend(img, Image.new("RGB", (W, H), WHITE), 0.55 * (1 - dt / 0.067))
    # fade in / out
    if t < 0.15: img = Image.blend(Image.new("RGB", (W, H), WHITE), img, t / 0.15)
    return img

# ---------- soundtrack (synthesized; royalty-free) ----------
def soundtrack():
    sr = 48000; n = int(sr * DUR); tt = np.arange(n) / sr
    out = np.zeros(n); rnd = np.random.RandomState(7)
    def add(sig, at):
        i = int(at * sr); j = min(n, i + len(sig)); out[i:j] += sig[: j - i]
    def kick():
        L = int(0.35 * sr); x = np.arange(L) / sr
        f = 50 + 110 * np.exp(-x * 30)
        return 0.9 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 9)
    def hat():
        L = int(0.06 * sr); x = np.arange(L) / sr
        s = rnd.randn(L); s = s - np.convolve(s, np.ones(4) / 4, "same")
        return 0.18 * s * np.exp(-x * 60)
    def whoosh(L=0.45, up=True):
        m = int(L * sr); x = np.linspace(0, 1, m)
        s = rnd.randn(m); k = 24
        s = np.convolve(s, np.ones(k) / k, "same")
        env = np.sin(np.pi * (x if up else 1 - x) ** 0.7) ** 2
        return 1.6 * s * env
    def impact():
        L = int(2.5 * sr); x = np.arange(L) / sr
        boom = np.sin(2 * np.pi * (40 + 60 * np.exp(-x * 8)) * x) * np.exp(-x * 2.2)
        noise = np.convolve(rnd.randn(L), np.ones(8) / 8, "same") * np.exp(-x * 6) * 0.6
        return 0.9 * (boom + noise)
    beat = 60 / 128
    b = 0.0
    while b < 6.5:
        add(kick(), b); add(hat(), b + beat / 2); b += beat
    for c in CUTS[:-1]: add(whoosh(0.35), c - 0.22)
    # riser into the logo
    m = int(1.0 * sr); x = np.linspace(0, 1, m)
    riser = np.convolve(rnd.randn(m), np.ones(6) / 6, "same") * x ** 2 * 0.7
    riser += 0.25 * np.sin(2 * np.pi * np.cumsum(200 + 900 * x ** 2) / sr) * x ** 2
    add(riser, 5.6)
    add(impact(), 6.6)
    # warm pad chord under the end card (D major add9)
    pad_t = tt[tt >= 6.6] - 6.6
    pad = sum(np.sin(2 * np.pi * f * pad_t) for f in (146.83, 220.0, 293.66, 369.99, 329.63)) / 5
    pad *= np.minimum(1, pad_t / 0.4) * np.clip((DUR - 6.6 - pad_t) / 1.2, 0, 1) * 0.35
    out[-len(pad):] += pad
    # bell sting on wordmark
    bt = np.arange(int(1.5 * sr)) / sr
    bell = sum(a * np.sin(2 * np.pi * f * bt) for f, a in ((880, 1), (1320, .5), (1760, .3))) * np.exp(-bt * 3) * 0.18
    add(bell, 7.2)
    out[-int(0.3 * sr):] *= np.linspace(1, 0, int(0.3 * sr))
    out = out / np.max(np.abs(out)) * 0.89
    st = np.stack([out, out], 1)
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
