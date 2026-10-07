"""The research pages: the list of the lab notes and a page for each note.

Texts     build/research/<language>/<note>.txt     one block per line (the tags are explained in research_import.py)
Notes     build/data/research.json                 date, place, pictures and videos of each note
Pictures  build/data/research-renditions.json      the web copies in assets/img/research (made by build/make_research_media.py)
Videos    assets/video/research/                   a video file that is not there is left out of the page
Embeds    assets/embeds/                           things that sit in a page, such as the carousel of Huk's poses

Called from build.py.
"""
from __future__ import annotations

import html
import html as html_mod
import json
import os
import re
import sys

import i18n
from i18n import t

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
S = {}

TEXT_TAGS = ("P", "+", "H", "LI", "A", "CAP")
MEDIA_TAGS = ("IMG", "VID", "MISSING-VIDEO", "VIDEO")     # VIDEO is the name for a new note; MISSING-VIDEO is the same thing, named when the old site still held the file


# ---------------------------------------------------------------------------------------------- reading
def read_blocks(slug, lang=None):
    lang = lang or i18n.LANG
    path = os.path.join(HERE, "research", lang, slug + ".txt")
    if not os.path.exists(path):
        if lang != "en":
            print("  no %s text for the note %s: the English text is used" % (lang, slug), file=sys.stderr)
        path = os.path.join(HERE, "research", "en", slug + ".txt")
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        tag, _, text = line.partition(":")
        out.append((tag.strip(), text.strip()))
    return out


def read_page(n):
    """A note written as a whole HTML page, in build/pages-in/<slug>/: index.html, and es.html for the Spanish when there is one.
    The page's own title, description and styles are kept. Its <body> becomes the body of the note."""
    folder = os.path.join(HERE, "pages-in", n["slug"])
    path = os.path.join(folder, "es.html" if i18n.LANG == "es" else "index.html")
    if not os.path.exists(path):
        if i18n.LANG != "en":
            print("  no %s page for the note %s: the English page is used" % (i18n.LANG, n["slug"]), file=sys.stderr)
        path = os.path.join(folder, "index.html")
    html = open(path, encoding="utf-8", errors="replace").read()

    def meta(name):
        m = re.search(r'<meta\s+name=["\']%s["\']\s+content=["\']([^"\']*)["\']' % name, html, re.I) or \
            re.search(r'<meta\s+content=["\']([^"\']*)["\']\s+name=["\']%s["\']' % name, html, re.I)
        return html_mod.unescape(m.group(1).strip()) if m else ""

    def text(tag, source):
        m = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), source, re.I | re.S)
        return html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()) if m else ""

    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.I | re.S)
    body = m.group(1) if m else re.sub(r"(?is)<head>.*?</head>|<!doctype[^>]*>|</?html[^>]*>", "", html)
    head_part = html[:m.start()] if m else ""
    styles = "".join(re.findall(r"<style[^>]*>.*?</style>", head_part, re.I | re.S))
    title = text("h1", body) or text("title", html) or n["title"]
    body = re.sub(r"<h1[^>]*>.*?</h1>", "", body, count=1, flags=re.I | re.S)        # the layout shows the title
    n["title"], n["page_title"] = title, title
    n["description"] = meta("description") or text("p", body)
    n["summary"] = n["description"]
    n["blocks"] = []
    n["html_body"] = styles + body.strip()
    n["html_folder"] = folder


def page_body(n, root):
    """The body of a dropped page, with its own files pointed at assets/pages/<slug>/."""
    folder, prefix = n["html_folder"], root + "assets/pages/" + n["slug"] + "/"

    def fix(m):
        attr, quote, target = m.group(1), m.group(2), m.group(3)
        file = target.split("?")[0].split("#")[0]
        if file and os.path.exists(os.path.join(folder, file)) and file.lower() not in ("index.html", "es.html"):
            return "%s=%s%s%s%s" % (attr, quote, prefix, target, quote)
        return m.group(0)
    body = re.sub(r"""\b(src|href|poster|srcset)=(["'])(?!https?:|//|/|#|data:|mailto:|tel:)([^"']+)\2""", fix, n["html_body"], flags=re.I)
    body = re.sub(r"""(url\()(["']?)(?!https?:|//|/|data:)([^"')]+)\2(\))""",
                  lambda m: "%s%s%s%s%s%s" % (m.group(1), m.group(2), prefix if os.path.exists(os.path.join(folder, m.group(3).split("?")[0])) else "", m.group(3), m.group(2), m.group(4)),
                  body, flags=re.I)
    return body



