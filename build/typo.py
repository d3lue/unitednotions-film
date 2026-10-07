"""Measures text with the real font files, so every room in the maze is big enough for its words."""
import os
from functools import lru_cache

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "site", "assets", "fonts")
if not os.path.isdir(FONTS):
    FONTS = os.path.join(HERE, "..", "assets", "fonts")
FILES = {
    "head": "unf-heros-condensed-bold.woff2",
    "text": "unf-heros-regular.woff2",
    "bold": "unf-heros-bold.woff2",
}


@lru_cache(None)
def _font(name):
    f = TTFont(os.path.join(FONTS, FILES[name]))
    return f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm


def width(text, font="text", size=16.0, tracking=0.0):
    """Width in px of one line of text. tracking in em."""
    cmap, metrics, upm = _font(font)
    total = 0
    for ch in text:
        g = cmap.get(ord(ch)) or cmap.get(ord("n"))
        total += metrics[g][0]
    return total / upm * size + tracking * size * len(text)


def wrap(text, max_width, font="text", size=16.0, tracking=0.0):
    """Greedy line breaking, the way a browser does it."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and width(trial, font, size, tracking) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def fit(text, max_width, max_lines, font="head", lo=20.0, hi=400.0, tracking=0.0, step=1.0):
    """Largest size at which the text fits the width in at most max_lines lines."""
    best = lo
    s = lo
    while s <= hi:
        lines = wrap(text, max_width, font, s, tracking)
        if len(lines) <= max_lines and all(width(l, font, s, tracking) <= max_width for l in lines):
            best = s
        else:
            break
        s += step
    return best, wrap(text, max_width, font, best, tracking)
