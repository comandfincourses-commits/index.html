#!/usr/bin/env python3
"""Animated call-to-action overlay (transparent PNG sequence, 30fps).
Usage: python3 cta.py OUTDIR [--big] [--share] [--vertical --y TOP] [--seconds N] [--channel NAME]
Card slides in, a cursor clicks LIKE (turns blue), [SHARE (turns green)], then SUBSCRIBE (turns grey,
'SUBSCRIBED', bell rings). Normal cards slide out at the end; --big holds (end screen).
"""
import argparse, math, os
from PIL import Image, ImageDraw, ImageFont

FPS = 30
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK, RED, BLUE, GREEN, GREY, PAPER = (35, 31, 32), (230, 33, 23), (30, 136, 229), (0, 168, 132), (96, 96, 96), (255, 251, 240)

def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def clamp(t): return max(0.0, min(1.0, t))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)

def thumb(d, cx, cy, s, fill, line):
    w = max(2, int(3 * s))
    d.rounded_rectangle([cx - 26*s, cy - 6*s, cx - 14*s, cy + 22*s], 3*s, fill=fill, outline=line, width=w)
    d.rounded_rectangle([cx - 10*s, cy - 6*s, cx + 22*s, cy + 22*s], 6*s, fill=fill, outline=line, width=w)
    pts = [(cx - 10*s, cy - 4*s), (cx - 2*s, cy - 26*s), (cx + 6*s, cy - 24*s), (cx + 4*s, cy - 6*s)]
    d.polygon(pts, fill=fill); d.line(pts, fill=line, width=w, joint="curve")

def share_icon(d, cx, cy, s, col):
    r = 7 * s; a, b, c = (cx + 12*s, cy - 14*s), (cx - 14*s, cy), (cx + 12*s, cy + 14*s)
    d.line([a, b, c], fill=col, width=max(2, int(4 * s)))
    for x, y in (a, b, c): d.ellipse([x - r, y - r, x + r, y + r], fill=col)

def bell(img, cx, cy, s, col, angle):
    b = Image.new("RGBA", (int(60*s), int(60*s)), (0, 0, 0, 0)); d = ImageDraw.Draw(b); m = 30*s
    d.pieslice([m - 16*s, m - 22*s, m + 16*s, m + 10*s], 180, 360, fill=col)
    d.polygon([(m - 16*s, m - 6*s), (m + 16*s, m - 6*s), (m + 21*s, m + 12*s), (m - 21*s, m + 12*s)], fill=col)
    d.ellipse([m - 5*s, m + 12*s, m + 5*s, m + 20*s], fill=col)
    b = b.rotate(angle, resample=Image.BICUBIC, center=(m, m - 18*s))
    img.alpha_composite(b, (int(cx - m), int(cy - m)))

def cursor(d, x, y, s):
    pts = [(x + px*s, y + py*s) for px, py in [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]]
    d.polygon(pts, fill="white"); d.line(pts + [pts[0]], fill=INK, width=max(2, int(2.5*s)))