def load():
    if S.get("notes"):
        return S["notes"]
    notes = json.load(open(os.path.join(HERE, "data", "research.json"), encoding="utf-8"))
    for n in notes:
        if n.get("html"):
            read_page(n)
            continue
        blocks = read_blocks(n["slug"])
        head = {tag: text for tag, text in blocks[:3]}
        n["title"], n["description"], n["summary"] = head.get("T", n["title"]), head.get("D", ""), head.get("S", "")
        n["blocks"] = blocks[3:]
    for n in notes:
        n.setdefault("section", "research")
    notes.sort(key=lambda n: (n["iso"] + "-99")[:10], reverse=True)
    S["all"] = notes                                                  # lab notes and the pages added to News
    S["notes"] = [n for n in notes if n["section"] != "news"]
    path = os.path.join(HERE, "data", "research-renditions.json")
    S["rr"] = json.load(open(path)) if os.path.exists(path) else {}
    path = os.path.join(HERE, "data", "research-videos.json")
    S["vv"] = json.load(open(path)) if os.path.exists(path) else {}
    path = os.path.join(HERE, "research", "alts.json")
    S["alts"] = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    for n in notes:
        # a new note lists no pictures in research.json: the web copies made from build/picture-in count instead
        k = len(n["images"])
        while S["rr"].get("%s-%02d" % (n["key"], k + 1)):
            k += 1
        n["images"] = n["images"] + ["picture-in"] * (k - len(n["images"]))
    return S["notes"]


def news_pages():
    """The pages added on the editing page with News as their section, newest first."""
    load()
    return [n for n in S["all"] if n["section"] == "news"]


def latest(k):
    """The newest lab notes, for the home page."""
    return load()[:k]


def when(n):
    """Date and place, as one line."""
    d = i18n.date(n["iso"]) if n["iso"] else ""
    return ", ".join(x for x in (d, n["place"]) if x)


def asset_file(*parts):
    """Is this file of the folder assets there? Both languages share the folder."""
    return os.path.exists(os.path.join(S["B"].SITE, "assets", *parts))


# ---------------------------------------------------------------------------------------------- text
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def href(address, root):
    if address.startswith("note:"):
        return "%sresearch/%s.html" % (root, address[5:])
    return address


def inline(text, root):
    """Escape a line and turn [text](address) into links."""
    out, last = [], 0
    for m in LINK.finditer(text):
        out.append(E(text[last:m.start()]))
        address = href(m.group(2), root)
        outside = ' rel="noopener"' if address.startswith("http") else ""
        out.append('<a href="%s"%s>%s</a>' % (E(address), outside, E(m.group(1))))
        last = m.end()
    out.append(E(text[last:]))
    return "".join(out)


# ---------------------------------------------------------------------------------------------- pictures and videos
def rendition(name):
    return S["rr"].get(name)


def tone(r):
    return "#%02x%02x%02x" % tuple(r["mean"]) if r and r.get("mean") else "#111"


def picture(n, k, root, sizes, want=960, eager=False):
    """The img element of picture k of a note, or None when its web copy has not been made yet."""
    name = "%s-%02d" % (n["key"], k)
    r = rendition(name)
    if not r or "error" in r:
        S["waiting"].add(name)
        return None
    prefix = root + "assets/img/research/"
    w = min(r["widths"], key=lambda x: (abs(x - want), x))
    alt = (S["alts"].get(n["slug"], {}).get(str(k), {}) or {}).get(i18n.LANG) or t("Picture from the lab note “%s”.") % n["title"]
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    tag = ('<img src="%s%s-%d.webp" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" %s>'
           % (prefix, name, w, ", ".join("%s%s-%d.webp %dw" % (prefix, name, x, x) for x in r["widths"]), sizes, r["w"], r["h"], E(alt), load))
    return dict(img=tag, big="%s%s-%d.webp" % (prefix, name, r["widths"][-1]), aspect=r["w"] / r["h"], w=r["w"], tone=tone(r))


