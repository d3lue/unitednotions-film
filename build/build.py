"""Writes the site, in English and then in Spanish (the folder es).

    python3 build/build.py                    every page of both languages
    UNF_ONLY=en python3 build/build.py        English only
    UNF_LANG=es python3 build/build.py        Spanish only
    UNF_TRIES=300 python3 build/build.py      a quicker search for the plan of the maze, for a look while editing

The home page and its maze are made here. The maze is generated three times: for wide screens, for medium screens and for phones.
The other pages are made by pages.py (About, People, News, Film Futurism, Press) and research.py (the lab notes).
The Spanish comes from strings_es.py and from build/research/es.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys

if __name__ == "__main__" and os.environ.get("PYTHONHASHSEED") != "0":
    # The same texts and pictures must give the same pages every time.
    # Python keeps some collections in a different order in each run unless this number is fixed, so the build starts itself again with it.
    # (The maze itself no longer depends on that order: maze.py sorts before it chooses. This is a second lock.)
    os.execve(sys.executable, [sys.executable] + sys.argv, dict(os.environ, PYTHONHASHSEED="0"))

import content
import content_pages
import i18n
from i18n import t

i18n.localise_content(content, content_pages)        # the texts, in the language of this build

import layout                                       # noqa: E402
import typo                                         # noqa: E402
from maze import Band, Card, Photo, Work            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
if not os.path.isdir(SITE):
    SITE = os.path.join(HERE, "..")          # the build folder sits inside the site folder
ES = i18n.LANG == "es"
OUT = os.path.join(SITE, "es") if ES else SITE      # the Spanish pages are separate files, in the folder es
SITE_URL = "https://unitednotions.film/"
HOME_URL = SITE_URL + ("es/" if ES else "")
QL = ' lang="en"' if ES else ""                     # press quotes stay in the language they were written in
E = html.escape


def title_lang(w):
    """The lang attribute for the title of a work, when the title is in another language than the page."""
    lang = w.get("lang") or "en"
    return ' lang="%s"' % lang if lang != i18n.LANG else ""

# the three mazes: letter used in the CSS, layout name, seed that picks one of the many possible mazes
MAZES = [("a", "wide", 1), ("b", "medium", 1), ("c", "narrow", 1)]
TRIES = int(os.environ.get("UNF_TRIES", "1500"))
FIT_SAFETY = 0.965      # titles are set a little smaller than measured, so no font can overflow


def num(v):
    """Short number for CSS and SVG."""
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


# ---------------------------------------------------------------------------------------------- data
def gather():
    colour, rend, quotes = layout.load()
    built = {}
    for letter, name, seed in MAZES:
        out = layout.build(name, tries=TRIES, seed=seed)
        out["by_id"] = {r.id: r for r in out["rects"]}
        built[letter] = out
        print("  maze %s (%s): %d rows, %s" % (letter, name, out["rows"], out["info"]), file=sys.stderr)
    return colour, rend, quotes, built


def place(built, rid):
    """The CSS variables that put a tile in its place in all three mazes."""
    parts = []
    for letter, _, _ in MAZES:
        r = built[letter]["by_id"][rid]
        parts.append("--%sx:%d;--%sy:%d;--%sw:%d;--%sh:%d" % (letter, r.x, letter, r.y, letter, r.w, letter, r.h))
    return ";".join(parts)


def work_by_slug():
    return {w["slug"]: w for w in content.WORKS}


# ---------------------------------------------------------------------------------------------- pictures
def srcset(rend, slug, prefix="assets/img/maze/"):
    r = rend[slug]
    return ", ".join("%s%s-%d.webp %dw" % (prefix, slug, w, w) for w in r["widths"])


def src(rend, slug, want=800, prefix="assets/img/maze/"):
    r = rend[slug]
    w = min(r["widths"], key=lambda x: (abs(x - want), x))
    return "%s%s-%d.webp" % (prefix, slug, w)


def photo_tile(p, built, rend, colour, works, eager, key_of=None):
    slug = p["slug"]
    r = rend[slug]
    wa = built["a"]["by_id"][slug].w
    wb = built["b"]["by_id"][slug].w
    wc = built["c"]["by_id"][slug].w
    sizes = "(min-width: 1920px) %dpx, (min-width: 1200px) %svw, (min-width: 700px) %svw, %svw" % (
        round(wa / 24 * 1920), num(wa / 24 * 100), num(wb / 16 * 100), num(wc / 12 * 100))
    style = place(built, slug) + ";--tone:%s" % colour[slug]["swatch"]
    if p["focus"]:
        style += ";--focus:%s" % p["focus"]
    attrs = 'loading="eager" fetchpriority="high"' if eager == "high" else ('loading="eager"' if eager else 'loading="lazy"')
    img = ('<img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" %s decoding="async">'
           % (src(rend, slug), srcset(rend, slug), sizes, r["w"], r["h"], E(content.caption(p)), attrs))
    w = works.get(p["work"])
    link = None
    label = ""
    if w:
        link = w["href"]
        label = "%s, %d" % (w["title"], w["year"])
    elif slug in content.NOTE_OF:
        link = "research/%s.html" % content.NOTE_OF[slug]
        label = t("From the lab")
    elif p["work"] in content.OTHER_LINKS:
        label, link = content.OTHER_LINKS[p["work"]]
    credit = ("<small>%s</small>" % E(t("Photo: %s") % p["credit"])) if p["credit"] else ""
    cls = "tile photo"
    if key_of:
        cls += " photo-key"
        cap = "<figcaption>%s%s</figcaption>" % (E(key_of["line"]), credit)
    else:
        head = ("<b>%s</b>" % E(label)) if label else ""
        cap = "<figcaption>%s%s%s</figcaption>" % (head, E(content.caption(p)), credit)
    inner = ('<a href="%s">%s</a>' % (E(link), img)) if link else img
    return '<figure class="%s" style="%s">%s%s</figure>' % (cls, style, inner, cap)


# ---------------------------------------------------------------------------------------------- rooms
def sized(built, rid, fn):
    """Run a type-fitting function for the room in each maze. Returns {letter: result}."""
    out = {}
    for letter, name, _ in MAZES:
        r = built[letter]["by_id"][rid]
        out[letter] = fn(name, r.w, r.h)
    return out


def title_room(built, colour, order):
    ty = {letter: layout.title_type(name) for letter, name, _ in MAZES}
    style = place(built, "title") + ";" + ";".join("--%sts:%s" % (l, num(ty[l]["size"] * FIT_SAFETY)) for l in ty)
    sw = "".join('<i style="--c:%s"></i>' % colour[s]["swatch"] for s in order)
    return ('<div class="tile room room-title" id="top" data-room="title" style="%s">'
            '<h1><span>United</span> <span>Notions</span> <span>Film</span></h1>'
            '<div class="palette" aria-hidden="true">%s</div></div>' % (style, sw))


def intro_room(built):
    return ('<div class="tile room room-intro" id="about" data-room="intro" style="%s">'
            '<p class="lead">%s</p><p class="more">%s</p>'
            '<p class="how" data-how>%s</p>'
            '<p class="go"><a href="about.html">%s</a><a href="people.html">%s</a></p>'
            '</div>' % (place(built, "intro"), E(content.INTRO), E(content.INTRO_MORE), E(content.HOW_TO_WALK), E(t("Our story")), E(t("The people"))))


def work_room(w, built, quotes):
    rid = "work-" + w["slug"]
    note = layout.work_note(w, quotes)
    ty = sized(built, rid, lambda name, cw, ch: layout.work_room_type(name, w, note, cw, ch))
    sizes = []
    for letter in ty:
        if ty[letter] is None:
            raise SystemExit("The room of %s is too small in maze %s" % (w["slug"], letter))
        sizes.append("--%sts:%s" % (letter, num(ty[letter]["size"] * FIT_SAFETY)))
    style = place(built, rid) + ";" + ";".join(sizes)
    lang = title_lang(w)
    if note["kind"] == "quote":
        body = ('<blockquote class="note"%s><p>“%s”</p><cite class="source">%s</cite></blockquote>'
                % (QL, E(note["text"]), E(note["source"])))
    else:
        body = '<p class="note">%s</p>' % E(note["text"])
    return ('<article class="tile room room-work" id="%s" data-room="work-%s" data-work="%s" style="%s">'
            '<p class="meta">%s, %d</p>'
            '<h2%s><a href="%s">%s</a></h2>%s'
            '<p class="go"><a href="%s">%s</a></p></article>'
            % (w["slug"], w["slug"], w["slug"], style, E(w["kind"]), w["year"], lang, E(w["href"]), E(w["title"]), body, E(w["href"]), E(w["cta"])))


def quote_room(rid, built, quotes, works):
    slug, qi = rid[len("quote-"):].rsplit("-", 1)
    qi = int(qi)
    w = works[slug]
    q = quotes[w["qkey"]]["quotes"][qi]
    source = layout.source_name(q["source"])
    ty = sized(built, rid, lambda name, cw, ch: layout.card_type(name, q["text"], source, cw, ch))
    sizes = ";".join("--%scs:%s" % (l, num((ty[l]["size"] if ty[l] else 20) * FIT_SAFETY)) for l in ty)
    lang = title_lang(w)
    return ('<figure class="tile room room-quote" data-room="%s" style="%s;%s"><blockquote%s>“%s”</blockquote>'
            '<figcaption>%s%s<a href="#%s"%s>%s</a></figcaption></figure>'
            % (rid, place(built, rid), sizes, QL, E(q["text"]), E(source), E(t(", on ")), slug, lang, E(w["title"])))


def statement_room(rid, built):
    k = int(rid.rsplit("-", 1)[1])
    text = content.STATEMENTS[k]
    ty = {letter: layout.statement_type(name, text) for letter, name, _ in MAZES}
    sizes = ";".join("--%sss:%s" % (l, num(ty[l]["size"] * (FIT_SAFETY if ty[l]["fit"] else 1))) for l in ty)
    return '<div class="tile room room-statement" data-room="%s" style="%s;%s"><p>%s</p></div>' % (rid, place(built, rid), sizes, E(text))


def exit_room(built):
    return ('<div class="tile room room-exit" data-room="exit" style="%s">'
            '<p class="journey" data-journey data-t="%s" hidden></p><a href="#works">%s</a></div>'
            % (place(built, "exit"), E(t("Your way through the maze:")), E(t("Every work, listed"))))


# ---------------------------------------------------------------------------------------------- lines
def rect_path(rects):
    return "".join("M%s %sH%sV%sH%sZ" % (num(x0), num(y0), num(x1), num(y1), num(x0)) for (x0, y0, x1, y1) in rects)


def floor_rects(out):
    """Every piece of open floor: corridors, rooms and gaps."""
    mz = out["maze"]
    rects = list(mz.bands(out["spec"].corridor))
    for y in range(mz.R):
        x = 0
        while x < mz.C:
            if mz.owner[y][x] == -1:
                e = x
                while e < mz.C and mz.owner[y][e] == -1:
                    e += 1
                rects.append((x, y, e, y + 1))
                x = e
            else:
                x += 1
    return rects


def merge_rows(rects):
    """Join floor rectangles that sit exactly under each other, to keep the file small."""
    by = {}
    for (x0, y0, x1, y1) in rects:
        by.setdefault((x0, x1), []).append((y0, y1))
    out = []
    for (x0, x1), spans in by.items():
        spans.sort()
        cur = list(spans[0])
        for a, b in spans[1:]:
            if abs(a - cur[1]) < 1e-9:
                cur[1] = b
            else:
                out.append((x0, cur[0], x1, cur[1]))
                cur = [a, b]
        out.append((x0, cur[0], x1, cur[1]))
    return out


def lines_svg(letter, out):
    """The floor of the maze: corridors, rooms and gaps. The walker and the visitor's trail are added in the browser."""
    mz = out["maze"]
    px = 1.0 / layout.unit(out["name"])
    d = rect_path(merge_rows(floor_rects(out)))
    return ('<svg class="lines lines-%s" data-px="%s" viewBox="0 0 %d %d" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            '<path class="edge" stroke-width="%s" d="%s"/><path class="floor" d="%s"/></svg>'
            % (letter, num(px), mz.C, mz.R, num(2 * px), d, d))


