#!/usr/bin/env python3
"""Animated 'LIKE + SUBSCRIBE' call-to-action overlay (transparent PNG sequence, 1920x1080, 30fps).
Usage: python3 cta.py OUTDIR [--big] [--channel COMandFIN]
Normal: compact card bottom-right, 5s, slides in and out.
--big : larger card centred-bottom for the end screen, no slide-out (holds on last frame).
"""
import argparse, math, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK, RED, BLUE, GREY, PAPER = (35, 31, 32), (230, 33, 23), (30, 136, 229), (96, 96, 96), (255, 251, 240)

def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def lerp(a, b, t): return a + (b - a) * t
def clamp(t): return max(0.0, min(1.0, t))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)

def thumb(d, cx, cy, s, fill, line):
    # cuff
    d.rounded_rectangle([cx - 26*s, cy - 6*s, cx - 14*s, cy + 22*s], 3*s, fill=fill, outline=line, width=max(2, int(3*s)))
    # palm + thumb
    d.rounded_rectangle([cx - 10*s, cy - 6*s, cx + 22*s, cy + 22*s], 6*s, fill=fill, outline=line, width=max(2, int(3*s)))
    d.polygon([(cx - 10*s, cy - 4*s), (cx - 2*s, cy - 26*s), (cx + 6*s, cy - 24*s), (cx + 4*s, cy - 6*s)], fill=fill, outline=line)
    d.line([(cx - 10*s, cy - 4*s), (cx - 2*s, cy - 26*s), (cx + 6*s, cy - 24*s), (cx + 4*s, cy - 6*s)], fill=line, width=max(2, int(3*s)), joint="curve")

def bell(img, cx, cy, s, col, angle):
    b = Image.new("RGBA", (int(60*s), int(60*s)), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    m = 30*s
    d.pieslice([m - 16*s, m - 22*s, m + 16*s, m + 10*s], 180, 360, fill=col)
    d.polygon([(m - 16*s, m - 6*s), (m + 16*s, m - 6*s), (m + 21*s, m + 12*s), (m - 21*s, m + 12*s)], fill=col)
    d.ellipse([m - 5*s, m + 12*s, m + 5*s, m + 20*s], fill=col)
    b = b.rotate(angle, resample=Image.BICUBIC, center=(m, m - 18*s))
    img.alpha_composite(b, (int(cx - m), int(cy - m)))

def cursor(d, x, y, s):
    pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]
    pts = [(x + px*s, y + py*s) for px, py in pts]
    d.polygon(pts, fill="white", outline=INK); d.line(pts + [pts[0]], fill=INK, width=max(2, int(2.5*s)))

def frame(f, n, big, channel):
    s = 1.55 if big else 1.0
    cw, ch = 640*s, 200*s
    cx0 = (W - cw) / 2 if big else W - cw - 50
    y_rest = H - ch - (70 if big else 50)
    t_in = clamp(f / 14)
    y = lerp(H + 20, y_rest, ease_out_back(t_in)) if f < 14 else y_rest
    if not big and f > n - 15:
        y = lerp(y_rest, H + 20, smooth((f - (n - 15)) / 15))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x0, y0 = cx0, y
    # shadow + card (hand-drawn look: thick ink outline on paper)
    d.rounded_rectangle([x0 + 8*s, y0 + 10*s, x0 + cw + 8*s, y0 + ch + 10*s], 26*s, fill=(0, 0, 0, 90))
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], 26*s, fill=PAPER, outline=INK, width=int(5*s))
    ft = ImageFont.truetype(FB, int(30*s)); fb = ImageFont.truetype(FB, int(34*s))
    title = f"Follow {channel} for more stories" if big else "Enjoying the story?"
    tw = d.textlength(title, font=ft)
    d.text((x0 + (cw - tw) / 2, y0 + 22*s), title, font=ft, fill=INK)
    # buttons
    like_t = f - 32; sub_t = f - 64
    liked, subbed = like_t >= 0, sub_t >= 0
    lb = [x0 + 30*s, y0 + 82*s, x0 + 230*s, y0 + 168*s]
    sb = [x0 + 255*s, y0 + 82*s, x0 + cw - 30*s, y0 + 168*s]
    def pop(box, t):
        k = 1 + 0.12 * math.sin(math.pi * clamp(t / 8)) if 0 <= t <= 8 else 1
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        hw, hh = (box[2] - box[0]) / 2 * k, (box[3] - box[1]) / 2 * k
        return [cx - hw, cy - hh, cx + hw, cy + hh]
    l = pop(lb, like_t)
    d.rounded_rectangle(l, 43*s, fill=BLUE if liked else "white", outline=INK, width=int(4*s))
    thumb(d, l[0] + 58*s, (l[1] + l[3]) / 2 + 2*s, 1.0*s, "white" if liked else PAPER, INK)
    d.text((l[0] + 92*s, (l[1] + l[3]) / 2), "LIKE", font=fb, fill="white" if liked else INK, anchor="lm")
    b = pop(sb, sub_t)
    d.rounded_rectangle(b, 43*s, fill=GREY if subbed else RED, outline=INK, width=int(4*s))
    label = "SUBSCRIBED" if subbed else "SUBSCRIBE"
    fl = ImageFont.truetype(FB, int((30 if subbed else 34) * s))
    lw = d.textlength(label, font=fl); bx = (b[0] + b[2]) / 2 + 22*s
    d.text((bx - lw / 2, (b[1] + b[3]) / 2), label, font=fl, fill="white", anchor="lm")
    ang = 18 * math.sin((sub_t - 6) * 0.9) * math.exp(-max(0, sub_t - 6) / 14) if sub_t > 6 else 0
    bell(img, bx - lw / 2 - 34*s, (b[1] + b[3]) / 2 + 2*s, 1.0*s, "white", ang)
    # cursor path: enter -> LIKE -> SUBSCRIBE -> exit
    lx, ly = (lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2 + 8*s
    sx, sy = (sb[0] + sb[2]) / 2 + 40*s, (sb[1] + sb[3]) / 2 + 8*s
    if 14 <= f <= 100:
        if f < 30: p = smooth((f - 14) / 16); px, py = lerp(x0 + cw + 60*s, lx, p), lerp(y0 + ch + 40*s, ly, p)
        elif f < 50: px, py = lx, ly
        elif f < 62: p = smooth((f - 50) / 12); px, py = lerp(lx, sx, p), lerp(ly, sy, p)
        elif f < 84: px, py = sx, sy
        else: p = smooth((f - 84) / 16); px, py = lerp(sx, x0 + cw + 80*s, p), lerp(sy, y0 + ch + 60*s, p)
        press = 0.85 if (0 <= like_t <= 4 or 0 <= sub_t <= 4) else 1.0
        cursor(d, px, py, 1.1 * s * press)
    return img

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--big", action="store_true")
    ap.add_argument("--channel", default="COMandFIN"); ap.add_argument("--seconds", type=float, default=5.0)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    n = int(a.seconds * FPS)
    for f in range(n):
        frame(f, n, a.big, a.channel).save(os.path.join(a.out, f"c_{f:04d}.png"), compress_level=1)
