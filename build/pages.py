"""About, People (with a page for each person), News and Film Futurism.

Called from build.py. Texts are in content_pages.py.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from urllib.parse import urlparse

import content
import content_pages as CP
import i18n
import layout
import typo
from i18n import t

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
SITE_URL = "https://unitednotions.film/"
PAGE_URL = SITE_URL + ("es/" if i18n.LANG == "es" else "")       # the address of the pages in this language
QL = ' lang="en"' if i18n.LANG == "es" else ""

S = {}      # shared state: the build module, colours, picture sizes


def setup(B, colour, rend, quotes, order):
    S.update(B=B, colour=colour, rend=rend, quotes=quotes, order=order,
             prend=json.load(open(os.path.join(HERE, "data", "pages-renditions.json"))),
             manifest=json.load(open(os.path.join(HERE, "data", "pages-manifest.json"))),
             works={w["slug"]: w for w in content.WORKS})


# ---------------------------------------------------------------------------------------------- pictures
def pic(name, root, want=800):
    if name.startswith("maze:"):
        key = name[5:]
        r = S["rend"][key]
        prefix = root + "assets/img/maze/"
        tone = S["colour"][key]["swatch"]
    else:
        key = name
        r = S["prend"][name]
        prefix = root + "assets/img/pages/"
        tone = "#%02x%02x%02x" % tuple(r["mean"])
    w = min(r["widths"], key=lambda x: (abs(x - want), x))
    return dict(src="%s%s-%d.webp" % (prefix, key, w), big="%s%s-%d.webp" % (prefix, key, r["widths"][-1]),
                srcset=", ".join("%s%s-%d.webp %dw" % (prefix, key, x, x) for x in r["widths"]),
                w=r["w"], h=r["h"], tone=tone, aspect=r["w"] / r["h"])


def img(name, root, alt, sizes, want=800, eager=False):
    p = pic(name, root, want)
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return '<img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" %s>' % (p["src"], p["srcset"], sizes, p["w"], p["h"], E(alt), load)


def palette(tones):
    return '<div class="palette page-palette" aria-hidden="true">%s</div>' % "".join('<i style="--c:%s"></i>' % t for t in tones)


def fit_vw(text, most=21.0):
    """Font size in vw at which a one-line title fills the page width."""
    em = typo.width(text, "head", 1000, layout.TRACK_HEAD) / 1000.0
    return min(most, 94.0 / em * 0.975)


def head(title, lead=None, kicker=None, tones=(), most=21.0, lang=None, extra=""):
    k = '<p class="label kicker">%s</p>' % kicker if kicker else ""
    l = '<p class="page-lead">%s</p>' % E(lead) if lead else ""
    lg = ' lang="%s"' % lang if lang else ""
    return ('<div class="page-head">%s<h1 class="page-title" style="--fit:%svw"%s>%s</h1>%s%s%s</div>'
            % (k, S["B"].num(fit_vw(title, most)), lg, E(title), palette(tones) if tones else "", l, extra))


def write(path, out):
    S["B"].write(path, out)


def ld(data):
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(data, indent=2, ensure_ascii=False)


ORG = {"@type": "Organization", "@id": SITE_URL + "#organization", "name": "United Notions Film", "url": SITE_URL}


# ---------------------------------------------------------------------------------------------- about
def figure(name, alt, focus, root, sizes="(min-width: 900px) 40vw, 92vw"):
    if name.startswith("maze:"):
        # a picture of the maze carries the caption it has there: who, what, where and when
        alt = next((content.caption(ph) for ph in content.PHOTOS if ph["slug"] == name[5:]), alt)
    p = pic(name, root)
    cap_w = "min(calc(var(--pic-h) * %s), %dpx)" % (S["B"].num(p["aspect"]), p["w"])
    return ('<figure style="flex:%s 1 0%%;max-width:%s;--tone:%s">%s<figcaption>%s</figcaption></figure>'
            % (S["B"].num(p["aspect"]), cap_w, p["tone"], img(name, root, alt, sizes), E(alt)))


def build_about():
    B = S["B"]
    tones, years = [], []
    for year, paras, pics in CP.ABOUT:
        tones.extend(pic(n, "")["tone"] for n, _, _ in pics)
    for year, paras, pics in CP.ABOUT:
        body = "".join("<p>%s</p>" % E(t) for t in paras)
        if pics:
            body += '<div class="pics">%s</div>' % "".join(figure(n, alt, focus, "") for n, alt, focus in pics)
        years.append('<section class="year" id="y%s"><h2>%s</h2><div class="body">%s</div></section>' % (year, year, body))
    jump = '<p class="years" aria-label="%s">%s</p>' % (E(t("Years")), "".join('<a href="#y%s">%s</a>' % (y, y) for y, _, _ in CP.ABOUT))
    body = ('<a class="skip" href="#story">%s</a>\n' % E(t("Skip to the story")) + B.header(current="about.html") + '\n<main>\n'
            + head(t("About"), CP.ABOUT_LEAD, tones=tones, most=24, extra=jump)
            + '\n<div class="story" id="story">\n' + "\n".join(years) + '\n</div>\n'
            + '<section class="block onward"><p class="label">%s</p><p class="onward-links"><a href="people.html">%s</a><a href="film-futurism.html">%s</a><a href="index.html#works">%s</a></p></section>\n'
              % (E(t("Next")), E(t("The people")), E(t("Film Futurism")), E(t("The work")))
            + '</main>\n' + B.footer(S["colour"], S["order"]))
    data = {"@context": "https://schema.org", "@type": "AboutPage", "url": PAGE_URL + "about", "name": t("About United Notions Film"), "inLanguage": i18n.LANG,
            "description": CP.ABOUT_DESCRIPTION, "about": dict(ORG, foundingDate="2006")}
    write("about.html", B.page(t("About | United Notions Film"), CP.ABOUT_DESCRIPTION, "about", body, body_class="about", extra_head=ld(data)))


# ---------------------------------------------------------------------------------------------- people
def person_ld(p):
    same = [h for _, h in p["links"] if "unitednotions" not in h]
    data = {"@context": "https://schema.org", "@type": "Person", "@id": SITE_URL + "people/" + p["slug"] + "#person", "name": p["name"],
            "url": PAGE_URL + "people/" + p["slug"], "jobTitle": p["job"], "description": " ".join(p["bio"]), "worksFor": ORG, "sameAs": same}
    if p.get("base"):
        data["homeLocation"] = {"@type": "Place", "name": p["base"]}
    return data


def wall_pictures(work_slugs, most=12, chosen=None):
    """Pictures of a person's works for the wall on their page: the key picture of each work first.
    chosen: a list written by hand in content_pages.py wins."""
    if chosen:
        order = {s: i for i, s in enumerate(S["order"])}
        return sorted(chosen, key=lambda s: order.get(s, 999))
    by_work = {}
    for ph in content.PHOTOS:
        by_work.setdefault(ph["work"], []).append(ph["slug"])
    keys = {w["slug"]: w["key"] for w in content.WORKS}
    picked = [keys[s] for s in work_slugs if s in keys]
    rest = {s: [x for x in by_work.get(s, []) if x != keys.get(s) and not x.endswith("-poster")] for s in work_slugs}
    k = 0
    while len(picked) < most and any(rest.values()):
        s = work_slugs[k % len(work_slugs)]
        if rest[s]:
            picked.append(rest[s].pop(0))
        k += 1
    order = {s: i for i, s in enumerate(S["order"])}
    return sorted(picked[:most], key=lambda s: order.get(s, 999))


def build_people():
    B = S["B"]
    works = S["works"]
    # the index
    rows, tones = [], []
    for p in CP.PEOPLE:
        strip = pic(p["strip"], "")
        tones.append(strip["tone"])
        rows.append('<li class="person-row"><a class="strip" href="people/%s.html" tabindex="-1" aria-hidden="true" style="--tone:%s">%s</a>'
                    '<h2><a href="people/%s.html">%s</a></h2><div class="about-them"><p class="role">%s</p><p>%s</p></div></li>'
                    % (p["slug"], strip["tone"], img(p["strip"], "", "", "100vw", want=1200), p["slug"], E(p["name"]), E(p["role"]), E(p["bio"][0])))
    body = ('<a class="skip" href="#people">%s</a>\n' % E(t("Skip to the people")) + B.header(current="people.html") + '\n<main>\n'
            + head(t("People"), t("The people who make the films, the virtual reality, the installations and the lab."), most=24)
            + '\n<ul class="people" id="people">%s</ul>\n' % "".join(rows)
            + '</main>\n' + B.footer(S["colour"], S["order"]))
    data = {"@context": "https://schema.org", "@type": "ItemList", "name": t("The people of United Notions Film"),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": PAGE_URL + "people/" + p["slug"], "name": p["name"]} for i, p in enumerate(CP.PEOPLE)]}
    write("people.html", B.page(t("People | United Notions Film"), CP.PEOPLE_DESCRIPTION, "people", body, body_class="people-page", extra_head=ld(data)))

    # a page for each person
    n = len(CP.PEOPLE)
    for i, p in enumerate(CP.PEOPLE):
        root = "../"
        strip = pic(p["strip"], root)
        bio = '<p class="lead">%s</p>%s' % (E(p["bio"][0]), "".join("<p>%s</p>" % E(t) for t in p["bio"][1:]))
        links = "".join('<li><a href="%s">%s</a></li>' % (E(h), E(t)) for t, h in p["links"])
        credits = []
        for slug in p["works"]:
            w = works[slug]
            lang = B.title_lang(w)
            credits.append('<li><a href="%sindex.html#%s"%s>%s</a><span>%s, %d</span></li>' % (root, slug, lang, E(w["title"]), E(w["kind"]), w["year"]))
        mine = wall_pictures(p["works"], chosen=p.get("wall"))
        wall = B.stills_maze(mine, S["colour"], S["rend"], seed=5 + i, link_works=works, root=root)
        prev, nxt = CP.PEOPLE[(i - 1) % n], CP.PEOPLE[(i + 1) % n]
        pager = ('<nav class="pager" aria-label="%s"><a href="%s.html"><span class="label">%s</span>%s</a>'
                 '<a href="../people.html"><span class="label">%s</span>%s</a>'
                 '<a href="%s.html"><span class="label">%s</span>%s</a></nav>'
                 % (E(t("More people")), prev["slug"], E(t("Before")), E(prev["name"]), E(t("Everyone")), E(t("People")), nxt["slug"], E(t("Next")), E(nxt["name"])))
        extra = ""
        if p.get("embed") and os.path.exists(os.path.join(B.SITE, "assets", "embeds", p["embed"][0] + ".html")):
            extra = ('<section class="block person-embed"><h2 class="label">%s</h2><div class="embed"><iframe src="%sassets/embeds/%s.html" title="%s" loading="lazy"></iframe></div>'
                     '<p class="more-link"><a href="%sresearch/%s.html">%s</a></p></section>\n'
                     % (E(t(p["embed"][1])), root, p["embed"][0], E(t(p["embed"][1])), root, p["embed"][2], E(t("Read the lab note"))))
        wall_tones = [S["colour"][s]["swatch"] for s in mine]
        body = ('<a class="skip" href="#bio">%s</a>\n' % E(t("Skip to the text")) + B.header(root=root, current="people.html") + '\n<main>\n'
                + head(p["name"], kicker='<a href="../people.html">%s</a>' % E(t("People")), most=21)
                + '\n<p class="person-role">%s</p>' % E(p["role"])
                + '\n<figure class="person-strip" style="--tone:%s">%s</figure>' % (strip["tone"], img(p["strip"], root, t("%s, in five pictures.") % p["name"], "100vw", want=1200, eager=True))
                + palette(wall_tones)
                + '\n<div class="person-body" id="bio"><div class="bio">%s</div>'
                  '<aside><h2 class="label">%s</h2><ul class="plain-links">%s</ul>'
                  '<h2 class="label">%s</h2><ul class="credit-list">%s</ul></aside></div>\n'
                  % (bio, E(t("Elsewhere")), links, E(t("Work with United Notions Film")), "".join(credits))
                + wall + "\n" + extra + pager + '\n</main>\n' + B.footer(S["colour"], S["order"], root=root))
        write("people/%s.html" % p["slug"],
              B.page("%s | United Notions Film" % p["name"], " ".join(p["bio"])[:300], "people/" + p["slug"], body,
                     root=root, body_class="person", extra_head=ld(person_ld(p))))


# ---------------------------------------------------------------------------------------------- news
def outlet(link):
    if not link:
        return ""
    for part, name in CP.OUTLET_BY_PATH:
        if part in link:
            return name
    host = urlparse(link).netloc.lower()
    host = re.sub(r"^(www|amp|m|edition|shows)\.", "", host)
    return CP.OUTLETS.get(host, host)


def build_news():
    B = S["B"]
    works = S["works"]
    by_key = {}
    for m in S["manifest"]:
        by_key.setdefault(m["key"], []).append(m)
    sections, jump, tones, total, linked = [], [], [], 0, 0
    for key, slug in CP.NEWS_ORDER:
        w = works[slug]
        clips = by_key.get(key, [])
        lang = B.title_lang(w)
        items = []
        for m in clips:
            p = pic(m["name"], "", want=480)
            tones.append(p["tone"])
            name = outlet(m["link"])
            alt = (t("Press clipping: %s, on %s.") % (name, w["title"])) if name else t("Press clipping on %s.") % w["title"]
            picture = img(m["name"], "", alt, "(min-width: 1200px) 18vw, (min-width: 700px) 30vw, 46vw", want=480)
            total += 1
            if m["link"]:
                linked += 1
                items.append('<li style="--tone:%s"><a href="%s" rel="noopener">%s<span class="outlet">%s</span></a></li>' % (p["tone"], E(m["link"]), picture, E(name)))
            else:
                items.append('<li style="--tone:%s">%s</li>' % (p["tone"], picture))
        note = layout.work_note(w, S["quotes"])
        quote = ('<blockquote class="press-quote"%s><p>“%s”</p><cite>%s</cite></blockquote>' % (QL, E(note["text"]), E(note["source"]))) if note["kind"] == "quote" else ""
        sections.append('<section class="press-work" id="press-%s"><header><p class="label">%s</p>'
                        '<h2%s><a href="index.html#%s">%s</a></h2>%s</header><ul class="clips">%s</ul></section>'
                        % (slug, E(t("%s, %d. %d clippings.") % (w["kind"], w["year"], len(clips))), lang, slug, E(w["title"]), quote, "".join(items)))
        jump.append('<li><a href="#press-%s"%s>%s</a> <span>%d</span></li>' % (slug, lang, E(w["title"]), len(clips)))
    extra = '<ul class="jump" aria-label="%s">%s</ul>' % (E(t("Works")), "".join(jump))
    lead = t("What the press wrote about each work. %d clippings. %d of them open the article.") % (total, linked)
    body = ('<a class="skip" href="#press">%s</a>\n' % E(t("Skip to the clippings")) + B.header(current="news.html") + '\n<main>\n'
            + head(t("News"), lead, tones=tones, most=24, extra=extra)
            + '\n<div id="press">\n' + "\n".join(sections) + '\n</div>\n</main>\n' + B.footer(S["colour"], S["order"]))
    data = {"@context": "https://schema.org", "@type": "CollectionPage", "url": PAGE_URL + "news", "name": t("News and press, United Notions Film"),
            "description": CP.NEWS_DESCRIPTION, "inLanguage": i18n.LANG, "publisher": ORG}
    write("news.html", B.page(t("News | United Notions Film"), CP.NEWS_DESCRIPTION, "news", body, body_class="news", extra_head=ld(data)))
    return total, linked


# ---------------------------------------------------------------------------------------------- film futurism
def build_futurism():
    B = S["B"]
    notes = []
    for n in CP.FF_NOTES:
        lang = ' lang="%s"' % n["lang"] if n.get("lang") and n["lang"] != i18n.LANG else ""
        parts = ['<h3%s>%s</h3>' % (lang, E(n["title"]))]
        parts += ["<p>%s</p>" % E(t) for t in n["text"]]
        if n.get("list"):
            parts.append('<h4 class="label">%s</h4><ul class="dash">%s</ul>' % (E(n["list"][0]), "".join("<li>%s</li>" % E(x) for x in n["list"][1])))
        if n.get("quote"):
            parts.append('<blockquote><p>“%s”</p><cite>%s</cite></blockquote>' % (E(n["quote"][0]), E(n["quote"][1])))
        if n.get("signed"):
            parts.append('<p class="signed">%s</p>' % E(n["signed"]))
        if n.get("links"):
            parts.append('<p class="links">%s</p>' % "".join('<a href="%s">%s</a>' % (E(h), E(t)) for t, h in n["links"]))
        picture = ""
        if n.get("picture"):
            name, alt = n["picture"]
            p = pic(name, "")
            picture = '<figure style="--tone:%s">%s</figure>' % (p["tone"], img(name, "", alt, "(min-width: 900px) 30vw, 92vw"))
        notes.append('<article class="note-card"><div class="words">%s</div>%s</article>' % ("".join(parts), picture))
    record = sorted(CP.FF_RECORD, key=lambda r: r[1], reverse=True)
    tones = [pic(r[4], "")["tone"] for r in record]
    years = {}
    for when, key, title, place, card in record:
        years.setdefault(key[:4], []).append((when, title, place, card))
    blocks = []
    for year in sorted(years, reverse=True):
        cards = []
        for when, title, place, card in years[year]:
            p = pic(card, "", want=480)
            alt = t("Card made by the studio: %s. %s") % (title, when) if when else t("Card made by the studio: %s.") % title
            cards.append('<li><a class="card" href="%s" style="--tone:%s">%s</a><p class="when">%s</p><h4>%s</h4>%s</li>'
                         % (p["big"], p["tone"], img(card, "", alt, "(min-width: 1200px) 22vw, (min-width: 700px) 30vw, 92vw", want=480),
                            E(when or year), E(title), ('<p class="place">%s</p>' % E(place)) if place else ""))
        blocks.append('<div class="rec-year" id="r%s"><h3>%s</h3><ul class="cards">%s</ul></div>' % (year, year, "".join(cards)))
    definition = '<div class="ff-def"><p class="statement">%s</p><div class="rest">%s</div></div>' % (
        E(CP.FF_STATEMENT), "".join("<p>%s</p>" % E(t) for t in CP.FF_DEFINITION))
    body = ('<a class="skip" href="#now">%s</a>\n' % E(t("Skip to the text")) + B.header(current="film-futurism.html") + '\n<main>\n'
            + head(t("Film Futurism"), tones=tones, most=21) + definition
            + '\n<section class="block" id="now"><h2 class="block-title">%s</h2><div class="note-cards">%s</div></section>' % (E(t("Now")), "".join(notes))
            + '\n<section class="block" id="record"><h2 class="block-title">%s</h2>'
              '<p class="block-lede">%s</p>%s</section>'
              % (E(t("The record")), E(t("%d moments, from %s to %s. The studio made a card for each one at the time. Open a card to read it.") % (len(record), min(years), max(years))),
                 "".join(blocks))
            + '\n</main>\n' + B.footer(S["colour"], S["order"]))
    data = {"@context": "https://schema.org", "@type": "WebPage", "url": PAGE_URL + "film-futurism", "name": t("Film Futurism, United Notions Film"),
            "description": CP.FF_DESCRIPTION, "inLanguage": i18n.LANG, "publisher": ORG}
    write("film-futurism.html", B.page(t("Film Futurism | United Notions Film"), CP.FF_DESCRIPTION, "film-futurism", body, body_class="futurism", extra_head=ld(data)))


def build_press():
    """For press and media: what the studio can give a journalist, and who to write to."""
    B = S["B"]
    pics = [n for n in ("press-page-01", "press-page-02", "press-page-03") if n in S["prend"]]
    figures = "".join('<figure style="flex:%s 1 0%%;--tone:%s">%s</figure>' % (B.num(pic(n, "")["aspect"]), pic(n, "")["tone"],
                      img(n, "", t(CP.PRESS_PICTURES.get(n, "")), "(min-width: 900px) 46vw, 92vw")) for n in pics)
    def column(title, items):
        return '<div><h2 class="label">%s</h2><ul class="dash">%s</ul></div>' % (E(t(title)), "".join("<li>%s</li>" % E(t(x)) for x in items))
    user, host = CP.PRESS_CONTACT
    body = ('<a class="skip" href="#press">%s</a>\n' % E(t("Skip to the text")) + B.header(current="press.html") + '\n<main>\n'
            + head(t("Press"), t(CP.PRESS_LEAD), tones=[pic(n, "")["tone"] for n in pics], most=24)
            + ('\n<div class="press-pics pics">%s</div>' % figures if figures else "")
            + '\n<section class="block press-kit" id="press"><div class="press-cols">%s%s</div>'
              '<div class="press-contact"><p class="label">%s</p><p class="mail"><a href="mailto:%s@%s">%s<span>@</span>%s</a></p><p>%s</p></div></section>'
              % (column("What we can provide", CP.PRESS_PROVIDE), column("What we can talk about", CP.PRESS_TOPICS),
                 E(t("Write to us")), user, host, user, host, E(t(CP.PRESS_CONTACT_NOTE)))
            + '\n<section class="block onward"><p class="label">%s</p><p class="onward-links"><a href="news.html">%s</a><a href="index.html#works">%s</a><a href="people.html">%s</a></p></section>'
              % (E(t("See also")), E(t("News")), E(t("The work")), E(t("The people")))
            + '\n</main>\n' + B.footer(S["colour"], S["order"]))
    data = {"@context": "https://schema.org", "@type": "ContactPage", "url": PAGE_URL + "press", "name": t("For press and media, United Notions Film"),
            "description": t(CP.PRESS_DESCRIPTION), "inLanguage": i18n.LANG, "publisher": ORG}
    write("press.html", B.page(t("For press and media | United Notions Film"), t(CP.PRESS_DESCRIPTION), "press", body, body_class="press-page", extra_head=ld(data)))


def build_all(B, colour, rend, quotes, order):
    setup(B, colour, rend, quotes, order)
    build_about()
    build_people()
    total, linked = build_news()
    build_futurism()
    build_press()
    print("  news: %d clippings, %d with a link" % (total, linked), file=sys.stderr)