def still_name(key, file):
    """The name of the still of a video. make_research_media.py uses the same rule."""
    stem = file.rsplit(".", 1)[0]
    return "%s-poster-%s" % (key, stem[len(key) + 1:] if stem.startswith(key + "-") else stem[:8])


def video(n, file, root, ratio=None):
    """A short video kept in assets/video/research. Returns None when the file is not there."""
    if not asset_file("video", "research", file):
        S["no_video"].append((n["slug"], file))
        return None
    info = S["vv"].get(file, {})
    w, h = info.get("w"), info.get("h")
    if not (w and h) and ratio:
        a, _, b = ratio.partition(":")
        w, h = int(a), int(b)
    aspect = (w / h) if (w and h) else 9 / 16
    still = still_name(n["key"], file)
    poster = rendition(still)
    p = ' poster="%sassets/img/research/%s-%d.webp"' % (root, still, poster["widths"][-1]) if poster and "error" not in poster else ""
    size = ' width="%d" height="%d"' % (w, h) if (w and h) else ""
    # a clip of a few seconds plays by itself, silently and in a loop, while it is on screen; a longer video waits for the visitor
    clip = info.get("dur", 99) <= 6
    mode = ' muted loop playsinline data-clip preload="none"' if clip else ' playsinline preload="none"'
    tag = '<video src="%sassets/video/research/%s" controls%s%s%s style="aspect-ratio:%s"></video>' % (root, file, mode, size, p, S["B"].num(aspect))
    return dict(img=tag, big=None, aspect=aspect, w=w or 720, tone=tone(poster))


def figure(item, caption, link=None):
    inner = item["img"]
    target = link or item.get("big")
    if target:
        outside = ' rel="noopener"' if link else ""
        inner = '<a href="%s"%s>%s</a>' % (E(target), outside, inner)
    cap = "<figcaption>%s</figcaption>" % caption if caption else ""
    tall = " class=\"tall\"" if item["aspect"] < 0.8 else ""
    return dict(html='<figure%s style="flex:%s 1 0%%;--tone:%s">%s%s</figure>' % (tall, S["B"].num(item["aspect"]), item["tone"], inner, cap),
                aspect=item["aspect"], w=item["w"])


def shots(figs, most=3.3):
    """Pictures and videos that follow each other stand side by side, all as tall as each other.
    A row never holds more than fits: the rest goes to the next row."""
    rows, cur, total = [], [], 0.0
    for f in figs:
        if cur and total + f["aspect"] > most:
            rows.append(cur)
            cur, total = [], 0.0
        cur.append(f)
        total += f["aspect"]
    if cur:
        rows.append(cur)
    out = []
    for row in rows:
        total = sum(f["aspect"] for f in row)
        cap = ";--most:%dpx" % sum(f["w"] for f in row) if len(row) == 1 else ""
        out.append('<div class="shots" style="--sum:%s;--n:%d%s">%s</div>' % (S["B"].num(total), len(row), cap, "".join(f["html"] for f in row)))
    return "".join(out)


def play_link(kind, ident, title, label):
    """A video or a slide deck kept somewhere else. Nothing is loaded from there until the visitor asks."""
    address = {"youtube": "https://www.youtube.com/watch?v=%s", "vimeo": "https://vimeo.com/%s", "frame": "%s"}[kind] % ident
    return ('<p class="play"><a href="%s" data-%s="%s" data-title="%s" rel="noopener"><span>%s</span><b>%s</b></a></p>'
            % (E(address), kind, E(ident), E(title), E(label), E(title)))