def plan_svg(letter, out, colour, works):
    mz = out["maze"]
    parts = ['<svg class="plan-%s" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (letter, mz.C, mz.R, E(t("Plan of the maze")))]
    gap = 0.22
    for r in out["rects"]:
        if r.kind == "photo":
            parts.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (num(r.x + gap), num(r.y + gap), num(r.w - 2 * gap), num(r.h - 2 * gap), colour[r.id]["swatch"]))
    parts.append('<path class="trail" stroke-width="0.34" d=""/>')
    parts.append('<rect class="here" x="-0.5" y="0" width="%s" height="10" stroke-width="0.35"/>' % num(mz.C + 1))
    for r in out["rects"]:
        if r.kind == "room" and r.role == "work":
            w = works[r.id[len("work-"):]]
            parts.append('<a href="#%s" data-name="%s" data-room="%s"><circle cx="%s" cy="%s" r="1.05" stroke-width="0.3"/></a>'
                         % (w["slug"], E(w["title"]), r.id, num(r.x + r.w / 2), num(r.y + r.h / 2)))
    parts.append('<circle class="me" cx="0" cy="0" r="0.9" stroke-width="0.25"/>')
    parts.append("</svg>")
    return "".join(parts)


def walk_json(letter, out):
    """What the browser needs to let a visitor walk this maze."""
    import zlib
    g = out["walk"]
    rooms = []
    for r in out["rects"]:
        if r.kind == "room" and r.id in g["spots"]:
            rooms.append([r.id, r.role, g["spots"][r.id], r.x, r.y, r.w, r.h])
    sig = "%s%08x" % (letter, zlib.crc32(json.dumps([g["nodes"], g["edges"]]).encode()) & 0xffffffff)
    data = dict(sig=sig, cols=out["maze"].C, rows=out["maze"].R, n=g["nodes"], e=g["edges"], rooms=rooms, start=g["spots"].get("title", 0),
                guide=layout.guide(out))
    return '<script type="application/json" id="walk-%s">%s</script>' % (letter, json.dumps(data, separators=(",", ":")))


