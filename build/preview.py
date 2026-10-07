"""Draws a picture of a maze layout so it can be judged without a browser.

python3 build/preview.py wide [scale] [columns]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import layout

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "..", "site", "assets", "img", "maze")
if not os.path.isdir(IMG):
    IMG = os.path.join(HERE, "..", "assets", "img", "maze")


def cover(im, w, h, focus=None):
    fx, fy = 0.5, 0.5
    if focus:
        a, b = focus.replace("%", "").split()
        fx, fy = float(a) / 100, float(b) / 100
    s = max(w / im.width, h / im.height)
    nw, nh = max(w, round(im.width * s)), max(h, round(im.height * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    x = round((nw - w) * fx)
    y = round((nh - h) * fy)
    return im.crop((x, y, x + w, y + h))


def render(out, U=16):
    import content
    photos = {p["slug"]: p for p in content.PHOTOS}
    rend = json.load(open(os.path.join(HERE, "data", "renditions.json")))
    C, R = out["spec"].cols, out["rows"]
    img = Image.new("RGB", (C * U, R * U), (0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(8, U // 2))
    except Exception:
        font = ImageFont.load_default()
    for r in out["rects"]:
        box = (r.x * U, r.y * U, r.x1 * U, r.y1 * U)
        if r.kind == "photo":
            src = Image.open(os.path.join(IMG, "%s-%d.webp" % (r.id, rend[r.id]["widths"][0]))).convert("RGB")
            img.paste(cover(src, r.w * U, r.h * U, photos[r.id]["focus"]), box[:2])
        else:
            d.rectangle(box, fill=(0, 0, 0))
            label = r.id.replace("work-", "").replace("statement", "STATEMENT").replace("quote-", "q: ")
            d.text((box[0] + 4, box[1] + 4), label[:int(r.w * U / (U * 0.32))], fill=(255, 255, 255), font=font)
    mz = out["maze"]
    for (x0, y0, x1, y1) in mz.bands(out["spec"].corridor):
        d.rectangle((x0 * U, y0 * U, x1 * U, y1 * U), fill=(0, 0, 0))
    th = mz.thread()
    if th:
        d.line([(x * U, y * U) for x, y in th], fill=(255, 255, 255), width=max(1, U // 12))
        x, y = th[0]
        d.ellipse((x * U - 3, y * U - 3, x * U + 3, y * U + 3), fill=(255, 255, 255))
    return img


def columns(img, n, gap=24, bg=(40, 40, 40)):
    h = (img.height + n - 1) // n
    sheet = Image.new("RGB", (img.width * n + gap * (n - 1), h), bg)
    for k in range(n):
        part = img.crop((0, k * h, img.width, min(img.height, (k + 1) * h)))
        sheet.paste(part, (k * (img.width + gap), 0))
    return sheet


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "wide"
    U = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    out = layout.build(name, seed=seed)
    print(name, "rows", out["rows"], out["info"])
    img = render(out, U)
    dest = sys.argv[5] if len(sys.argv) > 5 else "/tmp/claude-0/-home-claude/c7e8b4fd-c914-58ae-80e6-77bbaca3a7d0/scratchpad/unf/maze-%s.png" % name
    columns(img, n).save(dest)
    print(dest)