# ---------------------------------------------------------------------------------------------- one note
def body_of(n, root):
    """The blocks of a note as HTML."""
    if n.get("html_body") is not None:
        return page_body(n, root)
    B = S["B"]
    out, blocks, i = [], n["blocks"], 0
    sizes_one = "(min-width: 900px) 62vw, 92vw"
    sizes_row = "(min-width: 900px) 36vw, 92vw"
    while i < len(blocks):
        tag, text = blocks[i]
        if tag == "P":
            lines = [inline(text, root)]
            while i + 1 < len(blocks) and blocks[i + 1][0] == "+":
                i += 1
                lines.append(inline(blocks[i][1], root))
            out.append("<p>%s</p>" % "<br>".join(lines))
        elif tag == "+":
            out.append("<p>%s</p>" % inline(text, root))
        elif tag == "H":
            out.append("<h2>%s</h2>" % inline(text, root))
        elif tag == "LI":
            items = [inline(text, root)]
            while i + 1 < len(blocks) and blocks[i + 1][0] == "LI":
                i += 1
                items.append(inline(blocks[i][1], root))
            out.append('<ul class="dash">%s</ul>' % "".join("<li>%s</li>" % x for x in items))
        elif tag == "A":
            label, _, address = text.rpartition(" | ")
            address = href(address.strip(), root)
            outside = ' rel="noopener"' if address.startswith("http") else ""
            out.append('<p class="links"><a href="%s"%s>%s</a></p>' % (E(address), outside, E(label.strip())))
        elif tag in MEDIA_TAGS:
            # pictures and videos that follow each other stand side by side
            run = []
            while i < len(blocks) and blocks[i][0] in MEDIA_TAGS + ("CAP",):
                run.append(blocks[i])
                i += 1
            i -= 1
            figs = []
            many = sum(1 for g, _ in run if g != "CAP") > 1
            for j, (g, x) in enumerate(run):
                if g == "CAP":
                    continue
                cap = inline(run[j + 1][1], root) if j + 1 < len(run) and run[j + 1][0] == "CAP" else ""
                if g == "IMG":
                    k, _, link = x.partition(" | ")
                    item = picture(n, int(k), root, sizes_row if many else sizes_one)
                    if item:
                        figs.append(figure(item, cap, link.strip() or None))
                elif g == "VID":
                    item = video(n, x, root)
                    if item:
                        figs.append(figure(item, cap))
                else:
                    ident, _, ratio = x.partition(" | ")
                    item = video(n, "%s-%s.mp4" % (n["key"], ident.strip()), root, ratio.strip())
                    if item:
                        figs.append(figure(item, cap))
            if figs:
                out.append(shots(figs))
        elif tag == "CAP":
            out.append('<p class="cap">%s</p>' % inline(text, root))     # a caption whose picture is not there yet
        elif tag == "GAL":
            items = []
            for k in text.split():
                item = picture(n, int(k), root, "(min-width: 1200px) 22vw, (min-width: 700px) 30vw, 46vw", want=480)
                if item:
                    items.append('<li style="--tone:%s"><a href="%s">%s</a></li>' % (item["tone"], item["big"], item["img"]))
            if items:
                cap = ""
                if i + 1 < len(blocks) and blocks[i + 1][0] == "CAP":
                    i += 1
                    cap = '<p class="cap">%s</p>' % inline(blocks[i][1], root)
                out.append('<ul class="gallery">%s</ul>%s' % ("".join(items), cap))
        elif tag in ("YT", "VM"):
            ident, _, title = text.partition(" | ")
            out.append(play_link("youtube" if tag == "YT" else "vimeo", ident.strip(), title.strip(), t("Play the video")))
        elif tag == "EMBED":
            name, address, title = [x.strip() for x in (text.split("|") + ["", ""])[:3]]
            if name == "slides" and address:
                out.append(play_link("frame", address, title or t("Slides"), t("Open the slides")))
            elif asset_file("embeds", name + ".html"):
                label = t(EMBED_TITLES.get(name, "Interactive"))
                out.append('<div class="embed"><iframe src="%sassets/embeds/%s.html" title="%s" loading="lazy"></iframe></div>' % (root, name, E(label)))
            else:
                S["no_embed"].append(name)
        i += 1
    return "\n".join(out)


EMBED_TITLES = {"jaguaress-skeleton-widget": "Huk: the 24 poses by Brian Condori"}


def short(text, most=300):
    """A description for search engines: whole sentences, not much longer than they show."""
    if len(text) <= most:
        return text
    cut = text[:most]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[:end + 1] if end > 80 else cut.rsplit(" ", 1)[0] + "…"