def pad():
    """The arrows, the count of works found, and the two buttons: follow the line again, start again."""
    arrow = '<button type="button" class="%s" data-dir="%s" aria-label="%s"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="%s"/></svg></button>'
    return ('<div class="pad" data-pad role="group" aria-label="%s" data-t-walk="%s" data-t-some="%s" data-t-all="%s">' % (
                E(t("Walk the maze")), E(t("Scroll to follow the line")), E(t("{n} of {m} works found")), E(t("All {m} works found")))
            + arrow % ("up", "up", E(t("Walk up")), "M5 15l7-7 7 7")
            + arrow % ("left", "left", E(t("Walk left")), "M15 5l-7 7 7 7")
            + '<button type="button" class="me" data-find aria-label="%s"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/></svg></button>' % E(t("Show where I am"))
            + arrow % ("right", "right", E(t("Walk right")), "M9 5l7 7-7 7")
            + arrow % ("down", "down", E(t("Walk down")), "M5 9l7 7 7-7")
            + '<div class="status"><p class="tally" aria-live="polite"><span data-tally>%s</span></p>'
              '<button type="button" class="again" data-follow hidden>%s</button>'
              '<button type="button" class="again" data-again hidden>%s</button></div>'
              '</div>' % (E(t("Scroll to follow the line")), E(t("Back to the line")), E(t("Start again"))))


# ---------------------------------------------------------------------------------------------- words in the corridors
def hall_texts(built, quotes, works):
    """The press lines in the corridors. Their places were chosen before each maze was cut (halls.py)."""
    lines = layout.hall_lines(quotes)
    out = []
    for h in lines:
        places = {l: built[l]["maze"].halls.get(h["key"]) for l in ("a", "b")}
        if not places["a"] and not places["b"]:
            continue
        cls, style = ["hall"], []
        for l in ("a", "b"):
            p = places[l]
            if p:
                style.append("--%sx:%s;--%sy:%s" % (l, num(p["x"]), l, num(p["y"])))
                if p["upright"]:
                    cls.append("up-" + l)
                if p["form"] == "short":
                    cls.append("short-" + l)
            else:
                cls.append("no-" + l)
        out.append('<p class="%s" style="%s" aria-hidden="true"%s>“%s”<cite>%s<span>%s%s</span></cite></p>'
                   % (" ".join(cls), ";".join(style), QL, E(h["text"]), E(h["source"]), E(t(", on ")), E(h["title"])))
    return "".join(out), len(out), len(lines)


