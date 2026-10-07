"""Makes the icon of the browser tab: the white dot that walks the maze, on black.

    python3 build/make_icon.py

It was run once. The three files it writes are kept with the site:
    assets/img/favicon.svg             for browsers of today
    favicon.ico                        for the browsers that ask for /favicon.ico
    assets/img/apple-touch-icon.png    for a phone's home screen
To change the icon, change the numbers here and run it again.
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
if not os.path.isdir(SITE):
    SITE = os.path.join(HERE, "..")              # the build folder sits inside the site folder
DOT = 0.22                                       # radius of the dot, as a share of the side


def disc(side, margin=0.0):
    """A white dot on black, drawn four times larger and reduced, so its edge is smooth."""
    big = side * 4
    im = Image.new("RGB", (big, big), (0, 0, 0))
    r = big * DOT * (1 - margin)
    ImageDraw.Draw(im).ellipse((big / 2 - r, big / 2 - r, big / 2 + r, big / 2 + r), fill=(255, 255, 255))
    return im.resize((side, side), Image.LANCZOS)


svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#000"/>'
       '<circle cx="16" cy="16" r="%s" fill="#fff"/></svg>\n' % ("%.2f" % (32 * DOT)).rstrip("0").rstrip("."))
with open(os.path.join(SITE, "assets", "img", "favicon.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
disc(48).save(os.path.join(SITE, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
disc(180, margin=0.1).save(os.path.join(SITE, "assets", "img", "apple-touch-icon.png"), optimize=True)
print("favicon.svg, favicon.ico and apple-touch-icon.png written")