def note_page(n, newer, older):
    B = S["B"]
    root = "../"
    P = S["P"]
    news = n["section"] == "news"
    folder = "news" if news else "research"
    kicker, kind = (t("News"), t("Update")) if news else (t("Research"), t("Lab note"))
    every, more = (t("All the news"), t("More news")) if news else (t("Every note"), t("More notes"))
    tones = [tone(rendition("%s-%02d" % (n["key"], k + 1))) for k in range(len(n["images"])) if rendition("%s-%02d" % (n["key"], k + 1))]
    date = '<time datetime="%s">%s</time>' % (n["iso"], E(i18n.date(n["iso"]))) if n["iso"] else ""
    meta = "".join("<li>%s</li>" % x for x in (date, E(n["place"]), E(kind)) if x)
    body = body_of(n, root)
    pager = '<nav class="pager" aria-label="%s">%s<a href="../%s.html"><span class="label">%s</span>%s</a>%s</nav>' % (
        E(more),
        ('<a href="%s.html"><span class="label">%s</span>%s</a>' % (newer["slug"], E(t("Newer")), E(newer["title"]))) if newer else "<span></span>",
        folder, E(every), E(kicker),
        ('<a href="%s.html"><span class="label">%s</span>%s</a>' % (older["slug"], E(t("Older")), E(older["title"]))) if older else "<span></span>")
    out = ('<a class="skip" href="#note">%s</a>\n' % E(t("Skip to the text")) + B.header(root=root, current=folder + ".html") + '\n<main>\n'
           '<article class="lab-note">'
           '<header class="note-head"><p class="label kicker"><a href="../%s.html">%s</a></p>'
           '<h1 class="note-title">%s</h1>%s<p class="page-lead">%s</p></header>\n'
           '<div class="note-wrap"><aside class="note-meta"><ul class="label">%s</ul></aside>\n'
           '<div class="note-body" id="note">\n%s\n</div></div>'
           '</article>\n%s\n</main>\n'
           % (folder, E(kicker), E(n["title"]), P.palette(tones) if len(tones) >= 3 else "", E(n["summary"]), meta, body, pager)
           + B.footer(S["colour"], S["order"], root=root))
    first = rendition("%s-01" % n["key"]) if n["images"] else None
    url = B.HOME_URL + folder + "/" + n["slug"]
    data = {"@context": "https://schema.org", "@type": "Article", "@id": url + "#article", "headline": n["title"], "name": n["title"],
            "description": n["description"] or n["summary"], "abstract": n["summary"], "url": url, "mainEntityOfPage": url, "inLanguage": i18n.LANG,
            "author": [{"@type": "Organization", "@id": B.SITE_URL + "#organization", "name": "United Notions Film"}],
            "publisher": {"@type": "Organization", "@id": B.SITE_URL + "#organization", "name": "United Notions Film", "url": B.SITE_URL},
            "isPartOf": {"@type": "CollectionPage", "@id": B.HOME_URL + folder + "#collection", "name": kicker, "url": B.HOME_URL + folder},
            "articleSection": t("News") if news else t("Lab notes")}
    if n["iso"]:
        data["datePublished"] = n["iso"]
    if n["place"]:
        data["locationCreated"] = {"@type": "Place", "name": n["place"]}
    og = "assets/img/share.jpg"
    if first and "error" not in first:
        og = "assets/img/research/%s-01-%d.webp" % (n["key"], first["widths"][-1])
        data["image"] = B.SITE_URL + og
    B.write("%s/%s.html" % (folder, n["slug"]),
            B.page("%s | United Notions Film" % n["title"], short(n["description"] or n["summary"]), folder + "/" + n["slug"], out,
                   root=root, body_class="lab", extra_head=S["P"].ld(data), og_image=og))


# ---------------------------------------------------------------------------------------------- the list
LEAD = ("The lab is in Cochabamba. It builds creatures, sensors and worlds that respond to bodies, environments, memory and emotion in real time. "
        "These notes are its archive: experiments, failures and breakthroughs.")
DESCRIPTION = ("United Notions Film researches new forms of cinema across screen, space and code. The lab notes cover film futurism, "
               "computational creativity, XR, feminist AI, nonhuman characters, access and distribution.")


