"""2D comic-style cartoon engine: round-head characters with thick outlines, speech bubbles, simple sets."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 24
HERE = os.path.dirname(os.path.abspath(__file__))
INK = (28, 26, 30)
SKIN = (250, 214, 178)
WHITEHEAD = (247, 247, 245)
_fc = {}


def hand(size):
    k = ("hand", size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(HERE, "fonts/PatrickHand.woff"), size)
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


def bust(img, key, x, y, R, t=0.0, expr="neutral", talk=False, look=0.0, arms="down", seed=0, hold=None):
    """Draw a character from the chest up. (x, y) = head centre, R = head radius."""
    c = C[key]
    d = ImageDraw.Draw(img, "RGBA")
    R = R * c["scale"]
    ow = max(3, R * 0.055)
    bob = math.sin(t * 2.0 + seed) * R * 0.015
    y = y + bob
    # torso
    tw, tt = R * 1.18, y + R * 0.82
    top = c["top"]
    rr(d, (x - tw, tt, x + tw, tt + R * 2.6), R * 0.55, top, ow)
    if c.get("plaid"):
        for k in range(-3, 4):
            d.line([(x + k * R * 0.32, tt + 6), (x + k * R * 0.32, tt + R * 2.5)], fill=c["plaid"] + (150,), width=int(R * 0.07))
        for k in range(1, 7):
            d.line([(x - tw + 8, tt + k * R * 0.36), (x + tw - 8, tt + k * R * 0.36)], fill=c["plaid"] + (150,), width=int(R * 0.07))
    if c.get("stripes"):
        for k in range(1, 8):
            d.line([(x - tw + ow, tt + k * R * 0.3), (x + tw - ow, tt + k * R * 0.3)], fill=c["stripes"], width=int(R * 0.12))
    if c.get("dots"):
        rnd = random.Random(7)
        for _ in range(22):
            ell(d, x + rnd.uniform(-tw * 0.85, tw * 0.85), tt + rnd.uniform(R * 0.2, R * 2.3), R * 0.05, R * 0.05, (245, 245, 255))
    if c.get("shirt"):
        poly(d, [(x - R * 0.42, tt + 2), (x + R * 0.42, tt + 2), (x, tt + R * 1.25)], (252, 252, 250), ow * 0.6)
    if c.get("vest"):
        poly(d, [(x - tw + ow, tt + R * 0.35), (x - R * 0.2, tt + 4), (x, tt + R * 1.1), (x + R * 0.2, tt + 4), (x + tw - ow, tt + R * 0.35),
                 (x + tw - ow, tt + R * 2.6), (x - tw + ow, tt + R * 2.6)], c["vest"], ow * 0.6)
    if c.get("tie"):
        poly(d, [(x - R * 0.11, tt + R * 0.15), (x + R * 0.11, tt + R * 0.15), (x + R * 0.15, tt + R * 1.1), (x, tt + R * 1.3), (x - R * 0.15, tt + R * 1.1)], c["tie"], ow * 0.5)
    if c.get("braces"):
        for sx in (-1, 1):
            d.line([(x + sx * R * 0.48, tt + 4), (x + sx * R * 0.48, tt + R * 2.6)], fill=c["braces"], width=int(R * 0.14))
    if c.get("apron"):
        rr(d, (x - tw * 0.72, tt + R * 0.55, x + tw * 0.72, tt + R * 2.7), R * 0.12, (255, 255, 255), ow * 0.7)
        for sx in (-1, 1):
            d.line([(x + sx * tw * 0.62, tt + R * 0.58), (x + sx * R * 0.3, tt + 4)], fill=(235, 235, 235), width=int(R * 0.09))
    if c.get("collar") or key in ("boy6", "boy11", "friend", "grandpa"):
        for sx in (-1, 1):
            poly(d, [(x + sx * R * 0.05, tt + R * 0.2), (x + sx * R * 0.48, tt - 2), (x + sx * R * 0.55, tt + R * 0.28)], (255, 255, 255), ow * 0.6)
    # arms
    def arm(sx, hx_, hy_):
        sx0, sy0 = x + sx * (tw - R * 0.12), tt + R * 0.35
        d.line([(sx0, sy0), (hx_, hy_)], fill=INK, width=int(R * 0.34))
        d.line([(sx0, sy0), (hx_, hy_)], fill=top, width=int(R * 0.34 - ow * 1.6))
        ell(d, hx_, hy_, R * 0.17, R * 0.17, c["skin"], ow * 0.7)
    if arms == "hold":
        arm(-1, x - R * 0.55, tt + R * 1.55); arm(1, x + R * 0.55, tt + R * 1.55)
    elif arms == "raise":
        arm(-1, x - tw - R * 0.1, tt + R * 2.0); arm(1, x + tw + R * 0.45, y - R * 0.3 + math.sin(t * 6) * R * 0.08)
    elif arms == "point":
        arm(-1, x - tw - R * 0.1, tt + R * 2.0); arm(1, x + tw + R * 0.95, tt + R * 0.6)
    elif arms == "cross":
        d.line([(x - tw + R * 0.1, tt + R * 1.1), (x + tw - R * 0.1, tt + R * 1.35)], fill=INK, width=int(R * 0.36))
        d.line([(x - tw + R * 0.1, tt + R * 1.1), (x + tw - R * 0.1, tt + R * 1.35)], fill=shade(top, 0.92), width=int(R * 0.36 - ow * 1.6))
        d.line([(x + tw - R * 0.1, tt + R * 1.1), (x - tw + R * 0.1, tt + R * 1.35)], fill=INK, width=int(R * 0.36))
        d.line([(x + tw - R * 0.1, tt + R * 1.1), (x - tw + R * 0.1, tt + R * 1.35)], fill=top, width=int(R * 0.36 - ow * 1.6))
    if hold:
        hold(d, x, tt + R * 1.55, R)
    # neck + ears + head
    d.rectangle((x - R * 0.2, y + R * 0.6, x + R * 0.2, tt + 6), fill=c["skin"])
    if c["ears"]:
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.97, y + R * 0.08, R * 0.17 * c["ears"], R * 0.24 * c["ears"], c["skin"], ow * 0.8)
    st, hc = c["style"], c["hair"]
    if st == "bob":
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.9, y + R * 0.15, R * 0.36, R * 0.55, hc, ow)
    if st == "braids":
        for sx in (-1, 1):
            for k in range(4):
                ell(d, x + sx * R * 0.92, y + R * (0.55 + k * 0.42), R * 0.2, R * 0.23, hc, ow * 0.6)
    ell(d, x, y, R, R, c["skin"], ow)
    # hair on top
    if st in ("side", "slick", "short"):
        d.chord((x - R * 1.02, y - R * 1.06, x + R * 1.02, y + R * 0.75), 180, 360, fill=hc, outline=INK, width=int(ow))
        poly(d, [(x - R * 0.98, y - R * 0.12), (x - R * 0.35, y - R * 0.55), (x + R * 0.98, y - R * 0.3), (x + R * 0.99, y - R * 0.05)], hc)
        if st == "side":
            d.line([(x - R * 0.35, y - R * 1.0), (x - R * 0.42, y - R * 0.5)], fill=shade(hc, 0.7), width=int(ow * 0.8))
    elif st == "receding":
        d.chord((x - R * 1.0, y - R * 1.0, x + R * 1.0, y + R * 0.6), 200, 340, fill=hc, outline=INK, width=int(ow))
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.86, y - R * 0.3, R * 0.2, R * 0.35, hc)
    elif st in ("white", "oldwhite"):
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.88, y - R * 0.25, R * 0.24, R * 0.38, hc, ow * 0.6)
        if st == "oldwhite":
            d.chord((x - R * 0.95, y - R * 1.02, x + R * 0.95, y + R * 0.2), 200, 340, fill=hc, outline=INK, width=int(ow * 0.8))
    elif st == "bob":
        d.chord((x - R * 1.05, y - R * 1.08, x + R * 1.05, y + R * 0.6), 180, 360, fill=hc, outline=INK, width=int(ow))
        for k in range(3):
            d.arc((x - R * 0.9 + k * R * 0.6, y - R * 0.95, x - R * 0.3 + k * R * 0.6, y - R * 0.45), 200, 340, fill=shade(hc, 1.6), width=int(ow * 0.6))
    elif st == "braids":
        d.chord((x - R * 1.03, y - R * 1.06, x + R * 1.03, y + R * 0.6), 180, 360, fill=hc, outline=INK, width=int(ow))
        d.line([(x, y - R * 1.0), (x, y - R * 0.5)], fill=shade(hc, 0.6), width=int(ow * 0.7))
    elif st == "curly":
        for k in range(10):
            a = math.pi * (0.95 + k * 0.12)
            ell(d, x + math.cos(a) * R * 0.88, y + math.sin(a) * R * 0.88, R * 0.3, R * 0.3, hc, ow * 0.5)
    elif st == "bun":
        ell(d, x, y - R * 1.0, R * 0.35, R * 0.3, hc, ow * 0.7)
        d.chord((x - R * 1.02, y - R * 1.04, x + R * 1.02, y + R * 0.5), 180, 360, fill=hc, outline=INK, width=int(ow))
    # face
    blink = ((t + seed * 0.7) % 3.4) < 0.11
    lx = look * R * 0.12
    eyy = y + R * 0.02
    ex = [x - R * 0.34 + lx, x + R * 0.34 + lx]
    big = expr in ("shock",)
    for k, exx in enumerate(ex):
        if blink and not big:
            d.line([(exx - R * 0.1, eyy), (exx + R * 0.1, eyy)], fill=INK, width=int(ow * 0.8))
        else:
            ell(d, exx, eyy, R * (0.11 if big else 0.075), R * (0.13 if big else 0.105), INK)
            ell(d, exx - R * 0.025, eyy - R * 0.04, R * 0.025, R * 0.025, (255, 255, 255))
        sx = -1 if k == 0 else 1
        by = eyy - R * (0.32 if big else 0.25)
        if expr in ("angry", "sad", "worried"):
            dy = R * 0.07 if expr == "angry" else -R * 0.06   # + lowers the inner end
            inner, outer = (exx + R * 0.14, exx - R * 0.14) if sx < 0 else (exx - R * 0.14, exx + R * 0.14)
            d.line([(outer, by), (inner, by + dy)], fill=INK, width=int(ow))
        else:
            d.arc((exx - R * 0.15, by - R * 0.04, exx + R * 0.15, by + R * 0.12), 200, 340, fill=INK, width=int(ow * 0.9))
    if c.get("glasses") or c.get("bigglasses"):
        gr = R * (0.24 if c.get("bigglasses") else 0.19)
        for exx in ex:
            ell(d, exx, eyy, gr, gr * 0.9, None, ow * 0.7)
        d.line([(ex[0] + gr, eyy), (ex[1] - gr, eyy)], fill=INK, width=int(ow * 0.6))
    if c.get("wrinkles"):
        for sx in (-1, 1):
            d.arc((x + sx * R * 0.6 - R * 0.1, eyy + R * 0.1, x + sx * R * 0.6 + R * 0.1, eyy + R * 0.3), 200, 340, fill=shade(c["skin"], 0.7), width=int(ow * 0.5))
    # nose + mouth
    d.arc((x + lx - R * 0.08, y + R * 0.18, x + lx + R * 0.08, y + R * 0.34), 300, 120, fill=shade(c["skin"], 0.65), width=int(ow * 0.6))
    my = y + R * 0.52
    mx = x + lx
    open_ = talk and (math.sin(t * 15) > -0.2)
    if expr == "shock":
        ell(d, mx, my + R * 0.03, R * 0.11, R * 0.15, (90, 30, 35), ow * 0.7)
    elif open_:
        ell(d, mx, my, R * 0.15, R * 0.06 + R * 0.06 * abs(math.sin(t * 13)), (90, 30, 35), ow * 0.6)
    elif expr == "happy":
        d.chord((mx - R * 0.22, my - R * 0.16, mx + R * 0.22, my + R * 0.14), 10, 170, fill=(90, 30, 35), outline=INK, width=int(ow * 0.6))
    elif expr in ("sad", "worried"):
        d.arc((mx - R * 0.16, my, mx + R * 0.16, my + R * 0.18), 200, 340, fill=INK, width=int(ow * 0.8))
    elif expr == "angry":
        d.line([(mx - R * 0.16, my + R * 0.04), (mx + R * 0.16, my + R * 0.02)], fill=INK, width=int(ow))
    else:
        d.arc((mx - R * 0.14, my - R * 0.1, mx + R * 0.14, my + R * 0.06), 30, 150, fill=INK, width=int(ow * 0.8))
    if expr in ("happy", "neutral") and c["skin"] != WHITEHEAD:
        for sx in (-1, 1):
            ell(d, x + sx * R * 0.6, y + R * 0.38, R * 0.12, R * 0.07, (245, 150, 140, 90))
    if expr == "worried":
        ell(d, x + R * 0.78, y - R * 0.45, R * 0.07, R * 0.12, (150, 200, 240), ow * 0.4)


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
