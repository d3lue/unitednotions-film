"""The files a live site needs beside its pages.

    robots.txt       who may read the site, and where its map is
    sitemap.xml      every page in both languages, each one pointing at its twin in the other language
    llms.txt         a guide to the site for language models. es/llms.txt is the same guide in Spanish
    404.html         the page that answers a wrong address. es/404.html answers in Spanish
    .htaccess        the rules for the Apache server at DreamHost: short addresses, the addresses of the old site, caching

Called at the end of build.py, once for each language.
The addresses written here are the public ones, without .html: https://unitednotions.film/about
The server shows about.html for them. That is the work of .htaccess.
"""
from __future__ import annotations

import html
import os
import posixpath
import re

import i18n
from i18n import t

E = html.escape


def public(path):
    """The public address of a page: index.html -> "", about.html -> about, research/a-note.html -> research/a-note"""
    p = path[:-5] if path.endswith(".html") else path
    return "" if p == "index" else p


def put(B, folder, name, text):
    with open(os.path.join(folder, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    shown = os.path.relpath(os.path.join(folder, name), B.SITE)
    print(shown, max(1, len(text.encode("utf-8")) // 1024), "KB", file=__import__("sys").stderr)


# ---------------------------------------------------------------------------------------------- robots.txt
ROBOTS = """# United Notions Film
# https://unitednotions.film
#
# This site is open to every reader: people, search engines, archives and AI systems.
# A guide for language models is at /llms.txt in English and at /es/llms.txt in Spanish.

User-agent: *
Allow: /

Sitemap: %ssitemap.xml
"""


def robots(B):
    put(B, B.SITE, "robots.txt", ROBOTS % B.SITE_URL)


# ---------------------------------------------------------------------------------------------- sitemap.xml
NOT_IN_THE_MAP = ("404.html",)


def sitemap(B):
    """Both languages hold the same pages, so each page is listed twice, and each entry names both."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n']
    n = 0
    for path in B.WRITTEN:
        if path in NOT_IN_THE_MAP:
            continue
        p = public(path)
        en, es = B.SITE_URL + p, B.SITE_URL + "es/" + p
        twins = "".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (code, E(u))
                        for code, u in (("en", en), ("es", es), ("x-default", en)))
        for u in (en, es):
            out.append("  <url>\n    <loc>%s</loc>\n%s  </url>\n" % (E(u), twins))
            n += 1
    out.append("</urlset>\n")
    put(B, B.SITE, "sitemap.xml", "".join(out))
    return n


# ---------------------------------------------------------------------------------------------- llms.txt
def one_line(text):
    return " ".join(text.split())


def beyond_the_kind(line, kind):
    """The line of a work without a first sentence that only says what kind of work it is: the guide has just said it."""
    first, dot, rest = line.partition(". ")
    said = re.sub(r"^(an?|una?|el|la) ", "", first.lower()).rstrip(".")
    return rest if dot and said == kind.lower() else line


def llms(B, content, CP, research):
    """A guide in Markdown, in the shape llmstxt.org describes: a title, a summary in a quote, some notes,
    then lists of links under second-level headings. The heading "Optional" keeps its English name in both
    languages: tools read it as "these links can be left out when space is short"."""
    U = B.HOME_URL
    other = B.SITE_URL + ("llms.txt" if B.ES else "es/llms.txt")
    L = []
    add = L.append
    add("# United Notions Film")
    add("")
    add("> " + one_line(content.INTRO + " " + content.INTRO_MORE))
    add("")
    add(" ".join(content.STATEMENTS))
    add("")
    add("- " + t("United Notions Film is also written UNF."))
    add("- " + t("Huk is an ongoing project. Huk the Jaguaress (2025) is one work within it. They are two names for two things."))
    add("- " + t("This site exists in English and in Spanish, with the same pages in each. This guide covers the English pages. The Spanish guide is at %s.") % other)
    add("- " + t("Every page is plain HTML and reads without scripts. The addresses in this guide are the public ones."))
    add("")

    add("## " + t("Work"))
    add("")
    for w in content.WORKS:
        url = U + (public(w["href"]) if not w["href"].startswith("http") else "#" + w["slug"])
        facts = " ".join(w["facts"])
        add("- [%s](%s): %s, %d. %s %s" % (w["title"], url, w["kind"], w["year"], beyond_the_kind(w["line"], w["kind"]), facts))
    add("- [Yakumama](%s#now): %s. %s" % (U, t("Coming in 2026"), t("A robotic whale installation. It is set to premiere at MozFest 2026 in Barcelona.")))
    add("")

    add("## " + t("Now showing"))
    add("")
    for title, lang, where, action, href in content.NOW_SHOWING:
        add("- [%s](%s): %s" % (action, href, where))
    add("")

    add("## " + t("Studio"))
    add("")
    add("- [%s](%sabout): %s" % (t("About"), U, one_line(CP.ABOUT_DESCRIPTION)))
    add("- [%s](%speople): %s" % (t("People"), U, one_line(CP.PEOPLE_DESCRIPTION)))
    for p in CP.PEOPLE:
        add("- [%s](%speople/%s): %s" % (p["name"], U, p["slug"], p["role"]))
    add("- [%s](%sfilm-futurism): %s" % (t("Film Futurism"), U, one_line(CP.FF_DESCRIPTION)))
    add("- [%s](%snews): %s" % (t("News"), U, one_line(CP.NEWS_DESCRIPTION)))
    add("- [%s](%spress): %s" % (t("For press and media"), U, one_line(t(CP.PRESS_DESCRIPTION))))
    add("")

    notes = research.load()
    add("## " + t("Lab notes"))
    add("")
    add("- [%s](%sresearch): %s" % (t("Research"), U, one_line(t(research.DESCRIPTION))))
    for n in notes:
        when = research.when(n)
        add("- [%s](%sresearch/%s): %s%s" % (n["title"], U, n["slug"], (when + ". ") if when else "", one_line(n["summary"])))
    add("")

    news = research.news_pages()
    if news:
        add("## " + t("News"))
        add("")
        for n in news:
            when = research.when(n)
            add("- [%s](%snews/%s): %s%s" % (n["title"], U, n["slug"], (when + ". ") if when else "", one_line(n["summary"])))
        add("")

    add("## Optional")
    add("")
    add("- [sala.red](https://sala.red): %s" % t("Investigative tech journalism from Bolivia"))
    add("- [sala.video](https://sala.video/home.php): %s" % t("Independent film distribution"))
    add("- [koa.xyz](https://koa.xyz): %s" % t("Computational creativity lab"))
    add("- [violetaayala.com](https://www.violetaayala.com): %s" % t("The site of Violeta Ayala"))
    add("- [danfallshaw.com](https://danfallshaw.com): %s" % t("The site of Dan Fallshaw"))
    add("- [%s](%s): %s" % (t("United Notions Film in Spanish"), other, t("The guide for the Spanish pages")))
    text = "\n".join(L) + "\n"
    assert "—" not in text and "–" not in text, "a long dash in llms.txt"
    put(B, B.OUT, "llms.txt", text)
    return text


# ---------------------------------------------------------------------------------------------- 404.html
def from_the_root(page, base):
    """A wrong address can sit at any depth, so the page that answers it names its files from the top of the site."""
    def fix(m):
        attr, value = m.group(1), m.group(2)
        if not value or value.startswith(("#", "/", "http:", "https:", "mailto:", "data:")):
            return m.group(0)
        cut = min([i for i in (value.find("#"), value.find("?")) if i >= 0] or [len(value)])
        path, tail = value[:cut], value[cut:]
        return '%s="%s%s"' % (attr, posixpath.normpath(posixpath.join(base, path)) + ("/" if path.endswith("/") else ""), tail)
    return re.sub(r'\b(href|src|poster)="([^"]*)"', fix, page)


def not_found(B, colour, order):
    import pages
    lead = t("This address leads nowhere. The page has moved or the address has an error.")
    body = ('<a class="skip" href="#lost">%s</a>\n' % E(t("Skip to the text")) + B.header() + '\n<main>\n'
            + pages.head("404", lead, most=24)
            + '\n<section class="block onward" id="lost"><p class="label">%s</p><p class="onward-links">'
              '<a href="index.html">%s</a><a href="index.html#works">%s</a><a href="research.html">%s</a><a href="news.html">%s</a><a href="people.html">%s</a></p></section>'
              % (E(t("From here")), E(t("The maze")), E(t("The work")), E(t("Research")), E(t("News")), E(t("The people")))
            + '\n</main>\n' + B.footer(colour, order))
    page = B.page(t("Page not found | United Notions Film"), t("This address does not exist at United Notions Film."), "404", body, body_class="lost-page")
    # it is nobody's twin and it is not for search engines
    page = re.sub(r'<link rel="(?:canonical|alternate)"[^>]*>\n', "", page)
    page = re.sub(r'<meta property="og:url"[^>]*>\n', "", page)
    page = page.replace('<meta name="viewport" content="width=device-width, initial-scale=1">',
                        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="robots" content="noindex">', 1)
    base = "/es/" if B.ES else "/"
    page = from_the_root(page, base)
    # the other language: its home page, since a wrong address has no twin
    page = page.replace('href="/es/404.html"', 'href="/es/"').replace('href="/404.html"', 'href="/"')
    B.write("404.html", page)


# ---------------------------------------------------------------------------------------------- .htaccess
HTACCESS = """# United Notions Film. Rules for the Apache server at DreamHost.
#
# This file is named .htaccess and sits beside index.html. Its name starts with a dot, so a Mac hides it.
# If the site answers "500 Internal Server Error" after an upload, one line here is not allowed on that server.
# Put a # in front of the lines of one block at a time until the site comes back. Start with the block OPTIONS.

# ---- OPTIONS: no list of files for a folder, no guessing of file names
Options -Indexes -MultiViews
# research and people are each a page and a folder. The server must not add a / to them by itself.
# The rules under SHORT ADDRESSES add the / where a folder needs it.
<IfModule mod_dir.c>
  DirectorySlash Off
</IfModule>

# ---- TEXT: every text file is UTF-8, so Spanish letters arrive whole
AddDefaultCharset utf-8
<IfModule mod_mime.c>
  AddCharset utf-8 .html .css .js .txt .xml .svg .json
  AddType image/webp .webp
  AddType image/svg+xml .svg
  AddType font/woff2 .woff2
  AddType video/mp4 .mp4
</IfModule>

# ---- A WRONG ADDRESS: the page that answers it. The folder es has its own, in Spanish.
ErrorDocument 404 /404.html

<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /

  # ---- NOT FOR THE PUBLIC: the workshop and the notes to ourselves, in case they are uploaded by mistake
  RewriteRule ^(build(/.*)?|README\\.txt|FOR-DAN\\.txt|htaccess\\.txt|robots-no-ai-training\\.txt)$ - [R=404,L]

  # ---- THE OLD SITE: its addresses lead to the new pages
  RewriteRule ^for-press-media/?$ /press [R=301,L]
  RewriteRule ^research-archive/?$ /research [R=301,L]
  RewriteRule ^updates/?$ /research [R=301,L]
  RewriteRule ^updates/([^/]+)/?$ /research/$1 [R=301,L]
  RewriteRule ^(films|xr)/?$ /#works [R=301,NE,L]
  RewriteRule ^now-playing/?$ /#now [R=301,NE,L]
  RewriteRule ^news/huk/?$ /news#press-huk-the-jaguaress [R=301,NE,L]
  RewriteRule ^news/awichas/?$ /news#press-las-awichas [R=301,NE,L]
  RewriteRule ^news/prisonx/?$ /news#press-prison-x [R=301,NE,L]
  RewriteRule ^news/(cocaine-prison|the-fight|the-bolivian-case|stolen)/?$ /news#press-$1 [R=301,NE,L]
  # These two pages of the old site are not built yet. Until they are, their addresses lead home.
  RewriteRule ^(birdbot|educational-collection)/?$ / [R=302,L]

  # ---- SHORT ADDRESSES: /about shows about.html, /research/a-note shows research/a-note.html
  # research, people and news are each a page and a folder: the page wins
  RewriteRule ^(es/)?(research|people|news)/$ /$1$2 [R=301,L]
  RewriteRule ^(es/)?(research|people|news)$ $1$2.html [L]
  # the folder work has no page of its own: the list of works on the home page answers
  RewriteRule ^work/?$ /#works [R=302,NE,L]
  RewriteRule ^es/work/?$ /es/#works [R=302,NE,L]
  # any other folder asked for without its / gets it
  RewriteCond %{REQUEST_FILENAME} -d
  RewriteRule ^(.*[^/])$ /$1/ [R=301,L]
  # an address that ends in / and is not a folder loses the /
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule ^(.+)/$ /$1 [R=301,L]
  # the rule itself: when there is a file with that name and .html, show it
  RewriteCond %{REQUEST_URI} !\\.html$
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{DOCUMENT_ROOT}/$1.html -f [OR]
  RewriteCond %{REQUEST_FILENAME}.html -f
  RewriteRule ^(.+)$ $1.html [L]
</IfModule>

# ---- KEEPING: how long a browser may keep a file before it asks again
# The stylesheet and the script carry a mark in their address (?v=...) that changes when they change, so a year is safe.
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresDefault "access plus 10 minutes"
  ExpiresByType text/html "access plus 10 minutes"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType image/webp "access plus 30 days"
  ExpiresByType image/jpeg "access plus 30 days"
  ExpiresByType image/png "access plus 30 days"
  ExpiresByType image/svg+xml "access plus 30 days"
  ExpiresByType image/x-icon "access plus 30 days"
  ExpiresByType image/vnd.microsoft.icon "access plus 30 days"
  ExpiresByType video/mp4 "access plus 30 days"
</IfModule>

# ---- SMALLER: text travels compressed
<IfModule mod_deflate.c>
  <IfModule mod_filter.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/css text/javascript application/javascript application/json application/xml text/xml image/svg+xml
  </IfModule>
</IfModule>

# ---- TWO SMALL PROTECTIONS for visitors
<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
"""

HTACCESS_ES = """# The Spanish pages answer a wrong address in Spanish.
# The other rules come from the .htaccess one folder up. This file holds nothing else on purpose.
ErrorDocument 404 /es/404.html
"""


def htaccess(B):
    put(B, B.SITE, ".htaccess", HTACCESS)
    os.makedirs(os.path.join(B.SITE, "es"), exist_ok=True)
    put(B, os.path.join(B.SITE, "es"), ".htaccess", HTACCESS_ES)


# ---------------------------------------------------------------------------------------------- all of it
def build_all(B, colour, order):
    import content
    import content_pages as CP
    import research
    not_found(B, colour, order)
    llms(B, content, CP, research)
    if not B.ES:
        robots(B)
        n = sitemap(B)
        htaccess(B)
        print("  sitemap: %d addresses" % n, file=__import__("sys").stderr)
