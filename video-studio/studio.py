#!/usr/bin/env python3
"""COMandFIN Video Studio.

Turns a voice-over + a scene spec (JSON) into a branded explainer video:
  * "short" -> 1080x1920 Shorts / Reels (30 s - 2 min)
  * "long"  -> 1920x1080 YouTube video (up to ~6 min)

Every frame is drawn with Pillow (flat cartoon characters, charts, captions,
COMandFIN branding, Like / Share / Subscribe call-outs) and encoded with ffmpeg.
Also writes a thumbnail and a publish kit (title, description, hashtags).

  python3 studio.py render spec.json --out OUTDIR [--draft] [--jobs 4]
  python3 studio.py thumb  spec.json --out OUTDIR
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile
from functools import lru_cache
import multiprocessing as mp

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
FPS = 30
SR = 48000

# ----------------------------------------------------------------- brand ----
NAVY, GOLD, GREEN, RED, BLUE = (11, 31, 58), (201, 154, 46), (15, 174, 131), (192, 57, 43), (37, 99, 235)
INK, PAPER, WHITE, GREY = (28, 28, 34), (250, 247, 240), (255, 255, 255), (91, 107, 130)
YT_RED = (230, 33, 23)
SKIN, SKIN2 = (241, 206, 172), (224, 178, 140)
WEBSITE = "www.COMandFIN.com"
TAGLINE = "Finance. Simplified."

FORMATS = {
    # stage = (x, y, w, h) of the illustrated area inside the frame
    "short": dict(W=1080, H=1920, stage=(0, 300, 1080, 1150), intro=0.0, outro=3.5),
    "long": dict(W=1920, H=1080, stage=(0, 0, 1920, 1080), intro=2.2, outro=8.0),
}

# ----------------------------------------------------------------- fonts ----
FONT_FILES = {"head": "Poppins-ExtraBold.ttf", "bold": "Poppins-Bold.ttf", "med": "Poppins-Medium.ttf",
              "hand": "Kalam-Bold.ttf", "script": "Caveat-Bold.ttf"}
FALLBACKS = ["Kalam-Bold.ttf", "NotoSansDevanagari-Bold.ttf"]


@lru_cache(None)
def _cmap(fname):
    return set(TTFont(os.path.join(FONT_DIR, fname)).getBestCmap())


@lru_cache(None)
def _font(fname, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, fname), max(6, int(size)))


def _runs(text, kind):
    """Split text into (font_file, chunk) runs so missing glyphs (e.g. Devanagari) fall back."""
    stack = [FONT_FILES[kind]] + FALLBACKS
    runs = []
    for ch in text:
        f = next((f for f in stack if ord(ch) in _cmap(f)), stack[0]) if not ch.isspace() else None
        if runs and (f is None or runs[-1][0] == f):
            runs[-1][1] += ch
        else:
            runs.append([f or stack[0], ch])
    return runs


def text_w(text, kind, size):
    return sum(_font(f, size).getlength(c) for f, c in _runs(text, kind))


def draw_text(d, x, y, text, kind, size, fill, stroke=0, stroke_fill=INK):
    """Draw at baseline-left (x, y) with per-glyph font fallback."""
    for f, c in _runs(text, kind):
        d.text((x, y), c, font=_font(f, size), fill=fill, anchor="ls",
               stroke_width=int(stroke), stroke_fill=stroke_fill)
        x += _font(f, size).getlength(c)
    return x


def parse_rich(s):
    """'Profit is *not* cash' -> [(word, highlighted)]"""
    out, hl = [], False
    for li, line in enumerate((s or "").split("\n")):
        if li:
            out.append(("\n", False))
        for tok in line.split():
            word_hl = (not hl) if tok.startswith("*") else hl
            hl ^= tok.count("*") % 2 == 1
            if tok.replace("*", ""):
                out.append((tok.replace("*", ""), word_hl))
    return out


def wrap_words(words, kind, size, max_w):
    lines, cur, cw = [], [], 0
    sp = text_w(" ", kind, size)
    for w, hl in words:
        if w == "\n":
            if cur:
                lines.append(cur)
            cur, cw = [], 0
            continue
        ww = text_w(w, kind, size)
        if cur and cw + sp + ww > max_w:
            lines.append(cur)
            cur, cw = [], 0
        cw += (sp if cur else 0) + ww
        cur.append((w, hl))
    if cur:
        lines.append(cur)
    return lines


def rich_block(s, kind, size, max_w, color, hl=GOLD, stroke=0, stroke_fill=INK, align="center",
               lh=1.18, max_lines=None):
    """Render rich text to a transparent sprite. Auto-shrinks to fit max_lines."""
    words = parse_rich(s) if isinstance(s, str) else s
    while True:
        lines = wrap_words(words, kind, size, max_w)
        if not max_lines or len(lines) <= max_lines or size < 18:
            break
        size *= 0.92
    sp = text_w(" ", kind, size)
    widths = [sum(text_w(w, kind, size) for w, _ in ln) + sp * (len(ln) - 1) for ln in lines]
    pad = int(stroke + size * 0.15)
    W = int(max(widths or [1]) + 2 * pad)
    H = int(len(lines) * size * lh + size * 0.35 + 2 * pad)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (ln, lw) in enumerate(zip(lines, widths)):
        x = pad + {"center": (W - 2 * pad - lw) / 2, "left": 0, "right": W - 2 * pad - lw}[align]
        y = pad + size * (0.95 + i * lh)
        for w, h in ln:
            x = draw_text(d, x, y, w, kind, size, hl if h else color, stroke, stroke_fill) + sp
    return img


# --------------------------------------------------------------- helpers ----
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_back(t):
    t = clamp(t)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def paste(base, sprite, x, y, scale=1.0, alpha=1.0, anchor="center"):
    """Alpha-composite sprite with its anchor point at (x, y)."""
    if sprite is None or alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        sprite = sprite.resize((max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))),
                               Image.BILINEAR)
    if alpha < 0.99:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda a: int(a * alpha)))
    ax = {"center": 0.5, "top": 0.5, "bottom": 0.5, "left": 0, "topleft": 0, "right": 1, "topright": 1}[anchor]
    ay = {"center": 0.5, "top": 0, "bottom": 1, "left": 0.5, "topleft": 0, "right": 0.5, "topright": 0}[anchor]
    base.alpha_composite(sprite, (int(x - sprite.width * ax), int(y - sprite.height * ay)))


def supersample(w, h, fn, mode="RGBA"):
    """Draw at 2x with fn(draw, k) and downsample for anti-aliased shapes."""
    img = Image.new(mode, (w * 2, h * 2), (0, 0, 0, 0) if mode == "RGBA" else WHITE)
    fn(ImageDraw.Draw(img), 2)
    return img.resize((w, h), Image.LANCZOS)


@lru_cache(8)
def radial(w, h, c1, c2, cx=0.5, cy=0.42):
    y, x = np.ogrid[0:h, 0:w]
    dd = np.clip(np.sqrt(((x - cx * w) / w) ** 2 + ((y - cy * h) / h) ** 2) / 0.75, 0, 1)[..., None]
    arr = (np.array(c1) * (1 - dd) + np.array(c2) * dd).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


# ------------------------------------------------------------------ logo ----
@lru_cache(16)
def logo(size):
    """COMandFIN roundel (matches the logo used on COMandFIN learning labs)."""
    def fn(d, k):
        s = size * k / 100
        d.ellipse((2 * s, 2 * s, 98 * s, 98 * s), fill=NAVY, outline=GOLD, width=int(4 * s))
        d.text((50 * s, 47 * s), "C", font=_font("Poppins-ExtraBold.ttf", 34 * s), fill=WHITE, anchor="ms")
        d.text((50 * s, 68 * s), "FIN", font=_font("Poppins-Bold.ttf", 14 * s), fill=GOLD, anchor="ms")
        d.line([(20 * s, 80 * s), (35 * s, 67 * s), (50 * s, 74 * s), (65 * s, 57 * s), (82 * s, 42 * s)],
               fill=GREEN, width=int(5 * s), joint="curve")
    return supersample(size, size, fn)


@lru_cache(16)
def wordmark(size, dark_bg=True):
    """'COMandFIN' wordmark: COM + and + FIN."""
    c1 = WHITE if dark_bg else NAVY
    parts = [("COM", c1, "head"), ("and", GOLD, "bold"), ("FIN", c1, "head")]
    w = int(sum(text_w(t, k, size) for t, _, k in parts) + size * 0.2)
    img = Image.new("RGBA", (w, int(size * 1.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = size * 0.05
    for t, c, k in parts:
        x = draw_text(d, x, size * 1.0, t, k, size, c)
    return img


# ------------------------------------------------------------- characters ---
CAST = {
    "prof": dict(skin=SKIN, hair=(45, 38, 36), style="side", glasses=True, top=NAVY, shirt=WHITE, tie=GOLD,
                 legs=(40, 40, 48)),
    "student": dict(skin=SKIN2, hair=(92, 60, 36), style="messy", top=GREEN, hoodie=True, legs=(50, 60, 90)),
    "investor": dict(skin=SKIN, hair=(178, 178, 178), style="side", glasses=True, top=(62, 64, 72), shirt=WHITE,
                     tie=RED, legs=(45, 45, 50), beard=(170, 170, 170)),
    "woman": dict(skin=SKIN, hair=(35, 30, 30), style="long", top=(150, 40, 60), legs=(40, 40, 50)),
    "generic": dict(skin=WHITE, hair=None, top=(118, 150, 205), legs=(50, 50, 60)),
    "boss": dict(skin=SKIN2, hair=(30, 30, 30), style="bald", glasses=False, top=(30, 30, 36), shirt=WHITE,
                 tie=BLUE, legs=(30, 30, 36)),
}


@lru_cache(maxsize=1024)
def character(who, mood="neutral", pose="idle", mouth=0, blink=False, height=600):
    """Flat cartoon character, unit box 600 x 1000, feet at the bottom edge."""
    c = CAST.get(who, CAST["generic"])
    w = int(height * 0.6)

    def fn(d, k):
        s = height * k / 1000
        P = lambda x, y: (x * s, y * s)
        B = lambda x0, y0, x1, y1: (x0 * s, y0 * s, x1 * s, y1 * s)
        lw = max(2, int(13 * s))
        # legs
        for x0, x1 in ((255, 245), (345, 355)):
            d.line([P(x0, 760), P(x1, 975)], fill=INK, width=int(20 * s))
            d.line([P(x0, 760), P(x1, 975)], fill=c["legs"], width=int(10 * s))
        d.ellipse(B(205, 955, 268, 990), fill=INK)
        d.ellipse(B(332, 955, 395, 990), fill=INK)
        # long hair behind head
        if c.get("style") == "long":
            d.rounded_rectangle(B(98, 150, 502, 520), radius=int(150 * s), fill=c["hair"], outline=INK, width=lw)
        # arms
        arms = {"idle": [((190, 470), (165, 600), (150, 720)), ((410, 470), (435, 600), (450, 720))],
                "point": [((190, 470), (165, 600), (150, 720)), ((410, 470), (500, 420), (575, 330))],
                "wave": [((190, 470), (165, 600), (150, 720)), ((410, 470), (520, 430), (560, 280))],
                "shrug": [((190, 470), (95, 560), (55, 450)), ((410, 470), (505, 560), (545, 450))],
                "think": [((190, 470), (165, 600), (150, 720)), ((410, 470), (420, 600), (330, 420))],
                "cheer": [((190, 470), (110, 360), (70, 230)), ((410, 470), (490, 360), (530, 230))]}[pose]
        for a in arms:
            pts = [P(*p) for p in a]
            d.line(pts, fill=INK, width=int(26 * s), joint="curve")
            d.line(pts, fill=c["top"], width=int(12 * s), joint="curve")
            hx, hy = a[-1]
            d.ellipse(B(hx - 24, hy - 24, hx + 24, hy + 24), fill=c["skin"], outline=INK, width=lw)
        # body
        d.rounded_rectangle(B(165, 420, 435, 800), radius=int(95 * s), fill=c["top"], outline=INK, width=lw)
        if c.get("shirt"):
            d.polygon([P(245, 428), P(300, 545), P(355, 428)], fill=c["shirt"], outline=INK)
            d.polygon([P(290, 450), P(310, 450), P(320, 560), P(300, 595), P(280, 560)], fill=c["tie"])
        if c.get("hoodie"):
            d.line([P(270, 440), P(262, 540)], fill=WHITE, width=int(7 * s))
            d.line([P(330, 440), P(338, 540)], fill=WHITE, width=int(7 * s))
            d.rounded_rectangle(B(220, 640, 380, 730), radius=int(30 * s), outline=INK, width=int(7 * s))
        # head
        d.ellipse(B(115, 65, 485, 435), fill=c["skin"], outline=INK, width=lw)
        st = c.get("style")
        if c.get("hair") and st != "bald":
            d.chord(B(108, 52, 492, 420), 192, 348, fill=c["hair"], outline=INK, width=lw)
            if st == "side":
                d.polygon([P(150, 150), P(330, 128), P(240, 205)], fill=c["hair"])
            if st == "messy":
                for x in (170, 230, 290, 350, 410):
                    d.polygon([P(x - 35, 120), P(x + 10, 30), P(x + 35, 120)], fill=c["hair"], outline=INK)
                d.chord(B(108, 52, 492, 420), 192, 348, fill=c["hair"])
            if st == "long":
                d.chord(B(108, 52, 492, 420), 185, 355, fill=c["hair"], outline=INK, width=lw)
        # face
        sad = mood in ("worried", "sad")
        brows = {"neutral": ((205, 200, 262, 198), (338, 198, 395, 200)),
                 "happy": ((205, 196, 262, 186), (338, 186, 395, 196)),
                 "worried": ((205, 212, 262, 190), (338, 190, 395, 212)),
                 "sad": ((205, 212, 262, 190), (338, 190, 395, 212)),
                 "angry": ((205, 188, 262, 212), (338, 212, 395, 188)),
                 "serious": ((205, 192, 262, 206), (338, 206, 395, 192)),
                 "surprised": ((205, 172, 262, 165), (338, 165, 395, 172))}.get(mood)
        if brows and not (c.get("glasses") and mood == "neutral"):
            for b in brows:
                d.line([P(b[0], b[1]), P(b[2], b[3])], fill=INK, width=int(11 * s))
        er = 22 if mood == "surprised" else 16
        for ex in (235, 365):
            if blink:
                d.line([P(ex - 18, 262), P(ex + 18, 262)], fill=INK, width=int(8 * s))
            else:
                d.ellipse(B(ex - er, 262 - er, ex + er, 262 + er), fill=INK)
        if c.get("glasses"):
            for gx in (235, 365):
                d.rounded_rectangle(B(gx - 55, 225, gx + 55, 298), radius=int(14 * s), outline=INK,
                                    width=int(9 * s))
            d.line([P(290, 255), P(310, 255)], fill=INK, width=int(8 * s))
        if mood == "happy":
            for cx in (190, 410):
                d.ellipse(B(cx - 26, 305, cx + 26, 330), fill=(245, 165, 150))
        if c.get("beard"):
            d.chord(B(240, 330, 360, 430), 0, 180, fill=c["beard"], outline=INK, width=int(7 * s))
        if mouth:
            mw, mh = 26 + 8 * mouth, 10 + 14 * mouth
            d.ellipse(B(300 - mw, 352 - mh, 300 + mw, 352 + mh), fill=(110, 35, 40), outline=INK,
                      width=int(8 * s))
        elif mood == "happy":
            d.chord(B(250, 300, 350, 385), 15, 165, fill=(110, 35, 40), outline=INK, width=int(8 * s))
        elif sad:
            d.arc(B(258, 350, 342, 410), 200, 340, fill=INK, width=int(9 * s))
        elif mood == "surprised":
            d.ellipse(B(282, 335, 318, 380), fill=(110, 35, 40), outline=INK, width=int(8 * s))
        elif mood == "angry":
            d.line([P(270, 362), P(330, 356)], fill=INK, width=int(9 * s))
        else:
            d.arc(B(265, 320, 335, 370), 30, 150, fill=INK, width=int(9 * s))
    return supersample(w, height, fn)


# ------------------------------------------------------------------ icons ---
@lru_cache(256)
def icon(kind, size, color=None):
    """Simple flat icons drawn in a 100x100 unit box."""
    def fn(d, k):
        s = size * k / 100
        P = lambda x, y: (x * s, y * s)
        B = lambda x0, y0, x1, y1: (x0 * s, y0 * s, x1 * s, y1 * s)
        lw = max(2, int(5 * s))
        if kind in ("up", "down"):
            col = color or (GREEN if kind == "up" else RED)
            pts = [(8, 82), (32, 58), (50, 70), (84, 28)] if kind == "up" else [(8, 22), (32, 46), (50, 36), (84, 76)]
            d.line([P(*p) for p in pts], fill=INK, width=int(17 * s), joint="curve")
            d.line([P(*p) for p in pts], fill=col, width=int(9 * s), joint="curve")
            tip = [(92, 18), (68, 24), (86, 42)] if kind == "up" else [(92, 86), (68, 80), (86, 62)]
            d.polygon([P(*p) for p in tip], fill=col, outline=INK, width=lw)
        elif kind == "coin":
            d.ellipse(B(6, 6, 94, 94), fill=color or GOLD, outline=INK, width=lw)
            d.ellipse(B(18, 18, 82, 82), outline=(160, 118, 30), width=lw)
            d.text(P(50, 52), "₹", font=_font("Poppins-ExtraBold.ttf", 46 * s), fill=WHITE, anchor="mm",
                   stroke_width=int(2 * s), stroke_fill=(160, 118, 30))
        elif kind == "bag":
            d.ellipse(B(14, 30, 86, 96), fill=(196, 160, 96), outline=INK, width=lw)
            d.polygon([P(36, 34), P(30, 10), P(70, 10), P(64, 34)], fill=(196, 160, 96), outline=INK)
            d.line([P(34, 32), P(66, 32)], fill=INK, width=lw)
            d.text(P(50, 66), "₹", font=_font("Poppins-ExtraBold.ttf", 38 * s), fill=GREEN, anchor="mm")
        elif kind == "bulb":
            d.ellipse(B(22, 6, 78, 62), fill=(255, 214, 80), outline=INK, width=lw)
            d.rectangle(B(37, 58, 63, 80), fill=(150, 150, 160), outline=INK, width=lw)
            d.line([P(37, 68), P(63, 68)], fill=INK, width=lw)
            for a in range(0, 360, 45):
                x, y = 50 + 46 * math.cos(math.radians(a)), 34 + 46 * math.sin(math.radians(a))
                if y < 60:
                    d.line([P(50 + 36 * math.cos(math.radians(a)), 34 + 36 * math.sin(math.radians(a))), P(x, y)],
                           fill=GOLD, width=lw)
        elif kind == "bank":
            d.polygon([P(8, 34), P(50, 8), P(92, 34)], fill=(220, 220, 228), outline=INK, width=lw)
            for x in (20, 40, 60, 80):
                d.rectangle(B(x - 5, 38, x + 5, 80), fill=WHITE, outline=INK, width=lw)
            d.rectangle(B(8, 82, 92, 94), fill=(220, 220, 228), outline=INK, width=lw)
        elif kind == "chart":
            d.rounded_rectangle(B(4, 4, 96, 96), radius=int(10 * s), fill=WHITE, outline=INK, width=lw)
            for i, h in enumerate((30, 50, 42, 72)):
                d.rectangle(B(16 + i * 19, 86 - h, 30 + i * 19, 86), fill=(GREEN, BLUE, GOLD, GREEN)[i])
        elif kind == "warning":
            d.polygon([P(50, 6), P(96, 90), P(4, 90)], fill=(255, 196, 0), outline=INK, width=lw)
            d.text(P(50, 64), "!", font=_font("Poppins-ExtraBold.ttf", 52 * s), fill=INK, anchor="mm")
        elif kind in ("check", "cross"):
            d.ellipse(B(4, 4, 96, 96), fill=GREEN if kind == "check" else RED, outline=INK, width=lw)
            pts = [(28, 52), (44, 68), (74, 34)] if kind == "check" else None
            if pts:
                d.line([P(*p) for p in pts], fill=WHITE, width=int(11 * s), joint="curve")
            else:
                d.line([P(32, 32), P(68, 68)], fill=WHITE, width=int(11 * s))
                d.line([P(68, 32), P(32, 68)], fill=WHITE, width=int(11 * s))
        elif kind == "target":
            for r, col in ((46, RED), (34, WHITE), (22, RED), (10, WHITE)):
                d.ellipse(B(50 - r, 50 - r, 50 + r, 50 + r), fill=col, outline=INK, width=max(1, lw // 2))
        elif kind == "doc":
            d.rounded_rectangle(B(16, 4, 84, 96), radius=int(8 * s), fill=WHITE, outline=INK, width=lw)
            for y in (24, 40, 56, 72):
                d.line([P(28, y), P(72 if y != 72 else 56, y)], fill=GREY, width=lw)
        elif kind == "like":
            d.rounded_rectangle(B(8, 44, 28, 92), radius=int(4 * s), fill=color or WHITE, outline=INK, width=lw)
            d.polygon([P(34, 46), P(50, 10), P(60, 10), P(62, 40), P(88, 42), P(92, 52), P(84, 92), P(34, 92)],
                      fill=color or WHITE, outline=INK, width=lw)
        elif kind == "share":
            pts = [(24, 50), (74, 22), (74, 78)]
            d.line([P(*pts[1]), P(*pts[0]), P(*pts[2])], fill=INK, width=int(8 * s))
            for x, y in pts:
                d.ellipse(B(x - 15, y - 15, x + 15, y + 15), fill=color or BLUE, outline=INK, width=lw)
        elif kind == "bell":
            col = color or GOLD
            d.pieslice(B(22, 10, 78, 66), 180, 360, fill=col, outline=INK, width=lw)
            d.rectangle(B(22, 37, 78, 70), fill=col)
            d.line([P(22, 38), P(22, 70)], fill=INK, width=lw)
            d.line([P(78, 38), P(78, 70)], fill=INK, width=lw)
            d.polygon([P(12, 80), P(88, 80), P(78, 66), P(22, 66)], fill=col, outline=INK, width=lw)
            d.ellipse(B(42, 78, 58, 94), fill=INK)
    return supersample(size, size, fn)


# ------------------------------------------------------------ backgrounds ---
@lru_cache(32)
def background(kind, w, h):
    if kind == "studio":
        return radial(w, h, (34, 64, 108), (8, 18, 36)).copy()
    if kind == "dark":
        return radial(w, h, (34, 46, 44), (8, 11, 12)).copy()
    if kind == "brand":
        return radial(w, h, (24, 70, 120), NAVY).copy()

    def fn(d, k):
        W, H = w * k, h * k
        lw = int(4 * k * h / 1080)
        if kind == "office":
            d.rectangle((0, 0, W, H), fill=(228, 216, 198))
            d.rectangle((0, H * 0.64, W, H), fill=(200, 180, 152))
            d.line([(0, H * 0.64), (W, H * 0.64)], fill=INK, width=lw)
            d.rectangle((0, H * 0.88, W, H), fill=(146, 108, 80))
            d.line([(0, H * 0.88), (W, H * 0.88)], fill=INK, width=lw)
            wx0, wy0, wx1, wy1 = W * 0.62, H * 0.08, W * 0.93, H * 0.5
            d.rectangle((wx0, wy0, wx1, wy1), fill=(176, 214, 236))
            for i, (bx, bh) in enumerate(((0.0, 0.55), (0.14, 0.75), (0.3, 0.45), (0.45, 0.85), (0.62, 0.6),
                                          (0.8, 0.7))):
                x0 = wx0 + (wx1 - wx0) * bx
                d.rectangle((x0, wy1 - (wy1 - wy0) * bh, x0 + (wx1 - wx0) * 0.16, wy1),
                            fill=(130, 160, 192) if i % 2 else (112, 142, 178))
            d.rectangle((wx0, wy0, wx1, wy1), outline=INK, width=lw * 2)
            d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=INK, width=lw)
            fx0, fy0, fx1, fy1 = W * 0.07, H * 0.1, W * 0.3, H * 0.34
            d.rectangle((fx0, fy0, fx1, fy1), fill=WHITE, outline=INK, width=lw)
            pts = [(0.1, 0.8), (0.3, 0.6), (0.5, 0.68), (0.72, 0.38), (0.9, 0.2)]
            d.line([(fx0 + (fx1 - fx0) * x, fy0 + (fy1 - fy0) * y) for x, y in pts], fill=GREEN,
                   width=lw * 2, joint="curve")
        elif kind == "classroom":
            d.rectangle((0, 0, W, H), fill=(204, 214, 196))
            d.rectangle((W * 0.05, H * 0.05, W * 0.95, H * 0.55), fill=(150, 105, 60), outline=INK, width=lw)
            d.rectangle((W * 0.07, H * 0.07, W * 0.93, H * 0.53), fill=(42, 82, 62), outline=INK, width=lw)
            d.rectangle((W * 0.3, H * 0.55, W * 0.7, H * 0.575), fill=(150, 105, 60), outline=INK, width=lw)
            d.rectangle((0, H * 0.88, W, H), fill=(160, 122, 92))
            d.line([(0, H * 0.88), (W, H * 0.88)], fill=INK, width=lw)
        elif kind == "city":
            for y in range(0, H, 4):
                t = y / H
                d.rectangle((0, y, W, y + 4), fill=tuple(int(a + (b - a) * t) for a, b in
                                                          zip((150, 200, 235), (222, 238, 246))))
            rng = np.random.default_rng(7)
            x = 0
            while x < W:
                bw, bh = W * rng.uniform(0.06, 0.13), H * rng.uniform(0.25, 0.6)
                col = (96, 128, 168) if rng.random() > 0.5 else (74, 102, 140)
                d.rectangle((x, H * 0.88 - bh, x + bw, H * 0.88), fill=col, outline=INK, width=lw)
                for wy in np.arange(H * 0.88 - bh + 20 * k, H * 0.86, 34 * k * h / 1080):
                    for wx in np.arange(x + 12 * k, x + bw - 18 * k, 30 * k * h / 1080):
                        d.rectangle((wx, wy, wx + 12 * k, wy + 16 * k), fill=(250, 226, 150))
                x += bw + W * 0.01
            d.rectangle((0, H * 0.88, W, H), fill=(92, 100, 110))
        else:  # paper
            d.rectangle((0, 0, W, H), fill=PAPER)
            step = int(h * k * 0.06)
            for x in range(0, W, step):
                d.line([(x, 0), (x, H)], fill=(236, 230, 218), width=k)
            for y in range(0, H, step):
                d.line([(0, y), (W, y)], fill=(236, 230, 218), width=k)
    return supersample(w, h, fn, mode="RGB").convert("RGBA")


# ---------------------------------------------------------------- bubbles ---
@lru_cache(64)
def bubble(text, size, max_w, tail="left", think=False):
    body = rich_block(text, "hand", size, max_w, INK, hl=RED, max_lines=4)
    pad = int(size * 0.55)
    tw, th = body.width + 2 * pad, body.height + 2 * pad
    tail_h = int(size * 1.1)

    def fn(d, k):
        lw = max(2, int(size * 0.09 * k))
        d.rounded_rectangle((lw, lw, (tw - 1) * k - lw, th * k - lw), radius=int(size * 0.8 * k), fill=WHITE,
                            outline=INK, width=lw)
        tx = tw * k * (0.22 if tail == "left" else 0.78)
        dx = -size * 0.5 * k if tail == "left" else size * 0.5 * k
        if think:
            for i, r in enumerate((0.32, 0.22)):
                cx, cy = tx + dx * (i + 0.6), th * k + tail_h * k * (0.3 + i * 0.45)
                d.ellipse((cx - r * size * k, cy - r * size * k, cx + r * size * k, cy + r * size * k), fill=WHITE,
                          outline=INK, width=lw)
        else:
            pts = [(tx - size * 0.45 * k, th * k - lw * 2.2), (tx + size * 0.45 * k, th * k - lw * 2.2),
                   (tx + dx * 1.4, (th + tail_h) * k)]
            d.polygon(pts, fill=WHITE)
            d.line([pts[0], pts[2], pts[1]], fill=INK, width=lw, joint="curve")
    img = supersample(tw, th + tail_h, fn)
    img.alpha_composite(body, (pad, pad))
    return img


# ------------------------------------------------------------------ scenes ---
class Ctx:
    """Per-render state shared by the frame functions."""

    def __init__(self, spec, fmt, draft=False):
        self.spec, self.fmt_name = spec, fmt
        f = dict(FORMATS[fmt])
        k = 0.5 if draft else 1.0
        self.k = k
        self.W, self.H = int(f["W"] * k), int(f["H"] * k)
        sx, sy, sw, sh = f["stage"]
        self.stage = (int(sx * k), int(sy * k), int(sw * k), int(sh * k))
        self.u = min(self.W, self.H) / 1080
        self.intro = spec.get("intro", f["intro"])
        self.outro = spec.get("outro", f["outro"])
        self.short = fmt == "short"


def scene_static(ctx, sc):
    """Everything in a scene that does not move, rendered once per scene."""
    _, _, w, h = ctx.stage
    typ = sc["type"]
    bg = sc.get("bg") or {"title": "studio", "character": "office", "chart": "paper", "bignumber": "dark",
                          "list": "paper", "compare": "paper", "formula": "classroom", "quote": "dark"}.get(typ, "paper")
    img = background(bg, w, h).copy()
    d = ImageDraw.Draw(img)
    title = sc.get("title")
    if title and typ in ("chart", "list", "compare"):
        t = rich_block(title, "head", h * 0.058, w * 0.86, NAVY, hl=GOLD if bg != "paper" else BLUE, max_lines=2)
        paste(img, t, w / 2, h * 0.045, anchor="top")
        sc["_title_h"] = t.height
    if typ == "chart":
        x0, x1, y0, y1 = chart_box(ctx, sc)
        for i in range(5):
            y = y1 - (y1 - y0) * i / 4
            d.line([(x0, y), (x1, y)], fill=(220, 212, 198), width=max(1, int(2 * ctx.u)))
        d.line([(x0, y1), (x1, y1)], fill=INK, width=max(2, int(4 * ctx.u)))
        labels = sc.get("labels", [])
        n = len(sc["values"])
        for i, lb in enumerate(labels):
            cx = x0 + (x1 - x0) * ((i + 0.5) / n)
            lbs = rich_block(str(lb), "bold", h * 0.034, (x1 - x0) / n * 0.9, GREY, max_lines=2)
            paste(img, lbs, cx, y1 + h * 0.012, anchor="top")
    return img


def safe_bottom(ctx):
    """Lowest y (fraction of stage) for content; long videos keep the caption band clear."""
    return 0.97 if ctx.short else 0.84


def chart_box(ctx, sc):
    _, _, w, h = ctx.stage
    return w * 0.08, w * 0.92, h * 0.26, h * (0.8 if ctx.short else 0.68)


def fmt_val(v, sc):
    dec = sc.get("decimals", 0)
    s = f"{v:,.{dec}f}"
    return f"{sc.get('prefix', '')}{s}{sc.get('suffix', '')}"


def draw_cast(ctx, img, sc, lt, mouth_level, talking):
    _, _, w, h = ctx.stage
    cast = sc.get("cast") or []
    if not cast:
        return []
    xs = {1: [0.27], 2: [0.22, 0.78], 3: [0.17, 0.5, 0.83]}[min(3, len(cast))]
    ch_h = int(h * sc.get("char_scale", 0.6 if not ctx.short else 0.58))
    feet = h * 0.965
    heads = []
    for i, c in enumerate(cast[:3]):
        x = w * c.get("x", xs[i])
        speaking = i == sc.get("speaker", 0) and talking
        m = mouth_level if speaking else 0
        blink = ((lt + i * 1.3) % 3.6) < 0.12
        bob = math.sin((lt + i) * math.pi * 1.2) * h * 0.004 + (h * 0.006 * m if speaking else 0)
        ent = ease_back(lt / 0.35)
        spr = character(c.get("who", "generic"), c.get("mood", "neutral"), c.get("pose", "idle"), m, blink, ch_h)
        sh = Image.new("RGBA", (int(ch_h * 0.42), int(ch_h * 0.06)), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((0, 0, sh.width, sh.height), fill=(0, 0, 0, 50))
        paste(img, sh, x, feet - ch_h * 0.012)
        paste(img, spr, x, feet + bob + (1 - ent) * h * 0.25, anchor="bottom")
        heads.append((x, feet - ch_h))
    return heads


def render_scene(ctx, sc, static, lt, mouth_level, talking):
    _, _, w, h = ctx.stage
    img = static.copy()
    d = ImageDraw.Draw(img)
    typ, dur = sc["type"], sc["_dur"]
    u = ctx.u

    if typ == "title":
        if sc.get("tag"):
            tg = rich_block(sc["tag"].upper(), "bold", h * 0.032, w, NAVY)
            pill = Image.new("RGBA", (tg.width + int(40 * u), tg.height + int(10 * u)), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), radius=pill.height // 2,
                                                   fill=GOLD)
            pill.alpha_composite(tg, (int(20 * u), int(5 * u)))
            paste(img, pill, w / 2, h * 0.2, scale=ease_back(lt / 0.4))
        hd = rich_block(sc["text"], "head", h * (0.1 if ctx.short else 0.11), w * 0.86, WHITE, hl=GOLD,
                        stroke=int(4 * u), max_lines=3)
        paste(img, hd, w / 2, h * 0.27, scale=0.6 + 0.4 * ease_back((lt - 0.1) / 0.45),
              alpha=clamp((lt - 0.1) / 0.2), anchor="top")
        y = h * 0.27 + hd.height
        if sc.get("sub"):
            sb = rich_block(sc["sub"], "hand", h * 0.05, w * 0.84, (210, 222, 240), hl=GOLD, max_lines=2)
            paste(img, sb, w / 2, y + h * 0.03, alpha=clamp((lt - 0.5) / 0.3), anchor="top")
            y += h * 0.03 + sb.height
        if sc.get("icon"):
            size = int(min(h * 0.16, h * safe_bottom(ctx) - y - h * 0.04))
            if size > h * 0.06:
                paste(img, icon(sc["icon"], size), w / 2, y + h * 0.02 + size / 2 + math.sin(lt * 3) * h * 0.01,
                      scale=ease_back((lt - 0.6) / 0.4))
        if sc.get("cast"):
            draw_cast(ctx, img, sc, lt, mouth_level, talking)

    elif typ == "character":
        if sc.get("board"):
            n = len(sc["board"])
            shown = sc["board"][:int(n * clamp(lt / max(0.6, dur * 0.4)))]
            bd = rich_block(shown, "hand", h * 0.07, w * 0.8, (240, 240, 230), hl=(255, 214, 80), max_lines=3)
            paste(img, bd, w / 2, h * 0.3)
        heads = draw_cast(ctx, img, sc, lt, mouth_level, talking)
        if sc.get("prop"):
            px = w * (0.72 if len(heads) == 1 and heads[0][0] < w / 2 else 0.5 if len(heads) != 1 else 0.28)
            ic = icon(sc["prop"], int(h * 0.24))
            paste(img, ic, px, h * 0.6 + math.sin(lt * 2.4) * h * 0.012, scale=ease_back((lt - 0.3) / 0.4))
        if sc.get("say") and heads:
            si = min(sc.get("speaker", 0), len(heads) - 1)
            hx, hy = heads[si]
            left = hx < w / 2
            bb = bubble(sc["say"], int(h * (0.048 if ctx.short else 0.05)), int(w * (0.6 if ctx.short else 0.42)),
                        "left" if left else "right", sc.get("think", False))
            bx = clamp(hx - bb.width * 0.2 if left else hx - bb.width * 0.8, w * 0.03, w * 0.97 - bb.width)
            by = max(h * 0.03, hy - bb.height - h * 0.01)
            sc_ = ease_back((lt - 0.15) / 0.3)
            paste(img, bb, bx + bb.width / 2, by + bb.height, scale=sc_, anchor="bottom")

    elif typ == "chart":
        x0, x1, y0, y1 = chart_box(ctx, sc)
        vals = sc["values"]
        n = len(vals)
        vmax = max(vals) * 1.15 if max(vals) > 0 else 1
        trend = GREEN if vals[-1] >= vals[0] else RED
        col = {"green": GREEN, "red": RED, "blue": BLUE, "gold": GOLD}.get(sc.get("color"), trend)
        p = ease_out(lt / max(0.8, dur * 0.55))
        vs = h * 0.036
        if sc.get("kind", "bar") == "bar":
            bw = (x1 - x0) / n * 0.56
            for i, v in enumerate(vals):
                gi = ease_out((p * (n + 2) - i) / 3)
                cx = x0 + (x1 - x0) * ((i + 0.5) / n)
                top = y1 - (y1 - y0) * (v / vmax) * gi
                c = sc.get("colors", [None] * n)[i] if sc.get("colors") else col
                c = {"green": GREEN, "red": RED, "blue": BLUE, "gold": GOLD, "navy": NAVY}.get(c, c) or col
                if gi > 0.01:
                    d.rounded_rectangle((cx - bw / 2, top, cx + bw / 2, y1), radius=int(10 * u), fill=c,
                                        outline=INK, width=max(1, int(3 * u)))
                if gi > 0.9:
                    lb = rich_block(fmt_val(v, sc), "bold", vs, w, INK)
                    paste(img, lb, cx, top - h * 0.005, alpha=clamp((gi - 0.9) * 10), anchor="bottom")
        else:
            pts = [(x0 + (x1 - x0) * ((i + 0.5) / n), y1 - (y1 - y0) * (v / vmax)) for i, v in enumerate(vals)]
            lay = line_layer(int(w), int(h), tuple(pts), col, y1, u)
            cut = int(pts[0][0] + (pts[-1][0] - pts[0][0]) * p) + int(12 * u)
            img.alpha_composite(lay.crop((0, 0, max(1, cut), int(h))), (0, 0))
            for (px, py), v in zip(pts, vals):
                if px <= cut:
                    d.ellipse((px - 11 * u, py - 11 * u, px + 11 * u, py + 11 * u), fill=WHITE, outline=INK,
                              width=max(1, int(4 * u)))
                    paste(img, rich_block(fmt_val(v, sc), "bold", vs, w, INK), px, py - h * 0.018, anchor="bottom")
        if sc.get("note"):
            nt = rich_block(sc["note"], "hand", h * 0.05, w * 0.85, col, hl=NAVY)
            paste(img, nt, w / 2, h * safe_bottom(ctx), alpha=clamp((lt - dur * 0.55) / 0.3), anchor="bottom")

    elif typ == "bignumber":
        m = re.match(r"^(\D*?)(\d[\d,]*(?:\.\d+)?)(.*)$", sc["value"])
        if m:
            pre, num, suf = m.groups()
            dec = len(num.split(".")[1]) if "." in num else 0
            v = float(num.replace(",", "")) * ease_out(lt / min(1.4, dur * 0.5))
            txt = f"{pre}{v:,.{dec}f}{suf}"
        else:
            txt = sc["value"]
        col = {"green": GREEN, "red": (235, 80, 70), "gold": GOLD, "white": WHITE}.get(sc.get("color", "gold"))
        if sc.get("icon"):
            paste(img, icon(sc["icon"], int(h * 0.17)), w / 2, h * 0.2, scale=ease_back(lt / 0.4))
        num_img = rich_block(txt, "head", h * (0.15 if ctx.short else 0.17), w * 0.94, col, max_lines=1)
        paste(img, num_img, w / 2, h * 0.46, scale=0.8 + 0.2 * ease_back(lt / 0.4))
        if sc.get("label"):
            lb = rich_block(sc["label"], "hand", h * 0.06, w * 0.85, WHITE, hl=GOLD)
            paste(img, lb, w / 2, h * 0.58, alpha=clamp((lt - 0.4) / 0.3), anchor="top")

    elif typ == "list":
        items = sc["items"]
        top = h * 0.07 + sc.get("_title_h", 0) + h * 0.03
        avail = h * (safe_bottom(ctx) - 0.03) - top
        step = min(avail / len(items), h * 0.17)
        reveal = max(0.5, dur * 0.8) / len(items)
        for i, it in enumerate(items):
            a = ease_back((lt - i * reveal) / 0.35)
            if a <= 0.01:
                continue
            y = top + step * i + step / 2
            off = (1 - clamp(a)) * w * 0.15
            ix = w * 0.1 + off
            ic = icon(sc.get("icon", "check"), int(step * 0.62)) if sc.get("icon") else None
            if ic:
                paste(img, ic, ix, y, alpha=clamp(a))
            else:
                r = step * 0.3
                d.ellipse((ix - r, y - r, ix + r, y + r), fill=GOLD, outline=INK, width=max(1, int(4 * u)))
                d.text((ix, y), str(i + 1), font=_font("Poppins-ExtraBold.ttf", r * 1.1), fill=NAVY, anchor="mm")
            tb = rich_block(it, "bold", min(h * 0.048, step * 0.36), w * 0.74, NAVY, hl=BLUE, align="left",
                            max_lines=2)
            paste(img, tb, w * 0.17 + off, y, alpha=clamp(a), anchor="left")

    elif typ == "compare":
        top = h * 0.07 + sc.get("_title_h", 0) + h * 0.03
        for j, (side, col) in enumerate(((sc["left"], RED), (sc["right"], GREEN))):
            col = {"green": GREEN, "red": RED, "blue": BLUE, "gold": GOLD, "navy": NAVY}.get(side.get("color"), col)
            a = ease_back((lt - j * 0.5) / 0.4)
            cx0 = w * (0.04 + 0.49 * j)
            cw = w * 0.43
            yy = top + (1 - clamp(a)) * h * 0.2
            card = Image.new("RGBA", (int(cw), int(h * (safe_bottom(ctx) - 0.02) - top)), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle((0, 0, card.width - 1, card.height - 1), radius=int(28 * u), fill=WHITE,
                                 outline=INK, width=max(2, int(5 * u)))
            cd.rounded_rectangle((0, 0, card.width - 1, h * 0.12), radius=int(28 * u), fill=col, outline=INK,
                                 width=max(2, int(5 * u)))
            hd = rich_block(side["title"], "head", h * 0.048, cw * 0.9, WHITE, max_lines=2)
            paste(card, hd, cw / 2, h * 0.06)
            pts = side.get("points", [])
            ytxt = h * 0.15
            for k_, pt in enumerate(pts):
                if lt < j * 0.5 + 0.4 + k_ * max(0.3, (dur * 0.7 - 1) / max(1, 2 * len(pts))):
                    break
                tb = rich_block("• " + pt, "bold", h * 0.045, cw * 0.88, INK, hl=col, align="left", max_lines=3)
                paste(card, tb, cw * 0.06, ytxt, anchor="topleft")
                ytxt += tb.height + h * 0.025
            paste(img, card, cx0, yy, alpha=clamp(a), anchor="topleft")
        vs = Image.new("RGBA", (int(h * 0.1), int(h * 0.1)), (0, 0, 0, 0))
        ImageDraw.Draw(vs).ellipse((0, 0, vs.width - 1, vs.height - 1), fill=NAVY, outline=GOLD, width=int(5 * u))
        ImageDraw.Draw(vs).text((vs.width / 2, vs.height / 2), "VS", font=_font("Poppins-ExtraBold.ttf", h * 0.038),
                                fill=WHITE, anchor="mm")
        paste(img, vs, w / 2, h * 0.55, scale=ease_back((lt - 0.9) / 0.3))

    elif typ == "formula":
        txt = sc["text"]
        shown = txt[:int(len(txt) * clamp(lt / max(0.8, dur * 0.5)))]
        n_all = len(txt.split("\n"))
        fs = min(h * 0.085, h * 0.4 / (n_all * 1.2))
        for i, ln in enumerate(shown.split("\n")):
            fb = rich_block(ln, "hand", fs, w * 0.82, (245, 245, 235), hl=(255, 214, 80), max_lines=1)
            paste(img, fb, w / 2, h * (0.07 + 0.46 * (i + 0.5) / n_all))
        if sc.get("note"):
            nt = rich_block(sc["note"], "hand", h * 0.05, w * 0.9, NAVY, hl=RED)
            paste(img, nt, w / 2, h * 0.62, alpha=clamp((lt - dur * 0.5) / 0.3), anchor="top")
        if sc.get("cast"):
            draw_cast(ctx, img, sc, lt, mouth_level, talking)

    elif typ == "quote":
        q = rich_block("“" + sc["text"] + "”", "hand", h * 0.07, w * 0.8, WHITE, hl=GOLD, max_lines=5)
        paste(img, q, w / 2, h * 0.42, alpha=clamp(lt / 0.5))
        if sc.get("by"):
            by = rich_block("— " + sc["by"], "bold", h * 0.04, w * 0.8, GOLD)
            paste(img, by, w / 2, h * 0.44 + q.height / 2, alpha=clamp((lt - 0.6) / 0.4), anchor="top")
    return img


@lru_cache(16)
def line_layer(w, h, pts, col, ybase, u):
    def fn(d, k):
        P = [(x * k, y * k) for x, y in pts]
        area = [(P[0][0], ybase * k)] + P + [(P[-1][0], ybase * k)]
        d.polygon(area, fill=col + (60,))
        d.line(P, fill=INK, width=int(16 * u * k), joint="curve")
        d.line(P, fill=col, width=int(9 * u * k), joint="curve")
    return supersample(w, h, fn)


# ---------------------------------------------------------------- overlays ---
@lru_cache(16)
def cta_sprite(u, line, subscribed=False):
    """Like / Share / Subscribe call-out."""
    fs = 34 * u
    btns = [("like", "LIKE", WHITE, INK), ("share", "SHARE", WHITE, INK),
            ("bell", "SUBSCRIBED" if subscribed else "SUBSCRIBE", (120, 120, 128) if subscribed else YT_RED, WHITE)]
    sizes = [int(text_w(t, "head", fs) + 110 * u) for _, t, _, _ in btns]
    bh = int(82 * u)
    gap = int(16 * u)
    head = rich_block(line, "hand", 40 * u, sum(sizes) + 2 * gap, WHITE, hl=GOLD, stroke=int(4 * u),
                      stroke_fill=NAVY, max_lines=2)
    W = max(sum(sizes) + 2 * gap, head.width) + int(48 * u)
    img = Image.new("RGBA", (W, head.height + bh + int(40 * u)), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, W - 1, img.height - 1), radius=int(30 * u), fill=NAVY + (225,),
                                          outline=GOLD, width=max(2, int(3 * u)))
    paste(img, head, W / 2, int(10 * u), anchor="top")
    x = (W - sum(sizes) - 2 * gap) / 2
    y = head.height + int(16 * u)
    for (ic, t, bg, fg), bw in zip(btns, sizes):
        b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b)
        bd.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=bh // 2, fill=bg, outline=INK, width=max(2, int(4 * u)))
        paste(b, icon(ic, int(bh * 0.56), WHITE if ic == "bell" else None), bh * 0.55, bh / 2)
        draw_text(bd, bh * 0.95, bh * 0.66, t, "head", fs, fg)
        img.alpha_composite(b, (int(x), int(y)))
        x += bw + gap
    return img


@lru_cache(4)
def watermark(u):
    lg, wm = logo(int(70 * u)), wordmark(int(30 * u))
    img = Image.new("RGBA", (int(lg.width + wm.width + 46 * u), int(lg.height + 12 * u)), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=img.height // 2,
                                          fill=NAVY + (215,))
    img.alpha_composite(wm, (int(20 * u), int((img.height - wm.height) / 2 + 4 * u)))
    img.alpha_composite(lg, (int(img.width - lg.width - 6 * u), int(6 * u)))
    return img


@lru_cache(4)
def cursor(u):
    def fn(d, k):
        s = 60 * u * k / 60
        d.polygon([(4 * s, 2 * s), (4 * s, 46 * s), (16 * s, 35 * s), (25 * s, 55 * s), (33 * s, 51 * s),
                   (24 * s, 32 * s), (40 * s, 32 * s)], fill=WHITE, outline=INK, width=int(3 * s))
    return supersample(int(60 * u), int(60 * u), fn)


@lru_cache(512)
def caption_sprite(ctx_short, u, words):
    if ctx_short:
        return rich_block(list(words), "head", 66 * u, 940 * u, WHITE, hl=(255, 204, 64), stroke=int(8 * u),
                          stroke_fill=INK, max_lines=2)
    return rich_block(list(words), "hand", 54 * u, 1560 * u, WHITE, hl=(255, 214, 80), stroke=int(6 * u),
                      stroke_fill=(20, 20, 24), max_lines=2)


# ---------------------------------------------------------------- timeline ---
def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def speech_profile(voice):
    """Per-frame mouth level (0-2) and silence midpoints for alignment."""
    hop = SR // FPS
    n = len(voice) // hop
    rms = np.sqrt(np.mean(voice[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    ref = np.percentile(rms, 95) or 1
    lvl = rms / ref
    mouth = np.where(lvl > 0.45, 2, np.where(lvl > 0.14, 1, 0))
    quiet = lvl < 0.08
    sil, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if j - i >= int(0.18 * FPS):
                sil.append(((i + j) / 2 / FPS, (j - i) / FPS))
            i = j
        else:
            i += 1
    voiced = np.nonzero(~quiet)[0]
    s0, s1 = (voiced[0] / FPS, voiced[-1] / FPS) if len(voiced) else (0, n / FPS)
    return mouth, sil, s0, s1


def word_weight(w):
    return len(w) + 1 + (6 if w[-1:] in ".?!" else 3 if w[-1:] in ",;:" else 0)


def chunk_words(words, short):
    max_w, max_c = (4, 24) if short else (10, 62)
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        n_chars = sum(len(x) + 1 for x, _ in cur)
        if len(cur) >= max_w or n_chars >= max_c or w[0][-1:] in ".?!,;:":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def build_timeline(ctx, voice_dur=None, prof=None):
    scenes = ctx.spec["scenes"]
    for sc in scenes:
        sc["_words"] = parse_rich(sc.get("line", ""))
    if voice_dur is not None:
        _, sil, s0, s1 = prof
        weights = [max(1, sum(word_weight(w) for w, _ in sc["_words"])) for sc in scenes]
        tot = sum(weights)
        bounds, acc = [0.0], 0
        for wgt in weights[:-1]:
            acc += wgt
            b = s0 + (s1 - s0) * acc / tot
            near = [m for m, ln in sil if abs(m - b) < 0.9]
            bounds.append(min(near, key=lambda m: abs(m - b)) if near else b)
        bounds.append(voice_dur)
        for i, sc in enumerate(scenes):
            if "at" in sc:
                bounds[i] = float(sc["at"])
        for i, sc in enumerate(scenes):
            sc["_t0"], sc["_dur"] = bounds[i], max(0.4, bounds[i + 1] - bounds[i])
        total = voice_dur
    else:
        t = 0.0
        for sc in scenes:
            dur = sc.get("dur") or (len(sc["_words"]) / 2.6 + 0.6)
            sc["_t0"], sc["_dur"] = t, dur
            t += dur
        total = t
    # captions: spread over the voiced part of each scene
    caps = []
    for sc in scenes:
        if not sc["_words"] or sc.get("captions") is False:
            continue
        a, b = sc["_t0"], sc["_t0"] + sc["_dur"]
        if voice_dur is not None:
            a, b = max(a, prof[2]) if sc is scenes[0] else a, min(b, prof[3] + 0.3) if sc is scenes[-1] else b
        chunks = chunk_words(sc["_words"], ctx.short)
        wts = [sum(word_weight(w) for w, _ in c) for c in chunks]
        tt = a
        for c, wgt in zip(chunks, wts):
            dt = (b - a) * wgt / sum(wts)
            caps.append((tt, tt + dt, tuple(c)))
            tt += dt
    return total, caps


def cta_schedule(ctx, total):
    sp = ctx.spec
    if "cta_times" in sp:
        times = sp["cta_times"]
    elif ctx.short:
        times = [max(4.0, total * 0.3)] + ([total * 0.7] if total > 40 else [])
    else:
        times = [min(18.0, total * 0.15), total * 0.42, total * 0.75]
    lines = sp.get("cta_lines") or ["Found this useful? *Like* & *Subscribe*!",
                                    "*Share* this with a friend who needs it",
                                    "*Subscribe* to COMandFIN for daily finance lessons"]
    return [(t, lines[i % len(lines)]) for i, t in enumerate(times) if t < total - 3]


# ------------------------------------------------------------------ frames ---
def intro_frame(ctx, t):
    W, H, u = ctx.W, ctx.H, ctx.u
    img = background("brand", W, H).copy()
    lg = logo(int(260 * u))
    paste(img, lg, W / 2, H * 0.4, scale=ease_back(t / 0.5))
    wm = wordmark(int(96 * u))
    paste(img, wm, W / 2, H * 0.62, alpha=clamp((t - 0.4) / 0.3), anchor="top")
    tg = rich_block(TAGLINE, "hand", 54 * u, W, GOLD)
    paste(img, tg, W / 2, H * 0.62 + wm.height + 10 * u, alpha=clamp((t - 0.8) / 0.3), anchor="top")
    if t > ctx.intro - 0.25:
        img = Image.blend(img, Image.new("RGBA", img.size, NAVY + (255,)), clamp((t - ctx.intro + 0.25) / 0.25))
    return img


def outro_frame(ctx, t):
    W, H, u = ctx.W, ctx.H, ctx.u
    img = background("brand", W, H).copy()
    cx = W / 2 if ctx.short else W * 0.3
    ly = H * (0.17 if ctx.short else 0.15)
    paste(img, logo(int(200 * u)), cx, ly, scale=ease_back(t / 0.4))
    wm = wordmark(int(78 * u))
    paste(img, wm, cx, ly + 108 * u, alpha=clamp((t - 0.2) / 0.3), anchor="top")
    big = 1.35 if ctx.short else 1.25
    rows = [("like", "LIKE this video", WHITE), ("share", "SHARE with your friends", WHITE),
            ("bell", "SUBSCRIBE + hit the bell", YT_RED)]
    y = H * (0.34 if ctx.short else 0.385)
    for i, (ic, txt, col) in enumerate(rows):
        a = ease_back((t - 0.4 - i * 0.25) / 0.35)
        if a <= 0.01:
            continue
        row = Image.new("RGBA", (int(620 * u * big), int(96 * u * big)), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row)
        rd.rounded_rectangle((0, 0, row.width - 1, row.height - 1), radius=row.height // 2, fill=col, outline=INK,
                             width=int(4 * u))
        wig = math.sin(t * 9) * 0.08 if ic == "bell" and t > 1.6 else 0
        ics = icon(ic, int(row.height * 0.6), WHITE if ic == "bell" else None).rotate(wig * 180, resample=Image.BICUBIC)
        paste(row, ics, row.height * 0.6, row.height / 2)
        draw_text(rd, row.height * 1.1, row.height * 0.64, txt, "head", 36 * u * big, WHITE if col == YT_RED else NAVY)
        paste(img, row, cx, y + row.height / 2, scale=clamp(a, 0, 1.2))
        y += row.height + 22 * u
    msg = ctx.spec.get("end_message", "Share this with someone who is learning *finance*!")
    paste(img, rich_block(msg, "hand", 50 * u, (980 if ctx.short else 1000) * u, WHITE, hl=GOLD, max_lines=2), cx,
          y + 6 * u, alpha=clamp((t - 1.4) / 0.4), anchor="top")
    paste(img, rich_block(WEBSITE, "bold", 40 * u, W, GOLD), cx, H * (0.87 if ctx.short else 0.95),
          alpha=clamp((t - 1.0) / 0.4))
    if ctx.short:
        paste(img, character("prof", "happy", "wave", 0, (t % 3) < 0.12, int(360 * u)), W / 2, H * 0.84,
              anchor="bottom")
    else:
        d = ImageDraw.Draw(img)
        for i, lab in enumerate(("Watch Next", "Subscribe")):
            x0, y0 = W * 0.6, H * (0.16 + i * 0.4)
            if i == 0:
                d.rounded_rectangle((x0, y0, x0 + W * 0.33, y0 + H * 0.33), radius=int(20 * u), outline=GOLD,
                                    width=int(4 * u))
                paste(img, rich_block(lab, "bold", 40 * u, W, (180, 196, 220)), x0 + W * 0.165, y0 + H * 0.165)
            else:
                r = H * 0.14
                d.ellipse((x0 + W * 0.165 - r, y0 + H * 0.1 - r, x0 + W * 0.165 + r, y0 + H * 0.1 + r), outline=GOLD,
                          width=int(4 * u))
                paste(img, rich_block(lab, "bold", 34 * u, W, (180, 196, 220)), x0 + W * 0.165, y0 + H * 0.1)
    return img


class Renderer:
    def __init__(self, ctx, total, caps, ctas, mouth):
        self.ctx, self.total, self.caps, self.ctas, self.mouth = ctx, total, caps, ctas, mouth
        self.static = {}

    def frame(self, i):
        ctx = self.ctx
        t = i / FPS
        if t < ctx.intro:
            return intro_frame(ctx, t)
        tv = t - ctx.intro
        if tv >= self.total:
            return outro_frame(ctx, tv - self.total)
        scenes = ctx.spec["scenes"]
        si = max(k for k, sc in enumerate(scenes) if sc["_t0"] <= tv + 1e-6) if tv >= scenes[0]["_t0"] else 0
        sc = scenes[si]
        lt = tv - sc["_t0"]
        if si not in self.static:
            self.static = {si: scene_static(ctx, sc)}
        cap = next((c for c in self.caps if c[0] <= tv < c[1]), None)
        if self.mouth is not None:
            fi = int(tv * FPS)
            m = int(self.mouth[fi]) if 0 <= fi < len(self.mouth) else 0
        else:
            m = [0, 1, 2, 1][int(tv * 12) % 4] if cap else 0
        stage = render_scene(ctx, sc, self.static[si], lt, m, cap is not None or self.mouth is not None)
        if lt < 0.18 and si > 0:
            stage = Image.blend(Image.new("RGBA", stage.size, WHITE + (255,)), stage, clamp(lt / 0.18))
        sx, sy, sw, sh = ctx.stage
        u = ctx.u
        if ctx.short:
            img = background("brand", ctx.W, ctx.H).copy()
            img.alpha_composite(stage, (sx, sy))
            d = ImageDraw.Draw(img)
            paste(img, logo(int(118 * u)), 92 * u, 150 * u)
            paste(img, wordmark(int(56 * u)), 168 * u, 128 * u, anchor="left")
            series = ctx.spec.get("series", "Finance Explained Simply")
            draw_text(d, 172 * u, 205 * u, series, "med", 30 * u, GOLD)
            d.rectangle((sx, sy + sh - 8 * u, sx + sw * clamp(tv / self.total), sy + sh), fill=GOLD)
            if cap:
                cs = caption_sprite(True, u, cap[2])
                pop = 0.86 + 0.14 * ease_back((tv - cap[0]) / 0.14)
                paste(img, cs, ctx.W / 2, sy + sh + 120 * u, scale=pop)
            paste(img, rich_block(WEBSITE, "med", 28 * u, ctx.W, (150, 170, 200)), ctx.W / 2, ctx.H - 190 * u)
        else:
            img = stage
            paste(img, watermark(u), ctx.W - 24 * u, 24 * u, alpha=0.92, anchor="topright")
            if cap:
                paste(img, caption_sprite(False, u, cap[2]), ctx.W / 2, ctx.H - 40 * u, anchor="bottom")
        for t0, line in self.ctas:
            ct = tv - t0
            if 0 <= ct < 3.6:
                sub = ct > 1.75
                spr = cta_sprite(u, line, sub)
                slide = ease_back(ct / 0.4) if ct < 3.2 else 1 - ease_out((ct - 3.2) / 0.4)
                if ctx.short:
                    x, y = ctx.W / 2, (sy - spr.height) / 2 - (1 - slide) * (spr.height + 120 * u)
                    if slide > 0.05:
                        ImageDraw.Draw(img).rectangle((0, 0, ctx.W, sy - 2), fill=NAVY)
                    paste(img, spr, x, y, anchor="top")
                    bx, by = x + spr.width / 2 - 150 * u, y + spr.height - 40 * u
                else:
                    x, y = ctx.W - 40 * u + (1 - slide) * (spr.width + 60 * u), ctx.H * 0.66
                    paste(img, spr, x, y, anchor="right")
                    bx, by = x - 150 * u, y + spr.height / 2 - 40 * u
                if 0.9 < ct < 2.6:
                    k = ease_out((ct - 0.9) / 0.7)
                    press = 0.85 if 1.6 < ct < 1.8 else 1.0
                    paste(img, cursor(u), bx + (1 - k) * 220 * u, by + (1 - k) * 160 * u, scale=press,
                          anchor="topleft")
        return img


def render_range(args):
    ctx_args, timeline, a, b, path = args
    ctx = Ctx(*ctx_args)
    total, caps, ctas, mouth, sched = timeline
    for sc, (t0, dur) in zip(ctx.spec["scenes"], sched):
        sc["_t0"], sc["_dur"] = t0, dur
    r = Renderer(ctx, total, caps, ctas, mouth)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                            f"{ctx.W}x{ctx.H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset",
                            "veryfast" if ctx.k < 1 else "medium", "-crf", "20", "-pix_fmt", "yuv420p", path],
                           stdin=subprocess.PIPE)
    for i in range(a, b):
        enc.stdin.write(r.frame(i).convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    return path


# ------------------------------------------------------------------- audio ---
def tone(freqs, dur, vol=0.25, decay=8.0):
    t = np.arange(int(SR * dur)) / SR
    return (sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs) * np.exp(-decay * t) * vol).astype(np.float32)


def build_audio(ctx, voice, total, ctas, out):
    n = int((ctx.intro + total + ctx.outro) * SR)
    mix = np.zeros(n, np.float32)
    v0 = int(ctx.intro * SR)
    if voice is not None:
        mix[v0:v0 + len(voice)] += voice[:n - v0]
    pop, ding = tone([660, 990], 0.12, 0.18, 30), tone([1320, 1760], 0.5, 0.14, 7)
    for t0, _ in ctas:
        for at, s in ((t0, pop), (t0 + 1.7, ding)):
            k = int((ctx.intro + at) * SR)
            mix[k:k + len(s)] += s[:max(0, n - k)]
    if ctx.intro:
        mix[:len(ding)] += ding[:n] * 1.4
    ko = int((ctx.intro + total) * SR)
    mix[ko:ko + len(ding)] += ding[:max(0, n - ko)]
    music = ctx.spec.get("music")
    if music:
        m = load_audio(music)
        reps = int(np.ceil(n / len(m)))
        m = np.tile(m, reps)[:n] * float(ctx.spec.get("music_volume", 0.08))
        fade = int(SR * 2)
        m[-fade:] *= np.linspace(1, 0, fade)
        mix += m
    raw = out + ".f32"
    mix.tofile(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", raw, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "2", "-c:a", "aac", "-b:a", "192k", out],
                   check=True)
    os.remove(raw)


# --------------------------------------------------------------- thumbnail ---
def thumbnail(spec, fmt, path, size=(1280, 720)):
    th = spec.get("thumbnail", {})
    W, H = size
    u = min(W, H) / 720
    vertical = H > W
    img = radial(W, H, (30, 78, 140), (6, 16, 34), cx=0.7, cy=0.45).copy()
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(W * 0.66, 0), (W * 0.73, 0), (W * 0.6, H), (W * 0.53, H)], fill=(201, 154, 46, 70)) if not vertical \
        else d.polygon([(0, H * 0.5), (W, H * 0.4), (W, H * 0.46), (0, H * 0.56)], fill=(201, 154, 46, 70))
    who, mood, pose = th.get("who", "prof"), th.get("mood", "surprised"), th.get("pose", "point")
    if vertical:
        ch = character(who, mood, pose, 0, False, int(H * 0.52))
        paste(img, ch, W * 0.5, H * 1.02, anchor="bottom")
        if th.get("icon"):
            paste(img, icon(th["icon"], int(W * 0.3)), W * 0.8, H * 0.58)
        txt = rich_block(th.get("text", spec.get("title", "")).upper(), "head", W * 0.13, W * 0.92, WHITE,
                         hl=(255, 204, 64), stroke=int(10 * u), max_lines=4, lh=1.05)
        paste(img, txt, W / 2, H * 0.19, anchor="top")
        tag_y = H * 0.145
        paste(img, logo(int(W * 0.14)), W * 0.12, H * 0.05)
        paste(img, wordmark(int(W * 0.06)), W * 0.22, H * 0.05, anchor="left")
    else:
        ch = character(who, mood, pose, 0, False, int(H * 1.0))
        paste(img, ch, W * 0.8, H * 1.12, anchor="bottom")
        if th.get("icon"):
            paste(img, icon(th["icon"], int(H * 0.3)), W * 0.6, H * 0.2)
        txt = rich_block(th.get("text", spec.get("title", "")).upper(), "head", H * 0.15, W * 0.55, WHITE,
                         hl=(255, 204, 64), stroke=int(9 * u), max_lines=3, lh=1.05, align="left")
        paste(img, txt, W * 0.04, H * 0.53, anchor="left")
        tag_y = H * 0.12
        paste(img, logo(int(H * 0.15)), W * 0.06, H * 0.89)
        paste(img, wordmark(int(H * 0.06)), W * 0.12, H * 0.89, anchor="left")
    if th.get("tag"):
        tg = rich_block(th["tag"].upper(), "head", H * (0.025 if vertical else 0.05), W, WHITE)
        pill = Image.new("RGBA", (tg.width + int(30 * u), tg.height + int(8 * u)), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), radius=int(12 * u),
                                               fill=YT_RED, outline=WHITE, width=int(3 * u))
        pill.alpha_composite(tg, (int(15 * u), int(4 * u)))
        if vertical:
            paste(img, pill, W / 2, tag_y)
        else:
            paste(img, pill, W * 0.04, tag_y, anchor="left")
    img.convert("RGB").save(path, quality=92)


def publish_kit(spec, fmt, path, video_len):
    m = spec.get("meta", {})
    lines = [f"# Publish Kit — {spec.get('title', '')}", "",
             f"**Format:** {'YouTube Short / Instagram Reel (9:16)' if fmt == 'short' else 'YouTube long-form (16:9)'}"
             f"  |  **Length:** {int(video_len // 60)}:{int(video_len % 60):02d}", ""]
    for key, label in (("titles", "Title options"), ("description", "YouTube description"),
                       ("caption", "Instagram / LinkedIn caption"), ("hashtags", "Hashtags"),
                       ("tags", "YouTube tags"), ("pinned_comment", "Pinned comment"), ("chapters", "Chapters")):
        v = m.get(key)
        if not v:
            continue
        lines.append(f"## {label}")
        if isinstance(v, list):
            lines += ([" ".join(v)] if key == "hashtags" else [", ".join(v)] if key == "tags"
                      else [f"- {x}" for x in v])
        else:
            lines.append(v)
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ------------------------------------------------------------------- main ---
def render(spec_path, out_dir, draft=False, jobs=None):
    spec = json.load(open(spec_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(spec_path))
    fmt = spec.get("format", "short")
    ctx = Ctx(spec, fmt, draft)
    os.makedirs(out_dir, exist_ok=True)
    name = spec.get("slug") or re.sub(r"[^a-z0-9]+", "-", spec.get("title", "video").lower()).strip("-")
    voice = mouth = None
    if spec.get("audio"):
        ap = spec["audio"] if os.path.isabs(spec["audio"]) else os.path.join(base, spec["audio"])
        voice = load_audio(ap)
        prof = speech_profile(voice)
        mouth = prof[0]
        total, caps = build_timeline(ctx, len(voice) / SR, prof)
    else:
        total, caps = build_timeline(ctx)
    if spec.get("music") and not os.path.isabs(spec["music"]):
        spec["music"] = os.path.join(base, spec["music"])
    ctas = cta_schedule(ctx, total)
    n = int((ctx.intro + total + ctx.outro) * FPS)
    jobs = jobs or max(1, os.cpu_count() or 1)
    tmp = tempfile.mkdtemp(prefix="studio_")
    sched = [(sc["_t0"], sc["_dur"]) for sc in spec["scenes"]]
    timeline = (total, caps, ctas, mouth, sched)
    step = math.ceil(n / jobs)
    tasks = [((spec, fmt, draft), timeline, a, min(n, a + step), os.path.join(tmp, f"seg{a:06d}.mp4"))
             for a in range(0, n, step)]
    print(f"[studio] {fmt} | voice {total:.1f}s | total {n / FPS:.1f}s | {n} frames | {len(caps)} captions | "
          f"CTAs at {[round(t, 1) for t, _ in ctas]}", flush=True)
    for sc in spec["scenes"]:
        print(f"   {sc['_t0']:6.2f}s +{sc['_dur']:5.2f}s  {sc['type']:<10} {sc.get('line', '')[:60]}")
    with mp.get_context("fork").Pool(len(tasks)) as pool:
        segs = pool.map(render_range, tasks)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    audio = os.path.join(tmp, "audio.m4a")
    build_audio(ctx, voice, total, ctas, audio)
    out = os.path.join(out_dir, f"{name}{'_draft' if draft else ''}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio, "-c:v",
                    "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    make_extras(spec, fmt, out_dir, name, n / FPS)
    print(f"[studio] wrote {out}")
    return out


def make_extras(spec, fmt, out_dir, name, length):
    thumbnail(spec, fmt, os.path.join(out_dir, f"{name}_thumbnail.jpg"))
    if fmt == "short":
        thumbnail(spec, fmt, os.path.join(out_dir, f"{name}_cover_9x16.jpg"), size=(1080, 1920))
    publish_kit(spec, fmt, os.path.join(out_dir, f"{name}_publish_kit.md"), length)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "thumb"])
    ap.add_argument("spec")
    ap.add_argument("--out", default="out")
    ap.add_argument("--draft", action="store_true", help="half resolution, faster")
    ap.add_argument("--jobs", type=int)
    a = ap.parse_args()
    if a.cmd == "render":
        render(a.spec, a.out, a.draft, a.jobs)
    else:
        s = json.load(open(a.spec, encoding="utf-8"))
        nm = s.get("slug", "video")
        make_extras(s, s.get("format", "short"), a.out, nm, 0)
