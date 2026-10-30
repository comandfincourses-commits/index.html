"""2D comic-style cartoon engine: round-head characters with thick outlines, speech bubbles, simple sets."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 24
HERE = os.path.dirname(os.path.abspath(__file__))
INK = (28, 26, 30)
SKIN = (243, 211, 176)
WHITEHEAD = (247, 247, 245)
_fc = {}


def hand(size):
    k = ("hand", size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(HERE, "fonts/Caveat.woff"), int(size * 1.15))
    return _fc[k]


def bold(size):
    k = ("bold", size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Black.otf", size)
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ell(d, cx, cy, rx, ry, fill=None, ow=0, oc=INK):
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=oc if ow else None, width=int(ow))


def rr(d, box, r, fill=None, ow=0, oc=INK):
    d.rounded_rectangle(box, radius=int(r), fill=fill, outline=oc if ow else None, width=int(ow))


def poly(d, pts, fill=None, ow=0, oc=INK):
    d.polygon(pts, fill=fill, outline=oc if ow else None, width=int(ow) if ow else 1)


def shade(c, k):
    return tuple(int(clamp(v * k, 0, 255)) for v in c[:3])


# ------------------------------------------------------------------ characters
C = {
    "boy6": dict(skin=SKIN, hair=(150, 100, 55), style="side", top=(250, 250, 248), braces=(110, 70, 40), ears=1.25, scale=0.82),
    "boy11": dict(skin=SKIN, hair=(150, 100, 55), style="side", top=(250, 250, 248), vest=(35, 50, 100), ears=1.25, scale=0.9),
    "teen14": dict(skin=SKIN, hair=(130, 88, 50), style="side", top=(185, 60, 45), plaid=(120, 35, 25), ears=1.2, scale=0.96),
    "young20": dict(skin=SKIN, hair=(105, 70, 40), style="slick", top=(130, 132, 138), shirt=True, tie=(30, 30, 45), ears=1.15, scale=1.0),
    "father": dict(skin=SKIN, hair=(55, 42, 32), style="receding", top=(95, 98, 108), shirt=True, tie=(40, 40, 55), glasses=True, ears=1.0, scale=1.0),
    "mother": dict(skin=SKIN, hair=(60, 42, 32), style="bob", top=(95, 135, 205), dots=True, collar=True, ears=0.9, scale=0.95),
    "sister": dict(skin=SKIN, hair=(75, 52, 35), style="braids", top=(215, 190, 145), collar=True, ears=0.9, scale=0.9),
    "grandpa": dict(skin=(245, 205, 172), hair=(238, 238, 238), style="white", top=(250, 250, 248), apron=True, glasses=True, wrinkles=True, ears=1.05, scale=1.0),
    "friend": dict(skin=SKIN, hair=(45, 32, 25), style="curly", top=(250, 250, 248), stripes=(40, 60, 115), ears=1.0, scale=0.96),
    "clerk": dict(skin=WHITEHEAD, hair=None, style="none", top=(40, 42, 50), shirt=True, tie=(150, 30, 30), ears=0.0, scale=1.0),
    "suit": dict(skin=WHITEHEAD, hair=(60, 45, 35), style="short", top=(40, 42, 50), shirt=True, tie=(40, 90, 60), ears=0.0, scale=1.0),
    "lady": dict(skin=WHITEHEAD, hair=(120, 80, 50), style="bun", top=(160, 90, 110), collar=True, ears=0.0, scale=0.95),
    "prof": dict(skin=WHITEHEAD, hair=(200, 200, 200), style="white", top=(120, 90, 60), shirt=True, tie=(90, 30, 30), glasses=True, ears=0.0, scale=1.0),
    "oldwb": dict(skin=SKIN, hair=(240, 240, 240), style="oldwhite", top=(45, 50, 65), shirt=True, tie=(150, 35, 40), bigglasses=True, wrinkles=True, ears=1.1, scale=1.0),
}


def _shaded_disc(img, cx, cy, rx, ry, col, ow, shade_k=0.82, off=0.2):
    """Filled ellipse with a darker crescent on the right, then an ink outline (comic shading)."""
    pad = int(ow) + 4
    w_, h_ = int(rx * 2 + pad * 2), int(ry * 2 + pad * 2)
    lay = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    box = (pad, pad, pad + rx * 2, pad + ry * 2)
    ld.ellipse(box, fill=shade(col, shade_k) + (255,))
    m = Image.new("L", (w_, h_), 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    inner = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    ImageDraw.Draw(inner).ellipse((pad - rx * off, pad - ry * 0.06, pad + rx * 2 - rx * off * 1.2, pad + ry * 2 - ry * 0.02), fill=tuple(col[:3]) + (255,))
    lay.alpha_composite(Image.composite(inner, Image.new("RGBA", (w_, h_), (0, 0, 0, 0)), m))
    ImageDraw.Draw(lay).ellipse(box, outline=INK, width=int(ow))
    img.alpha_composite(lay, (int(cx - rx - pad), int(cy - ry - pad)))


def _hair(d, x, y, R, st, hc, ow, t):
    hl = shade(hc, 1.35)
    if st in ("side", "messy"):
        for a, b, rx_, ry_ in ((-0.62, -0.62, 0.42, 0.36), (-0.15, -0.86, 0.46, 0.3), (0.38, -0.78, 0.44, 0.32), (0.78, -0.42, 0.3, 0.34)):
            ell(d, x + a * R, y + b * R, rx_ * R, ry_ * R, hc, ow * 0.9)
        d.chord((x - R * 1.02, y - R * 1.0, x + R * 1.02, y + R * 0.9), 185, 355, fill=hc)
        for a, b, rx_, ry_ in ((-0.62, -0.62, 0.42, 0.36), (-0.15, -0.86, 0.46, 0.3), (0.38, -0.78, 0.44, 0.32), (0.78, -0.42, 0.3, 0.34)):
            ell(d, x + a * R, y + b * R, rx_ * R - ow, ry_ * R - ow, hc)
        d.arc((x - R * 1.02, y - R * 1.0, x + R * 1.02, y + R * 0.9), 185, 205, fill=INK, width=int(ow))
        d.arc((x - R * 1.02, y - R * 1.0, x + R * 1.02, y + R * 0.9), 335, 355, fill=INK, width=int(ow))
        for fx in (-0.55, -0.15, 0.25):
            poly(d, [(x + (fx - 0.22) * R, y - R * 0.45), (x + (fx + 0.22) * R, y - R * 0.45), (x + (fx + 0.05) * R, y - R * 0.22)], hc)
        d.arc((x - R * 0.7, y - R * 1.0, x + R * 0.1, y - R * 0.55), 200, 290, fill=hl, width=int(ow * 1.1))
    elif st == "slick":
        d.chord((x - R * 1.02, y - R * 1.06, x + R * 1.02, y + R * 0.75), 185, 355, fill=hc, outline=INK, width=int(ow))
        poly(d, [(x - R * 0.98, y - R * 0.2), (x - R * 0.3, y - R * 0.62), (x + R * 0.98, y - R * 0.32), (x + R * 0.99, y - R * 0.12)], hc)
        for k in range(3):
            d.arc((x - R * (0.8 - k * 0.25), y - R * 1.0, x + R * (0.6 + k * 0.1), y - R * 0.3), 200, 300, fill=hl, width=int(ow * 0.7))
    elif st == "receding":
        d.chord((x - R * 1.02, y - R * 1.02, x + R * 1.02, y + R * 0.6), 205, 335, fill=hc, outline=INK, width=int(ow))
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.9, y - R * 0.28, R * 0.18, R * 0.36, hc, ow * 0.7)
    elif st in ("white", "oldwhite"):
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.9, y - R * 0.22, R * 0.22, R * 0.36, hc, ow * 0.7)
        if st == "oldwhite":
            d.chord((x - R * 0.96, y - R * 1.03, x + R * 0.96, y + R * 0.1), 205, 335, fill=hc, outline=INK, width=int(ow * 0.8))
    elif st == "bob":
        d.chord((x - R * 1.08, y - R * 1.1, x + R * 1.08, y + R * 0.7), 180, 360, fill=hc, outline=INK, width=int(ow))
        for k in range(3):
            d.arc((x - R * 0.85 + k * R * 0.55, y - R * 0.95, x - R * 0.3 + k * R * 0.55, y - R * 0.5), 200, 340, fill=hl, width=int(ow * 0.7))
    elif st == "braids":
        d.chord((x - R * 1.04, y - R * 1.07, x + R * 1.04, y + R * 0.62), 180, 360, fill=hc, outline=INK, width=int(ow))
        d.line([(x, y - R * 1.02), (x, y - R * 0.48)], fill=shade(hc, 0.6), width=int(ow * 0.8))
    elif st == "curly":
        for k in range(11):
            a = math.pi * (0.92 + k * 0.116)
            ell(d, x + math.cos(a) * R * 0.86, y + math.sin(a) * R * 0.86, R * 0.28, R * 0.28, hc, ow * 0.6)
    elif st == "bun":
        ell(d, x, y - R * 1.02, R * 0.32, R * 0.28, hc, ow * 0.8)
        d.chord((x - R * 1.03, y - R * 1.05, x + R * 1.03, y + R * 0.5), 180, 360, fill=hc, outline=INK, width=int(ow))
    elif st == "short":
        d.chord((x - R * 1.02, y - R * 1.04, x + R * 1.02, y + R * 0.6), 190, 350, fill=hc, outline=INK, width=int(ow))


def bust(img, key, x, y, R, t=0.0, expr="neutral", talk=False, look=0.0, arms="down", seed=0, hold=None, back=False):
    """Comic-style character from the chest up: big shaded head, dot eyes, small tapered body.
    (x, y) = head centre, R = head radius."""
    c = C[key]
    d = ImageDraw.Draw(img, "RGBA")
    R = R * c["scale"]
    ow = max(3, R * 0.05)
    y = y + math.sin(t * 2.0 + seed) * R * 0.012
    top = c["top"]
    # ---- body: narrow egg, shaded
    bt = y + R * 0.72
    _shaded_disc(img, x, bt + R * 1.25, R * 0.86, R * 1.25, top, ow, 0.78, 0.25)
    pat = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(pat, "RGBA")
    if c.get("plaid"):
        for k in range(-2, 3):
            d.line([(x + k * R * 0.28, bt + R * 0.2), (x + k * R * 0.28, bt + R * 2.6)], fill=c["plaid"] + (140,), width=int(R * 0.06))
        for k in range(1, 6):
            d.line([(x - R * 0.7, bt + k * R * 0.38), (x + R * 0.7, bt + k * R * 0.38)], fill=c["plaid"] + (140,), width=int(R * 0.06))
    if c.get("stripes"):
        for k in range(1, 7):
            d.line([(x - R * 0.72, bt + k * R * 0.34), (x + R * 0.72, bt + k * R * 0.34)], fill=c["stripes"], width=int(R * 0.1))
    if c.get("dots"):
        rnd = random.Random(7)
        for _ in range(14):
            ell(d, x + rnd.uniform(-R * 0.55, R * 0.55), bt + rnd.uniform(R * 0.3, R * 2.4), R * 0.045, R * 0.045, (245, 245, 255))
    if not back:
        if c.get("shirt") or c.get("vest"):
            poly(d, [(x - R * 0.3, bt + R * 0.05), (x + R * 0.3, bt + R * 0.05), (x, bt + R * 0.95)], (250, 250, 248), ow * 0.6)
        if c.get("vest"):
            poly(d, [(x - R * 0.3, bt + R * 0.05), (x, bt + R * 0.95), (x - R * 0.12, bt + R * 2.8), (x - R * 0.7, bt + R * 2.5), (x - R * 0.72, bt + R * 0.6)], c["vest"])
            poly(d, [(x + R * 0.3, bt + R * 0.05), (x, bt + R * 0.95), (x + R * 0.12, bt + R * 2.8), (x + R * 0.7, bt + R * 2.5), (x + R * 0.72, bt + R * 0.6)], shade(c["vest"], 0.8))
        if c.get("tie"):
            poly(d, [(x - R * 0.08, bt + R * 0.12), (x + R * 0.08, bt + R * 0.12), (x + R * 0.11, bt + R * 0.85), (x, bt + R * 1.0), (x - R * 0.11, bt + R * 0.85)], c["tie"], ow * 0.4)
        if c.get("braces"):
            for sx in (-1, 1):
                d.line([(x + sx * R * 0.35, bt + R * 0.1), (x + sx * R * 0.42, bt + R * 2.7)], fill=c["braces"], width=int(R * 0.11))
        if c.get("apron"):
            rr(d, (x - R * 0.52, bt + R * 0.55, x + R * 0.52, bt + R * 2.9), R * 0.1, (255, 255, 255), ow * 0.6)
        if c.get("collar") or key in ("boy6", "boy11", "friend", "grandpa", "teen14"):
            for sx in (-1, 1):
                poly(d, [(x + sx * R * 0.03, bt + R * 0.25), (x + sx * R * 0.38, bt + R * 0.02), (x + sx * R * 0.42, bt + R * 0.3)], (255, 255, 255), ow * 0.5)
    # clip all clothing details to the body shape
    bm = Image.new("L", img.size, 0)
    ImageDraw.Draw(bm).ellipse((x - R * 0.86 + ow, bt + ow, x + R * 0.86 - ow, bt + R * 2.5 - ow), fill=255)
    img.alpha_composite(Image.composite(pat, Image.new("RGBA", img.size, (0, 0, 0, 0)), bm))
    d = ImageDraw.Draw(img, "RGBA")
    # ---- arms (thin ink strokes with small hands, like the reference)
    def arm(sx, hx_, hy_):
        sx0, sy0 = x + sx * R * 0.62, bt + R * 0.55
        d.line([(sx0, sy0), (hx_, hy_)], fill=INK, width=int(R * 0.09))
        ell(d, hx_, hy_, R * 0.1, R * 0.1, c["skin"], ow * 0.6)
    if arms == "hold":
        arm(-1, x - R * 0.35, bt + R * 1.35); arm(1, x + R * 0.35, bt + R * 1.35)
    elif arms == "raise":
        arm(1, x + R * 1.05, y - R * 0.2 + math.sin(t * 6) * R * 0.08)
    elif arms == "point":
        arm(1, x + R * 1.5, bt + R * 0.5)
    elif arms == "cross":
        d.line([(x - R * 0.6, bt + R * 1.2), (x + R * 0.6, bt + R * 1.45)], fill=INK, width=int(R * 0.1))
        d.line([(x + R * 0.6, bt + R * 1.2), (x - R * 0.6, bt + R * 1.45)], fill=INK, width=int(R * 0.1))
    if hold:
        hold(d, x, bt + R * 1.35, R)
    # ---- head
    st, hc = c["style"], c["hair"]
    if st == "bob":
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.88, y + R * 0.2, R * 0.34, R * 0.55, hc, ow)
    if st == "braids":
        for sx in (-1, 1):
            for k in range(4):
                ell(d, x + sx * R * 0.9, y + R * (0.55 + k * 0.4), R * 0.18, R * 0.21, hc, ow * 0.6)
    skin = c["skin"]
    _shaded_disc(img, x, y, R, R, skin, ow, 0.84 if skin == WHITEHEAD else 0.86, 0.18)
    d = ImageDraw.Draw(img, "RGBA")
    if back:
        if hc:
            _shaded_disc(img, x, y - R * 0.12, R * 0.99, R * 0.9, hc, ow, 0.8, 0.2)
        return
    if hc:
        _hair(d, x, y, R, st, hc, ow, t)
    # ---- face: dot eyes, thick brows, tiny mouth
    blink = ((t + seed * 0.7) % 3.4) < 0.11
    lx = look * R * 0.14
    ey = y + R * 0.05
    ex = [x - R * 0.27 + lx, x + R * 0.27 + lx]
    big = expr == "shock"
    for k, exx in enumerate(ex):
        if blink and not big:
            d.line([(exx - R * 0.07, ey), (exx + R * 0.07, ey)], fill=INK, width=int(ow * 0.9))
        else:
            ell(d, exx, ey, R * (0.075 if big else 0.055), R * (0.12 if big else 0.1), INK)
        inner_sign = 1 if k == 0 else -1
        by = ey - R * (0.3 if big else 0.24)
        if expr == "angry":
            p1, p2 = (exx - inner_sign * R * 0.12, by - R * 0.04), (exx + inner_sign * R * 0.1, by + R * 0.06)
        elif expr in ("sad", "worried"):
            p1, p2 = (exx - inner_sign * R * 0.12, by + R * 0.04), (exx + inner_sign * R * 0.1, by - R * 0.05)
        else:
            p1, p2 = (exx - R * 0.11, by), (exx + R * 0.11, by - R * 0.01)
        d.line([p1, p2], fill=INK, width=int(R * 0.06))
    if c.get("glasses") or c.get("bigglasses"):
        gr = R * (0.2 if c.get("bigglasses") else 0.16)
        for exx in ex:
            ell(d, exx, ey, gr, gr * 0.85, None, ow * 0.6)
        d.line([(ex[0] + gr, ey), (ex[1] - gr, ey)], fill=INK, width=int(ow * 0.5))
    if c.get("wrinkles"):
        for sx in (-1, 1):
            d.line([(x + sx * R * 0.52, ey + R * 0.16), (x + sx * R * 0.6, ey + R * 0.26)], fill=shade(skin, 0.7), width=int(ow * 0.5))
    mx, my = x + lx * 0.8, y + R * 0.42
    open_ = talk and (math.sin(t * 15) > -0.2)
    if expr == "shock":
        ell(d, mx, my + R * 0.02, R * 0.07, R * 0.1, INK)
    elif open_:
        ell(d, mx, my, R * 0.08, R * 0.03 + R * 0.04 * abs(math.sin(t * 13)), INK)
    elif expr == "happy":
        d.arc((mx - R * 0.13, my - R * 0.12, mx + R * 0.13, my + R * 0.06), 20, 160, fill=INK, width=int(ow * 0.9))
    elif expr in ("sad", "worried"):
        d.arc((mx - R * 0.11, my - R * 0.01, mx + R * 0.11, my + R * 0.13), 200, 340, fill=INK, width=int(ow * 0.9))
    else:
        d.line([(mx - R * 0.09, my), (mx + R * 0.08, my - R * 0.01)], fill=INK, width=int(ow * 0.9))
    if expr == "worried":
        ell(d, x + R * 0.72, y - R * 0.38, R * 0.06, R * 0.1, (150, 200, 240), ow * 0.4)


# ------------------------------------------------------------------ text bubbles
def bubble(img, text, x, y, size=54, tail=None, kind="speech", a=1.0, maxw=620):
    if a <= 0:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = hand(size)
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if d.textlength(test, font=f) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = test
    lines.append(cur)
    tw = max(d.textlength(l, font=f) for l in lines)
    th = len(lines) * size * 1.05
    sc = 0.6 + 0.4 * ease(a)
    pw, ph = (tw / 2 + 34) * sc, (th / 2 + 22) * sc
    al = int(255 * clamp(a))
    if kind == "caption":
        rr(d, (x - pw, y - ph, x + pw, y + ph), 6, (255, 252, 235, al), 4, INK + (al,))
    elif kind == "thought":
        for k in range(9):
            ang = k / 9 * math.tau
            ell(d, x + math.cos(ang) * pw * 0.95, y + math.sin(ang) * ph * 0.95, pw * 0.32, ph * 0.42, (255, 255, 255, al), 4, INK + (al,))
        ell(d, x, y, pw * 1.02, ph * 1.02, (255, 255, 255, al))
        if tail:
            for k, s in enumerate((0.16, 0.1)):
                ell(d, x + (tail[0] - x) * (0.55 + k * 0.25), y + ph + (tail[1] - y - ph) * (0.55 + k * 0.25), size * s * 1.6, size * s * 1.3, (255, 255, 255, al), 4, INK + (al,))
    else:
        if tail:
            bx = clamp(tail[0], x - pw * 0.6, x + pw * 0.6)
            by_ = y + ph if tail[1] > y else y - ph
            poly(d, [(bx - 26 * sc, by_), (bx + 26 * sc, by_), tail], (255, 255, 255, al), 4, INK + (al,))
        rr(d, (x - pw, y - ph, x + pw, y + ph), 26 * sc, (255, 255, 255, al), 4, INK + (al,))
        if tail:
            by_ = y + ph if tail[1] > y else y - ph
            bx = clamp(tail[0], x - pw * 0.6, x + pw * 0.6)
            d.line([(bx - 22 * sc, by_), (bx + 22 * sc, by_)], fill=(255, 255, 255, al), width=8)
    fs = hand(int(size * sc))
    for k, l in enumerate(lines):
        d.text((x, y - th * sc / 2 + (k + 0.5) * size * 1.05 * sc), l, font=fs, fill=INK + (al,), anchor="mm")


def label(img, text, x, y, size=64, col=(255, 255, 255), a=1.0, anchor="mm", font=None):
    if a <= 0:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = font or hand(size)
    al = int(255 * clamp(a))
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        d.text((x + dx, y + dy), text, font=f, fill=INK + (al,), anchor=anchor)
    d.text((x, y), text, font=f, fill=col + (al,), anchor=anchor)


def pop(lt, t0, d=0.3):
    return ease((lt - t0) / d)