# ---------------------------------------------------------------------------------------------- the maze section
def maze_section(colour, rend, quotes, built):
    works = work_by_slug()
    photos = {p["slug"]: p for p in content.PHOTOS}
    seq, order = layout.sequence("wide", colour, rend, quotes)
    keys = {w["key"]: w for w in content.WORKS}
    top_rows = 16
    tiles = []
    for item in seq:
        if isinstance(item, Band):
            if item.role == "title":
                tiles.append(title_room(built, colour, order))
            elif item.role == "statement":
                tiles.append(statement_room(item.id, built))
            else:
                tiles.append(exit_room(built))
        elif isinstance(item, Card):
            tiles.append(intro_room(built) if item.role == "intro" else quote_room(item.id, built, quotes, works))
        elif isinstance(item, Work):
            w = works[item.id[len("work-"):]]
            tiles.append(work_room(w, built, quotes))
            first = built["a"]["by_id"][item.photo.slug].y < top_rows
            tiles.append(photo_tile(photos[item.photo.slug], built, rend, colour, works, "high" if first else False, key_of=w))
        else:
            first = built["a"]["by_id"][item.slug].y < top_rows
            tiles.append(photo_tile(photos[item.slug], built, rend, colour, works, first))
    halls, nh, nt = hall_texts(built, quotes, works)
    print("  corridor lines placed: %d of %d" % (nh, nt), file=sys.stderr)
    lines, plans, walks = [], [], []
    for letter, _, _ in MAZES:
        lines.append(lines_svg(letter, built[letter]))
        walks.append(walk_json(letter, built[letter]))
        if letter != "c":
            plans.append(plan_svg(letter, built[letter], colour, works))
    rows = ";".join("--rows-%s:%d" % (l, built[l]["rows"]) for l in built)
    return ('<section class="maze" id="maze" style="%s" aria-label="%s">'
            '<div class="maze-inner">\n%s\n%s\n%s\n</div>'
            '<nav class="plan" aria-label="%s">%s<span class="plan-label" aria-hidden="true"></span></nav>'
            '%s\n%s</section>' % (rows, E(t("The work of United Notions Film, as a maze of pictures")), "\n".join(tiles), halls, "\n".join(lines),
                                  E(t("Plan of the maze")), "".join(plans), pad(), "\n".join(walks)))


# ---------------------------------------------------------------------------------------------- the list of works
def index_section(colour, rend, quotes):
    def entry(w):
        lang = title_lang(w)
        poster = w["poster"]
        r = rend[poster]
        press = ""
        if w.get("qkey"):
            items = []
            for q in quotes[w["qkey"]]["quotes"]:
                if not q.get("source"):
                    continue
                short = q["words"] <= 9
                items.append('<li><blockquote%s%s>“%s”</blockquote><cite>%s</cite></li>'
                             % (' class="is-short"' if short else "", QL, E(q["text"]), E(layout.source_name(q["source"]))))
            if w["slug"] == "las-awichas":
                jury = quotes["las-awichas"]["quotes"][0]
                items = ['<li><blockquote%s>“%s”</blockquote><cite>%s</cite></li>' % (QL, E(jury["text"]), E(t("Jury statement, AIDC Awards 2025")))]
            if items:
                press = '<ul class="entry-press">%s</ul>' % "".join(items)
        links = ['<a href="%s">%s</a>' % (E(w["href"]), E(w["cta"]))]
        if w.get("watch") and w["watch"][1] != w["href"]:
            links.append('<a href="%s">%s</a>' % (E(w["watch"][1]), E(w["watch"][0])))
        facts = "".join("<li>%s</li>" % E(f) for f in w["facts"])
        return ('<article class="entry" id="work-%s">'
                '<a class="entry-poster" href="%s" tabindex="-1" aria-hidden="true" style="--tone:%s"><img src="%s" srcset="%s" sizes="(min-width: 900px) 15vw, (min-width: 560px) 24vw, 32vw" width="%d" height="%d" alt="" loading="lazy" decoding="async"></a>'
                '<div class="entry-main"><p class="label">%s, %d</p><h4%s><a href="%s">%s</a></h4>'
                '<p class="line">%s</p><ul class="facts">%s</ul><p class="links">%s</p></div>%s</article>'
                % (w["slug"], E(w["href"]), colour[poster]["swatch"], src(rend, poster, 480), srcset(rend, poster), r["w"], r["h"],
                   E(w["kind"]), w["year"], lang, E(w["href"]), E(w["title"]), E(w["line"]), facts, "".join(links), press))
    films = "".join(entry(w) for w in content.WORKS if w["group"] == "film")
    xr = "".join(entry(w) for w in content.WORKS if w["group"] == "xr")
    return ('<section class="block" id="works"><h2 class="block-title">%s</h2>'
            '<div class="index-group"><h3>%s</h3>%s</div>'
            '<div class="index-group"><h3>%s</h3>%s</div></section>' % (E(t("Work")), E(t("Films")), films, E(t("Extended realities")), xr))


def now_section(colour, rend):
    rows = []
    for title, lang, where, action, href in content.NOW_SHOWING:
        l = ' lang="%s"' % (lang or "en") if (lang or "en") != i18n.LANG else ""
        rows.append('<li class="row"><h3%s><a href="%s">%s</a></h3><p class="where">%s</p><p class="act"><a href="%s">%s</a></p></li>'
                    % (l, E(href), E(title), E(where), E(href), E(action)))
    slug = "whale-and-robot"
    r = rend[slug]
    return ('<section class="block" id="now"><h2 class="block-title">%s</h2>'
            '<p class="block-lede">%s</p>'
            '<ul class="rows">%s</ul>'
            '<div class="coming"><figure style="--tone:%s"><img src="%s" srcset="%s" sizes="(min-width: 760px) 58vw, 100vw" width="%d" height="%d" loading="lazy" decoding="async" alt="%s"></figure>'
            '<div><h3>%s</h3><p class="name">Yakumama</p><p>%s</p></div></div>'
            '</section>' % (E(t("Now showing")), E(t("Where to watch the films and play the VR today.")), "".join(rows),
                            colour[slug]["swatch"], src(rend, slug, 1200), srcset(rend, slug), r["w"], r["h"],
                            E({p["slug"]: p for p in content.PHOTOS}[slug]["alt"]), E(t("Coming in 2026")),
                            E(t("A robotic whale installation. It is set to premiere at MozFest 2026 in Barcelona."))))


