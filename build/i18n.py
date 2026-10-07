"""Two languages. English is written in the code and in the content files. Spanish is looked up in strings_es.py.

    python3 build/build.py                 builds the English site, then the Spanish one in /es
    UNF_LANG=es python3 build/build.py     builds only the Spanish site

The Spanish pages are separate files with the same names, inside the folder es.
A sentence that has no Spanish yet stays in English and is listed at the end of the build.
"""
import os

LANG = os.environ.get("UNF_LANG", "en")
ES = {}
if LANG == "es":
    from strings_es import ES      # noqa: F401
MISSING = []

MONTHS = {
    "en": ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "es": ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
}


def t(text):
    """The same sentence in the language of this build."""
    if LANG == "en" or not text:
        return text
    found = ES.get(text)
    if found is None:
        if text not in MISSING:
            MISSING.append(text)
        return text
    return found


def soft(text):
    """Like t, for values that are often names: nothing is reported when there is no Spanish."""
    return ES.get(text, text) if LANG != "en" else text


def date(iso):
    """2026-06-02 -> 2 June 2026 / 2 de junio de 2026. A month or a year alone also works."""
    parts = iso.split("-")
    m = MONTHS[LANG]
    if len(parts) == 3:
        return ("%d %s %s" if LANG == "en" else "%d de %s de %s") % (int(parts[2]), m[int(parts[1])], parts[0])
    if len(parts) == 2:
        month = m[int(parts[1])]
        return ("%s %s" % (month, parts[0])) if LANG == "en" else ("%s de %s" % (month.capitalize(), parts[0]))
    return iso


def other():
    return "es" if LANG == "en" else "en"


def localise_content(content, pages):
    """Put the texts of content.py and content_pages.py in the language of this build."""
    if LANG == "en":
        return
    for w in content.WORKS:
        for k in ("kind", "line", "cta", "award"):
            if w.get(k):
                w[k] = t(w[k])
        w["facts"] = [t(f) for f in w["facts"]]
        if w.get("watch"):
            w["watch"] = (t(w["watch"][0]), w["watch"][1])
    studio = getattr(content, "STUDIO_WROTE", set())
    for p in content.PHOTOS:
        if p["slug"] not in studio:
            p["alt"] = t(p["alt"])
    for k in list(content.WHERE):
        if k not in studio:
            content.WHERE[k] = t(content.WHERE[k])
    for k in list(content.MADE):
        content.MADE[k] = t(content.MADE[k])
    for k, (label, href) in list(content.OTHER_LINKS.items()):
        content.OTHER_LINKS[k] = (t(label), href)
    content.STATEMENTS[:] = [t(s) for s in content.STATEMENTS]
    content.INTRO, content.INTRO_MORE, content.HOW_TO_WALK = t(content.INTRO), t(content.INTRO_MORE), t(content.HOW_TO_WALK)
    content.NOW_SHOWING[:] = [(title, lang, t(where), t(action), href) for title, lang, where, action, href in content.NOW_SHOWING]

    pages.NAV[:] = [(t(label), href) for label, href in pages.NAV]
    for name in ("ABOUT_DESCRIPTION", "ABOUT_LEAD", "PEOPLE_DESCRIPTION", "FF_DESCRIPTION", "FF_STATEMENT", "NEWS_DESCRIPTION"):
        setattr(pages, name, t(getattr(pages, name)))
    pages.ABOUT[:] = [(year, [t(x) for x in paras], [(n, t(alt), focus) for n, alt, focus in pics]) for year, paras, pics in pages.ABOUT]
    for p in pages.PEOPLE:
        p["role"], p["job"] = t(p["role"]), t(p["job"])
        p["bio"] = [t(x) for x in p["bio"]]
        p["links"] = [(t(label), href) for label, href in p["links"]]
        if p.get("base"):
            p["base"] = t(p["base"])
    pages.FF_DEFINITION[:] = [t(x) for x in pages.FF_DEFINITION]
    for n in pages.FF_NOTES:
        if not n.get("lang"):
            n["title"] = t(n["title"])
        n["text"] = [t(x) for x in n["text"]]
        if n.get("quote"):
            n["quote"] = (t(n["quote"][0]), t(n["quote"][1]))
        if n.get("list"):
            n["list"] = (t(n["list"][0]), [t(x) for x in n["list"][1]])
        n["links"] = [(t(label), href) for label, href in n.get("links", [])]
        if n.get("picture"):
            n["picture"] = (n["picture"][0], t(n["picture"][1]))
    pages.FF_RECORD[:] = [(t(when), key, t(title), t(place), card) for when, key, title, place, card in pages.FF_RECORD]


def report():
    if LANG != "en" and MISSING:
        print("\n%d sentences have no Spanish yet:" % len(MISSING))
        for s in MISSING:
            print("    %r: \"\"," % s)