def row(n, folder, tones, root=""):
    """One note or page as a row of a list: date and place, title, summary, and its first picture when it has one."""
    thumb = ""
    if n["images"]:
        item = picture(n, 1, root, "(min-width: 760px) 22vw, 92vw", want=480)
        if item:
            tones.append(item["tone"])
            thumb = '<a class="thumb" href="%s%s/%s.html" tabindex="-1" aria-hidden="true" style="--tone:%s">%s</a>' % (root, folder, n["slug"], item["tone"], item["img"])
    date = ('<time datetime="%s">%s</time>' % (n["iso"], E(i18n.date(n["iso"])))) if len(n["iso"]) > 4 else ""
    line = ", ".join(x for x in (date, E(n["place"])) if x)
    return ('<li class="row note%s"><p class="when">%s</p><h3><a href="%s%s/%s.html">%s</a></h3><p class="sum">%s</p>%s</li>'
            % (" has-pic" if thumb else "", line, root, folder, n["slug"], E(n["title"]), E(n["summary"]), thumb))


def news_rows(tones):
    """The pages added to News, as rows for the News page. pages.py calls this before build_all has run."""
    S.setdefault("waiting", set())
    return [row(n, "news", tones) for n in news_pages()]


def index_page():
    B, P = S["B"], S["P"]
    notes = load()
    years, tones = {}, []
    for n in notes:
        years.setdefault(n["iso"][:4] or "", []).append(n)
    sections = []
    for year in sorted(years, reverse=True):
        rows = [row(n, "research", tones) for n in years[year]]
        sections.append('<section class="lab-year" id="y%s"><h2>%s</h2><ul class="rows">%s</ul></section>' % (year, year, "".join(rows)))
    jump = '<p class="years" aria-label="%s">%s</p>' % (E(t("Years")), "".join(
        '<a href="#y%s">%s <span>%d</span></a>' % (y, y, len(years[y])) for y in sorted(years, reverse=True)))
    lead = t(LEAD)
    body = ('<a class="skip" href="#notes">%s</a>\n' % E(t("Skip to the notes")) + B.header(current="research.html") + '\n<main>\n'
            + P.head(t("Research"), lead, tones=tones, most=24, extra=jump)
            + '\n<div class="lab-list" id="notes">\n' + "\n".join(sections) + '\n</div>\n</main>\n' + B.footer(S["colour"], S["order"]))
    url = B.HOME_URL + "research"
    data = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": url + "#collection", "url": url, "name": t("Research, United Notions Film"),
            "description": t(DESCRIPTION), "inLanguage": i18n.LANG, "publisher": P.ORG,
            "hasPart": [dict({"@type": "Article", "headline": n["title"], "url": url + "/" + n["slug"]}, **({"datePublished": n["iso"]} if n["iso"] else {})) for n in notes]}
    B.write("research.html", B.page(t("Research | United Notions Film"), t(DESCRIPTION), "research", body, body_class="lab-index", extra_head=P.ld(data)))


def build_all(B, colour, order):
    import pages as P
    S.update(B=B, P=P, colour=colour, order=order, waiting=S.get("waiting", set()), no_video=[], no_embed=[])
    notes = load()
    index_page()
    for i, n in enumerate(notes):
        note_page(n, notes[i - 1] if i else None, notes[i + 1] if i + 1 < len(notes) else None)
    print("  research: %d notes" % len(notes), file=sys.stderr)
    news = news_pages()
    for i, n in enumerate(news):
        note_page(n, news[i - 1] if i else None, news[i + 1] if i + 1 < len(news) else None)
    if news:
        print("  news: %d pages added on the editing page" % len(news), file=sys.stderr)
    if S["waiting"]:
        print("  %d pictures of the notes have no web copy yet (run build/make_research_media.py)" % len(S["waiting"]), file=sys.stderr)
    if S["no_video"]:
        print("  %d videos of the notes are not in assets/video/research: they are left out (build/fetch_lab_videos.py brings them from the old site)"
              % len(S["no_video"]), file=sys.stderr)
    json.dump(dict(pictures=sorted(S["waiting"]), videos=S["no_video"], embeds=S["no_embed"]),
              open(os.path.join(HERE, "data", "research-missing.json"), "w"), indent=1)