def frame(f, n, big, channel, W, H, y_top, share):
    s = (1.2 if share else 1.55) if big else (0.95 if share else 1.0)
    cw, ch = (860 if share else 640) * s, 200 * s
    cx0 = (W - cw) / 2 if (big or y_top is not None) else W - cw - 50
    y_rest = y_top if y_top is not None else H - ch - (70 if big else 50)
    y = lerp(H + 20, y_rest, ease_out_back(clamp(f / 14))) if f < 14 else y_rest
    if not big and f > n - 15: y = lerp(y_rest, H + 20, smooth((f - (n - 15)) / 15))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img); x0, y0 = cx0, y
    d.rounded_rectangle([x0 + 8*s, y0 + 10*s, x0 + cw + 8*s, y0 + ch + 10*s], 26*s, fill=(0, 0, 0, 90))
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], 26*s, fill=PAPER, outline=INK, width=int(5*s))
    ft = ImageFont.truetype(FB, int(30*s)); fb = ImageFont.truetype(FB, int(32*s))
    title = f"Follow {channel} for more stories" if big else ("Like, Share & Subscribe!" if share else "Enjoying the story?")
    d.text((x0 + cw / 2, y0 + 40*s), title, font=ft, fill=INK, anchor="mm")
    # buttons: (key, box, click frame)
    if share:
        boxes = {"like": [30, 230], "share": [245, 470], "sub": [485, 830]}; clicks = {"like": 32, "share": 54, "sub": 76}
    else:
        boxes = {"like": [30, 230], "sub": [255, 610]}; clicks = {"like": 32, "sub": 64}
    def box(k): a, b = boxes[k]; return [x0 + a*s, y0 + 82*s, x0 + b*s, y0 + 168*s]
    def pop(bx, t):
        k = 1 + 0.12 * math.sin(math.pi * clamp(t / 8)) if 0 <= t <= 8 else 1
        cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2; hw, hh = (bx[2] - bx[0]) / 2 * k, (bx[3] - bx[1]) / 2 * k
        return [cx - hw, cy - hh, cx + hw, cy + hh]
    t = {k: f - v for k, v in clicks.items()}
    l = pop(box("like"), t["like"]); on = t["like"] >= 0
    d.rounded_rectangle(l, 43*s, fill=BLUE if on else "white", outline=INK, width=int(4*s))
    thumb(d, l[0] + 52*s, (l[1] + l[3]) / 2 + 2*s, 0.95*s, "white" if on else PAPER, INK)
    d.text((l[0] + 84*s, (l[1] + l[3]) / 2), "LIKE", font=fb, fill="white" if on else INK, anchor="lm")
    if share:
        b = pop(box("share"), t["share"]); on = t["share"] >= 0
        d.rounded_rectangle(b, 43*s, fill=GREEN if on else "white", outline=INK, width=int(4*s))
        share_icon(d, b[0] + 44*s, (b[1] + b[3]) / 2, 0.95*s, "white" if on else INK)
        d.text((b[0] + 76*s, (b[1] + b[3]) / 2), "SHARE", font=fb, fill="white" if on else INK, anchor="lm")
    b = pop(box("sub"), t["sub"]); on = t["sub"] >= 0
    d.rounded_rectangle(b, 43*s, fill=GREY if on else RED, outline=INK, width=int(4*s))
    label = "SUBSCRIBED" if on else "SUBSCRIBE"
    fl = ImageFont.truetype(FB, int((27 if on else 31) * s))
    lw = d.textlength(label, font=fl); bx = (b[0] + b[2]) / 2 + 20*s
    d.text((bx - lw / 2, (b[1] + b[3]) / 2), label, font=fl, fill="white", anchor="lm")
    ts = t["sub"]; ang = 18 * math.sin((ts - 6) * 0.9) * math.exp(-max(0, ts - 6) / 14) if ts > 6 else 0
    bell(img, bx - lw / 2 - 30*s, (b[1] + b[3]) / 2 + 2*s, 0.95*s, "white", ang)
    # cursor travels button to button
    stops = [(k, ((box(k)[0] + box(k)[2]) / 2 + (30*s if k == "sub" else 0), (box(k)[1] + box(k)[3]) / 2 + 8*s), clicks[k]) for k in clicks]
    last_click = stops[-1][2]
    if 14 <= f <= last_click + 36:
        px, py = x0 + cw + 60*s, y0 + ch + 40*s; prev = (px, py, 14)
        for k, (sx, sy), c in stops:
            if f < c - 2:
                p = smooth((f - prev[2]) / max(1, (c - 2) - prev[2])); px, py = lerp(prev[0], sx, p), lerp(prev[1], sy, p); break
            prev = (sx, sy, c + 8); px, py = sx, sy
        else:
            if f > last_click + 20:
                p = smooth((f - last_click - 20) / 16); px, py = lerp(px, x0 + cw + 80*s, p), lerp(py, y0 + ch + 60*s, p)
        press = 0.85 if any(0 <= t[k] <= 4 for k in t) else 1.0
        cursor(d, px, py, 1.1 * s * press)
    return img

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--big", action="store_true")
    ap.add_argument("--share", action="store_true", help="add a SHARE button between LIKE and SUBSCRIBE")
    ap.add_argument("--channel", default="COMandFIN"); ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--vertical", action="store_true", help="1080x1920 canvas, card centred")
    ap.add_argument("--y", type=float, help="card top y")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    W, H = (1080, 1920) if a.vertical else (1920, 1080)
    y = a.y if a.y is not None else (1300 if a.vertical else None)
    n = int(a.seconds * FPS)
    for f in range(n):
        frame(f, n, a.big, a.channel, W, H, y, a.share).save(os.path.join(a.out, f"c_{f:04d}.png"), compress_level=1)
