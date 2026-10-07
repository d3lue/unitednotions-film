"""Measure the colour of every maze photo and put the photos in palette order.

Run:  python3 build/colour.py
Reads  site/assets/img/maze/<slug>-<width>.webp  and  build/data/renditions.json
Writes build/data/colour.json  (per photo: swatch, clusters, position in the palette)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
if not os.path.isdir(SITE):
    SITE = os.path.join(HERE, "..")          # the build folder sits inside the site folder
IMG = os.path.join(SITE, "assets", "img", "maze")


# ---------- colour maths ----------
def srgb_to_lab(rgb):
    """rgb: float array (..., 3) in 0..255 -> CIE Lab (D65)."""
    c = rgb / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ m.T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def lab_to_srgb(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    f = np.stack([fx, fy, fz], axis=-1)
    xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787)
    xyz = xyz * np.array([0.95047, 1.0, 1.08883])
    m = np.array([[3.2404542, -1.5371385, -0.4985314],
                  [-0.9692660, 1.8760108, 0.0415560],
                  [0.0556434, -0.2040259, 1.0572252]])
    lin = np.clip(xyz @ m.T, 0, 1)
    c = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(int)


def hexcol(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)


def kmeans(points, k=5, iters=24, seed=7):
    rng = np.random.default_rng(seed)
    # k-means++ start
    centres = [points[rng.integers(len(points))]]
    for _ in range(k - 1):
        d = np.min([((points - c) ** 2).sum(1) for c in centres], axis=0)
        centres.append(points[rng.choice(len(points), p=d / d.sum())])
    centres = np.array(centres)
    for _ in range(iters):
        d = ((points[:, None, :] - centres[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for j in range(k):
            sel = points[lab == j]
            if len(sel):
                centres[j] = sel.mean(0)
    d = ((points[:, None, :] - centres[None, :, :]) ** 2).sum(2)
    lab = d.argmin(1)
    weights = np.bincount(lab, minlength=k) / len(points)
    return centres, weights


def analyse(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((96, 96), Image.LANCZOS)
    rgb = np.asarray(im).astype(float).reshape(-1, 3)
    lab = srgb_to_lab(rgb)
    centres, weights = kmeans(lab, k=5)
    chroma = np.hypot(centres[:, 1], centres[:, 2])
    # the colour that "is" the picture: big and colourful beats big and grey
    score = weights * (0.25 + chroma / 22.0) ** 1.25 * (0.35 + np.clip(centres[:, 0], 0, 100) / 100.0)
    sig = centres[score.argmax()]
    pix_chroma = np.hypot(lab[:, 1], lab[:, 2])
    order = np.argsort(-weights)
    return {
        "sig": [round(float(v), 1) for v in sig],
        "mean": [round(float(v), 1) for v in lab.mean(0)],
        "dark": round(float((lab[:, 0] < 18).mean()), 3),
        "light": round(float((lab[:, 0] > 75).mean()), 3),
        "chroma": round(float(pix_chroma.mean()), 1),
        "clusters": [{"lab": [round(float(v), 1) for v in centres[j]], "w": round(float(weights[j]), 3),
                      "hex": hexcol(lab_to_srgb(centres[j]))} for j in order],
    }


# ---------- palette order ----------
def hue_deg(a, b):
    return math.degrees(math.atan2(b, a)) % 360


def palette_position(rec, mode):
    """Return a sort key. Lower comes first in the maze."""
    L, a, b = rec["sig"]
    C = math.hypot(a, b)
    h = hue_deg(a, b)
    mL = rec["mean"][0]
    if mode == "single":
        # one pass: salt, sand, gold, clay, red, rose, violet, blue, teal, green, then night
        if C < 9:
            if L >= 60:
                return (0, -L)
            if L <= 34 or rec["dark"] > 0.55:
                return (2, -L)
            # mid greys sit with the cool colours
            return (1, ((100 - (250 if b < 2 else 75)) % 360) / 360.0)
        t = ((105 - h) % 360) / 360.0  # yellow first, hue falling, green last
        return (1, t)
    if mode == "day":
        night = mL < 33 or rec["dark"] > 0.42
        if not night:
            if C < 9:
                return (0, 0.52 - L / 1000.0)  # pale, colourless pictures sit with the sand
            # day: blue sky, green, ochre, gold, amber, red
            t = ((300 - h) % 360) / 360.0
            return (0, 0.05 + t)
        if C < 9:
            return (1, 2.0 - L / 1000.0)  # black and white closes the night
        # night: amber street light, red neon, magenta, violet, blue, green
        t = ((100 - h) % 360) / 360.0
        return (1, t)
    raise ValueError(mode)


def main():
    rend = json.load(open(os.path.join(HERE, "data", "renditions.json")))
    out = {}
    for slug, r in rend.items():
        rec = analyse(os.path.join(IMG, "%s-%d.webp" % (slug, r["widths"][0])))
        rec["swatch"] = hexcol(lab_to_srgb(np.array(rec["sig"])))
        rec["meanhex"] = hexcol(lab_to_srgb(np.array(rec["mean"])))
        out[slug] = rec
    for mode in ("single", "day"):
        order = sorted(out, key=lambda s: palette_position(out[s], mode))
        for i, s in enumerate(order):
            out[s]["order_" + mode] = i
    json.dump(out, open(os.path.join(HERE, "data", "colour.json"), "w"), indent=1)
    print("analysed", len(out))


if __name__ == "__main__":
    main()