def lab_section():
    import research
    rows = []
    for n in research.latest(3):
        where = ", " + n["place"] if n["place"] else ""
        rows.append('<li class="row note"><p class="when"><time datetime="%s">%s</time>%s</p>'
                    '<h3><a href="research/%s.html">%s</a></h3><p class="sum">%s</p></li>'
                    % (n["iso"], E(i18n.date(n["iso"])), E(where), n["slug"], E(n["title"]), E(n["summary"])))
    return ('<section class="block" id="lab"><h2 class="block-title">%s</h2>'
            '<p class="block-lede">%s</p>'
            '<ul class="rows">%s</ul>'
            '<p class="more-link"><a href="research.html">%s</a></p></section>'
            % (E(t("From the lab")), E(t("The lab is in Cochabamba. It builds creatures that respond to bodies and environments in real time. These are its latest notes.")),
               "".join(rows), E(t("Read all the research notes"))))


def footer(colour, order, root=""):
    sw = "".join('<i style="--c:%s"></i>' % colour[s]["swatch"] for s in order)
    def li(label, href, note=""):
        return '<li><a href="%s">%s</a>%s</li>' % (href, E(label), note)
    studio = "".join([
        li(t("Work"), root + "index.html#works"), li(t("Now showing"), root + "index.html#now"), li(t("Film Futurism"), root + "film-futurism.html"),
        li(t("Research"), root + "research.html"), li(t("News"), root + "news.html"), li(t("About"), root + "about.html"),
        li(t("People"), root + "people.html"), li(t("For press and media"), root + "press.html")])
    wiki = "https://%s.wikipedia.org/wiki/" % ("es" if ES else "en")
    founders = (
        li("Violeta Ayala", root + "people/violeta-ayala.html", '<span><a href="https://www.violetaayala.com">violetaayala.com</a>, <a href="%sVioleta_Ayala">Wikipedia</a></span>' % wiki)
        + li("Dan Fallshaw", root + "people/dan-fallshaw.html", '<span><a href="https://danfallshaw.com">danfallshaw.com</a>, <a href="https://en.wikipedia.org/wiki/Dan_Fallshaw">Wikipedia</a></span>'))
    related = (li("sala.red", "https://sala.red", "<span>%s</span>" % E(t("Investigative tech journalism from Bolivia")))
               + li("sala.video", "https://sala.video/home.php", "<span>%s</span>" % E(t("Independent film distribution")))
               + li("koa.xyz", "https://koa.xyz", "<span>%s</span>" % E(t("Computational creativity lab"))))
    return ('<footer class="site-footer"><div class="palette" aria-hidden="true">%s</div><div class="footer-inner">'
            '<div class="footer-cols">'
            '<div><h2>%s</h2><ul>%s</ul></div>'
            '<div><h2>%s</h2><ul>%s</ul></div>'
            '<div><h2>%s</h2><ul>%s</ul></div>'
            '</div>'
            '<p class="billing">%s</p>'
            '<p class="colophon">\u00a9 2026 United Notions Film. %s {{LANG_FOOT}}</p>'
            '</div></footer>' % (sw, E(t("Studio")), studio, E(t("Founders")), founders, E(t("Related")), related,
                                 E(" ".join(content.STATEMENTS)), E(t("Bolivia and Australia, since 2006."))))


def header(root="", home=False, current=""):
    """The header. On small screens the links fold into a menu that fills the screen.
    {{LANG_LINK}} becomes the link to the same page in the other language (see page)."""
    def link(label, href):
        target = href[len("index.html"):] if home and href.startswith("index.html#") else root + href
        mark = ' aria-current="page"' if href == current else ""
        return '<li><a href="%s"%s>%s</a></li>' % (target, mark, E(label))
    main = "".join(link(label, href) for label, href in content_pages.NAV)
    more = link(t("Now showing"), "index.html#now") + link(t("For press and media"), "press.html")
    return ('<header class="site-header" data-header>'
            '<a class="wordmark" href="%sindex.html">United Notions Film</a>'
            '<nav class="site-nav" aria-label="%s"><ul>%s<li class="lang">{{LANG_LINK}}</li></ul></nav>'
            '<details class="menu" data-menu><summary><span class="when-closed">%s</span><span class="when-open">%s</span></summary>'
            '<nav aria-label="%s"><ul>%s%s<li class="lang">{{LANG_LINK}}</li></ul></nav></details>'
            '</header>' % (root, E(t("Main")), main, E(t("Menu")), E(t("Close")), E(t("Main, on a small screen")), main, more))


DESCRIPTION = t("United Notions Film is an award-winning film and creative technology studio based in Bolivia and Australia, "
                "founded in 2006 by Violeta Ayala and Dan Fallshaw. We make documentaries, virtual reality experiences and "
                "cinematic installations, and we run a lab that develops cinema systems, AI and robotics.")


def jsonld_home():
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": "https://unitednotions.film/#organization", "name": "United Notions Film", "alternateName": "UNF",
             "url": "https://unitednotions.film/", "description": DESCRIPTION, "foundingDate": "2006",
             "founder": [
                 {"@type": "Person", "name": "Violeta Ayala", "url": "https://www.violetaayala.com", "sameAs": ["https://en.wikipedia.org/wiki/Violeta_Ayala"]},
                 {"@type": "Person", "name": "Dan Fallshaw", "url": "https://danfallshaw.com", "sameAs": ["https://en.wikipedia.org/wiki/Dan_Fallshaw"]}],
             "location": [{"@type": "Place", "name": "Bolivia"}, {"@type": "Place", "name": "Australia"}]},
            {"@type": "WebSite", "@id": "https://unitednotions.film/#website", "url": "https://unitednotions.film/", "name": "United Notions Film",
             "inLanguage": ["en", "es"], "publisher": {"@id": "https://unitednotions.film/#organization"}},
            {"@type": "WebPage", "@id": HOME_URL + "#webpage", "url": HOME_URL, "name": "United Notions Film", "inLanguage": i18n.LANG,
             "isPartOf": {"@id": "https://unitednotions.film/#website"}, "about": {"@id": "https://unitednotions.film/#organization"}},
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


MARKS = {}
WRITTEN = []          # every page written in this run, as its file name inside the language (index.html, research/a-note.html)


def mark(*parts):
    """A short mark of what a file of the site holds. It goes behind the address of the stylesheet and the script,
    so the server may tell browsers to keep them for a year: when the file changes, its address changes."""
    key = "/".join(parts)
    if key not in MARKS:
        with open(os.path.join(SITE, *parts), "rb") as f:
            MARKS[key] = hashlib.md5(f.read()).hexdigest()[:8]
    return MARKS[key]


def page(title, description, path, body, root="", body_class="", extra_head="", og_image="assets/img/share.jpg"):
    """A whole page. path: the address of the page without the language and without .html ("" is the home page).
    Both languages share the folder assets, so in the Spanish pages every address of a file in assets climbs one folder more."""
    canonical = HOME_URL + path
    file = (path or "index") + ".html"
    here, there = i18n.LANG, i18n.other()
    to_other = (root + "es/" + file) if not ES else (root + "../" + file)
    name = "Español" if there == "es" else "English"
    lang_link = '<a href="%s" lang="%s" hreflang="%s">%s</a>' % (to_other, there, there, name)
    alternates = "\n".join('<link rel="alternate" hreflang="%s" href="%s">' % (code, SITE_URL + sub + path)
                           for code, sub in (("en", ""), ("es", "es/"), ("x-default", "")))
    out = """<!doctype html>
<html lang="%s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
%s
<meta property="og:type" content="website">
<meta property="og:site_name" content="United Notions Film">
<meta property="og:locale" content="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="https://unitednotions.film/%s">
<meta name="theme-color" content="#000000">
<link rel="icon" href="%sassets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="%sassets/img/apple-touch-icon.png">
<script>document.documentElement.className += " js";</script>
<link rel="stylesheet" href="%sassets/css/site.css?v=%s">
%s
</head>
<body class="%s">
%s
<script src="%sassets/js/site.js?v=%s" defer></script>
</body>
</html>
""" % (here, E(title), E(description), canonical, alternates, "es_BO" if ES else "en_AU", E(title), E(description), canonical, og_image,
       root, root, root, mark("assets", "css", "site.css"), extra_head, body_class, body, root, mark("assets", "js", "site.js"))
    out = out.replace("{{LANG_LINK}}", lang_link).replace("{{LANG_FOOT}}", lang_link)
    if ES:
        out = re.sub(r"""(?<=["' ,(])((?:\.\./)*)assets/""", lambda m: m.group(1) + "../assets/", out)
    return out


def write(path, out):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(out)
    if path.endswith(".html"):
        WRITTEN.append(path)
    print(("es/" if ES else "") + path, len(out) // 1024, "KB", file=sys.stderr)


def build_home():
    colour, rend, quotes, built = gather()
    order = built["a"]["order"]
    body = ('<a class="skip" href="#works">%s</a>'
            '<a class="skip" href="#maze" data-skip-walk>%s</a>\n' % (E(t("Skip to the list of works")), E(t("Walk the maze with the arrow keys")))
            + header(home=True) + "\n<main>\n"
            + maze_section(colour, rend, quotes, built) + "\n"
            + index_section(colour, rend, quotes) + "\n" + now_section(colour, rend) + "\n" + lab_section() + "\n</main>\n"
            + footer(colour, order))
    head = '<script type="application/ld+json">\n%s\n</script>' % jsonld_home()
    out = page(t("United Notions Film | Documentary, XR, AI and Immersive Experiences"), DESCRIPTION, "", body, body_class="home", extra_head=head)
    write("index.html", out)
    # keep the numbers of the mazes for anyone who wants to look
    dump = {l: dict(rows=built[l]["rows"], info=built[l]["info"],
                    rects=[dict(id=r.id, kind=r.kind, role=r.role, x=r.x, y=r.y, w=r.w, h=r.h) for r in built[l]["rects"]]) for l in built}
    json.dump(dump, open(os.path.join(HERE, "data", "maze%s.json" % ("-es" if ES else "")), "w"), indent=0)
    return colour, rend, quotes, built


# ---------------------------------------------------------------------------------------------- a film page
FILMS = {
    "la-lucha": dict(
        hero="lone-protester", hero_focus="62% 62%", trailer="oOwBoWMllWU", trailer_still="fence-banner",
        synopsis=("A group of people with disabilities in Bolivia unite in protest for a pension. They trek the Andes in their wheelchairs. "
                  "They confront a government that tries to silence them and a society indifferent to their struggle."),
        facts=[("Year", "2023"), ("Kind", "Feature documentary"), ("Length", "90 minutes"), ("Director", "Violeta Ayala"),
               ("Producers", "Redelia Shaw, Dan Fallshaw"), ("Production", "United Notions Film")],
        actions=[("Watch the film", "https://sala.video/film.php?slug=la-lucha"), ("Visit the film's website", "https://lalucha.red")],
        record=[("World premiere", "BlackStar Film Festival, Philadelphia, 2023"),
                ("Australian premiere", "SXSW Sydney, 2023"),
                ("New York premiere", "ReelAbilities Film Festival and the Museum of the Moving Image"),
                ("Award", "NYWIFT Award for Excellence in Directing"),
                ("Bolivian premiere", "The central plazas of Cochabamba, La Paz and Potosí, 2024, with sign language interpretation"),
                ("Broadcast", "PBS, 2024")],
        credits='<small>United Notions Film presents</small> <span lang="es">La Lucha</span> <small>directed by</small> Violeta Ayala <small>produced by</small> Redelia Shaw <small>and</small> Dan Fallshaw',
        related=("The same march, as a short film", "The Fight", "The short film of that same march, made in 2017. Released worldwide by The Guardian.",
                 [("Watch The Fight at The Guardian", "https://www.theguardian.com/world/ng-interactive/2017/may/05/fighting-for-a-pension-disability-rights-protesters-in-bolivia-face-barricades"),
                  ("See all the work", "../index.html#works")]),
        description="La Lucha (2023) is a feature documentary directed by Violeta Ayala. People with disabilities march across the Andes to La Paz to demand a pension. It premiered at BlackStar Film Festival and aired on PBS in 2024.",
        jsonld=dict(duration="PT90M", language="es", director="Violeta Ayala", producers=["Redelia Shaw", "Dan Fallshaw"], sameAs=["https://lalucha.red"]),
    ),
}


def stills_maze(slugs, colour, rend, seed=3, link_works=None, root="../"):
    """A small maze of pictures for a page of its own. No rooms, nobody walks it.
    The narrow version keeps its pictures as wide as the screen.
    link_works: when given, each picture links to its work on the home page."""
    import random
    from maze import Maze, Spec, pack
    photos = {p["slug"]: p for p in content.PHOTOS}
    built = {}
    for letter, name, _ in MAZES:
        L = layout.LAYOUTS[name]
        spec_args = dict(L["spec"])
        spec_args["tiers"] = {k: (a * 1.55, b * 1.6) for k, (a, b) in L["spec"]["tiers"].items()}
        spec_args["pass_w"] = 0
        spec_args["work_gap"] = 0
        spec = Spec(cols=L["cols"], **spec_args)
        seq = []
        for s in slugs:
            r = rend[s]
            seq.append(Photo(s, r["ow"] / r["oh"], "L" if photos[s]["tier"] != "S" else "M", maxw=max(spec.minw, r["ow"] // L["res"])))
        rects, rows, info = pack(seq, spec, tries=max(300, TRIES // 2), seed=seed)
        mz = Maze(rects, spec.cols, rows)
        mz.carve([], random.Random(seed * 31 + 7), thread=False, density=0.5)
        for extra in range(1, 6):
            if info["void"] <= spec.cols * 2:
                break
            # too much empty floor for a small wall: try other seeds
            r2, rows2, info2 = pack(seq, spec, tries=max(300, TRIES // 2), seed=seed + extra * 17)
            if info2["void"] < info["void"]:
                rects, rows, info = r2, rows2, info2
                mz = Maze(rects, spec.cols, rows)
                mz.carve([], random.Random(seed * 31 + 7), thread=False, density=0.5)
        built[letter] = dict(name=name, spec=spec, rects=rects, rows=rows, maze=mz, by_id={r.id: r for r in rects}, info=info)
        print("  stills %s: %d rows %s" % (letter, rows, info), file=sys.stderr)
    tiles = []
    for s in slugs:
        p = photos[s]
        r = rend[s]
        wa, wb, wc = built["a"]["by_id"][s].w, built["b"]["by_id"][s].w, built["c"]["by_id"][s].w
        sizes = "(min-width: 1920px) %dpx, (min-width: 1200px) %svw, (min-width: 700px) %svw, %svw" % (
            round(wa / 24 * 1920), num(wa / 24 * 100), num(wb / 16 * 100), num(wc / 12 * 100))
        style = place(built, s) + ";--tone:%s" % colour[s]["swatch"] + (";--focus:%s" % p["focus"] if p["focus"] else "")
        credit = ("<small>%s</small>" % E(t("Photo: %s") % p["credit"])) if p["credit"] else ""
        prefix = root + "assets/img/maze/"
        picture = ('<img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
                   % (src(rend, s, prefix=prefix), srcset(rend, s, prefix=prefix), sizes, r["w"], r["h"], E(content.caption(p))))
        label = ""
        w = link_works.get(p["work"]) if link_works else None
        if w:
            picture = '<a href="%sindex.html#%s">%s</a>' % (root, w["slug"], picture)
            label = "<b>%s, %d</b>" % (E(w["title"]), w["year"])
        tiles.append('<figure class="tile photo" style="%s">%s<figcaption>%s%s%s</figcaption></figure>' % (style, picture, label, E(content.caption(p)), credit))
    lines = [lines_svg(letter, built[letter]) for letter, _, _ in MAZES]
    rows = ";".join("--rows-%s:%d" % (l, built[l]["rows"]) for l in built)
    return ('<section class="maze no-plan film-maze" style="%s" aria-label="%s"><div class="maze-inner">\n%s\n%s\n</div></section>'
            % (rows, E(t("Pictures")), "\n".join(tiles), "\n".join(lines)))


def build_film(slug, colour, rend, quotes, order):
    w = work_by_slug()[slug]
    f = FILMS[slug]
    photos = {p["slug"]: p for p in content.PHOTOS}
    mine = [s for s in order if photos[s]["work"] == slug]
    hero = f["hero"]
    hr = rend[hero]
    lang = title_lang(w)
    sw = "".join('<i style="--c:%s"></i>' % colour[s]["swatch"] for s in mine)
    facts = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (E(t(k)), E(i18n.soft(v))) for k, v in f["facts"])
    actions = "".join('<a class="button" href="%s">%s</a>' % (E(h), E(t(label))) for label, h in f["actions"])
    press = []
    for q in quotes[w["qkey"]]["quotes"]:
        if not q.get("source"):
            continue
        press.append('<li%s><blockquote%s>“%s”</blockquote><cite>%s</cite></li>'
                     % (' class="is-long"' if q["words"] > 14 else "", QL, E(q["text"]), E(layout.source_name(q["source"]))))
    record = "".join('<li class="row"><p class="when">%s</p><h3 style="grid-column:4 / span 9">%s</h3></li>' % (E(t(k)), E(t(v))) for k, v in f["record"])
    ts = rend[f["trailer_still"]]
    rel_head, rel_title, rel_text, rel_links = f["related"]
    rel = "".join('<a href="%s">%s</a>' % (E(h), E(t(label))) for label, h in rel_links)
    body = ('<a class="skip" href="#film">%s</a>\n' % E(t("Skip to the text")) + header(root="../") + '\n<main>\n'
            '<div class="film-top"><figure class="film-frame photo-key" style="--tone:%s;--focus:%s">'
            '<img src="%s" srcset="%s" sizes="100vw" width="%d" height="%d" alt="%s" fetchpriority="high"></figure></div>\n'
            % (colour[hero]["swatch"], f["hero_focus"], src(rend, hero, 1200, "../assets/img/maze/"), srcset(rend, hero, "../assets/img/maze/"), hr["w"], hr["h"], E(photos[hero]["alt"])))
    body += ('<article id="film">'
             '<div class="film-head"><p class="label">%s, %d</p><h1 class="film-title"%s>%s</h1></div>'
             '<div class="palette film-palette" aria-hidden="true">%s</div>'
             '<div class="film-body"><p class="film-synopsis">%s</p><dl class="film-facts">%s</dl><p class="film-actions">%s</p></div>\n'
             % (E(w["kind"]), w["year"], lang, E(w["title"]), sw, E(t(f["synopsis"])), facts, actions))
    body += ('<section class="film-trailer" aria-label="%s"><a href="https://www.youtube.com/watch?v=%s" data-youtube="%s" data-title="%s" style="--tone:%s">'
             '<img src="%s" srcset="%s" sizes="100vw" width="%d" height="%d" alt="" loading="lazy" decoding="async"><span>%s</span></a></section>\n'
             % (E(t("Trailer")), f["trailer"], f["trailer"], E(t("%s, trailer") % w["title"]), colour[f["trailer_still"]]["swatch"],
                src(rend, f["trailer_still"], 1200, "../assets/img/maze/"),
                srcset(rend, f["trailer_still"], "../assets/img/maze/"), ts["w"], ts["h"], E(t("Play the trailer"))))
    body += '<section class="block"><h2 class="block-title">%s</h2><ul class="press">%s</ul></section>\n' % (E(t("Press")), "".join(press))
    body += stills_maze([s for s in mine if s not in (hero, f["trailer_still"])], colour, rend) + "\n"
    body += ('<section class="block"><h2 class="block-title">%s</h2><ul class="rows">%s</ul>'
             '<p class="credits">%s</p></section>\n' % (E(t("Premieres")), record, t(f["credits"])))
    body += '</article>\n'
    body += ('<section class="block" aria-labelledby="related-title"><h2 class="label" id="related-title">%s</h2>'
             '<p class="coming"><span class="name" style="grid-column:1 / -1">%s</span></p><p class="block-lede">%s</p><p class="entry"><span class="links" style="grid-column:1 / -1">%s</span></p></section>\n'
             % (E(t(rel_head)), E(rel_title), E(t(rel_text)), rel))
    body += '</main>\n' + footer(colour, order, root="../")
    j = f["jsonld"]
    data = {
        "@context": "https://schema.org", "@type": "Movie", "@id": "https://unitednotions.film/work/%s#movie" % slug,
        "name": w["title"], "url": HOME_URL + "work/%s" % slug, "description": w["line"], "genre": t("Documentary"),
        "dateCreated": str(w["year"]), "duration": j["duration"], "inLanguage": j["language"],
        "image": "https://unitednotions.film/assets/img/maze/%s-%d.webp" % (w["poster"], rend[w["poster"]]["widths"][-1]),
        "director": {"@type": "Person", "name": j["director"], "url": "https://www.violetaayala.com", "sameAs": ["https://en.wikipedia.org/wiki/Violeta_Ayala"]},
        "producer": [{"@type": "Person", "name": n} for n in j["producers"]],
        "productionCompany": {"@type": "Organization", "@id": "https://unitednotions.film/#organization", "name": "United Notions Film", "url": "https://unitednotions.film/"},
        "trailer": {"@type": "VideoObject", "name": t("%s, trailer") % w["title"], "url": "https://www.youtube.com/watch?v=%s" % f["trailer"], "embedUrl": "https://www.youtube.com/embed/%s" % f["trailer"]},
        "sameAs": j["sameAs"],
    }
    head = '<script type="application/ld+json">\n%s\n</script>' % json.dumps(data, indent=2, ensure_ascii=False)
    out = page("%s (%d) | United Notions Film" % (w["title"], w["year"]), t(f["description"]), "work/%s" % slug, body,
               root="../", body_class="film", extra_head=head,
               og_image="assets/img/maze/%s-%d.webp" % (hero, min(rend[hero]["widths"], key=lambda x: abs(x - 1200))))
    write("work/%s.html" % slug, out)


if __name__ == "__main__":
    colour, rend, quotes, built = build_home()
    build_film("la-lucha", colour, rend, quotes, built["a"]["order"])
    import pages
    pages.build_all(sys.modules[__name__], colour, rend, quotes, built["a"]["order"])
    import research
    research.build_all(sys.modules[__name__], colour, built["a"]["order"])
    import extras
    extras.build_all(sys.modules[__name__], colour, built["a"]["order"])
    if not ES:
        import captions_sheet
        captions_sheet.build(colour, rend, built["a"]["order"])
    i18n.report()
    if not ES and os.environ.get("UNF_ONLY") != "en":
        # the same site in Spanish: separate files, in the folder es
        subprocess.run([sys.executable, os.path.abspath(__file__)], env=dict(os.environ, UNF_LANG="es"), check=True)
