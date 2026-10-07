"""Visitors: a private page about the site's visitors, made from the server's own access log.

    python3 build/visitors.py          on the server, every quarter hour, from cron

It reads ~/logs/unitednotions.film/https/access.log from where it left off last time, keeps one small summary per day
in ~/unf-workshop/stats/days/ (counts only: no addresses, no names, nothing that identifies a person), and writes
the page ~/unitednotions.film/edit/visitors/index.html, which the editing page's password protects.
Nothing is added to the site for this: no script, no cookie, no third party. Countries come from the free
address-to-country list of DB-IP (db-ip.com, CC BY 4.0), downloaded to the server once a month; no address leaves the server. DreamHost keeps only the current day's
log, so the history on the page begins the day this started running. Days are the server's days (US Pacific time).
"""
import bisect
import gzip
import hashlib
import html
import ipaddress
import json
import os
import pickle
import re
import time
import urllib.request
from collections import Counter
from datetime import date, timedelta

HOME = os.environ.get("VISITORS_HOME") or os.path.expanduser("~")
LOGS = [os.path.join(HOME, "logs", "unitednotions.film", "https", "access.log"),
        os.path.join(HOME, "logs", "unitednotions.film", "http", "access.log")]
SITE = os.path.join(HOME, "unitednotions.film")
STATS = os.path.join(HOME, "unf-workshop", "stats")
DAYS = os.path.join(STATS, "days")
STATE = os.path.join(STATS, "state.json")
GEO = os.path.join(STATS, "geo")            # the address-to-country list of DB-IP, one file a month
OUT = os.path.join(SITE, "edit", "visitors", "index.html")

E = html.escape
LINE = re.compile(r'^(\S+) \S+ (\S+) \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d{3}) (\S+) "([^"]*)" "([^"]*)"')
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}

# who asked: AI assistants and their crawlers, then search engines and link previews, then any other robot, else a person
AI = [("Claude-SearchBot", "Claude (search)"), ("Claude-User", "Claude (on request)"), ("ClaudeBot", "Claude (index)"), ("anthropic-ai", "Anthropic"),
      ("OAI-SearchBot", "ChatGPT (search)"), ("ChatGPT-User", "ChatGPT (on request)"), ("GPTBot", "ChatGPT (index)"),
      ("Perplexity-User", "Perplexity (on request)"), ("PerplexityBot", "Perplexity (index)"), ("Google-Extended", "Gemini"),
      ("meta-externalagent", "Meta AI"), ("Bytespider", "ByteDance (TikTok)"), ("Amazonbot", "Amazon (Alexa)"), ("Applebot-Extended", "Apple AI"),
      ("CCBot", "Common Crawl"), ("cohere-ai", "Cohere"), ("Diffbot", "Diffbot"), ("DuckAssistBot", "DuckDuckGo AI"), ("YouBot", "You.com"),
      ("MistralAI-User", "Mistral"), ("Timpibot", "Timpi"), ("omgili", "Webz.io")]
CRAWLERS = [("Google-InspectionTool", "Google"), ("GoogleOther", "Google"), ("AdsBot-Google", "Google"), ("Googlebot", "Google"),
            ("bingbot", "Bing"), ("DuckDuckBot", "DuckDuckGo"), ("Applebot", "Apple"), ("YandexBot", "Yandex"), ("Baiduspider", "Baidu"),
            ("facebookexternalhit", "Facebook (link preview)"), ("Twitterbot", "X (link preview)"), ("LinkedInBot", "LinkedIn (link preview)"),
            ("Slackbot", "Slack (link preview)"), ("WhatsApp", "WhatsApp (link preview)"), ("TelegramBot", "Telegram (link preview)"),
            ("Discordbot", "Discord (link preview)"), ("Pinterestbot", "Pinterest"), ("SemrushBot", "Semrush"), ("AhrefsBot", "Ahrefs"),
            ("MJ12bot", "Majestic"), ("DotBot", "Moz"), ("PetalBot", "Petal"), ("archive.org_bot", "Internet Archive"), ("ia_archiver", "Internet Archive"),
            ("SeznamBot", "Seznam"), ("Qwantify", "Qwant"), ("Sogou", "Sogou")]
OTHER_ROBOT = re.compile(r"bot|crawl|spider|slurp|fetch|scrap|python|wget|go-http|java/|okhttp|libwww|httpclient|headless|phantom|lighthouse|"
                         r"pingdom|uptime|monitor|dataforseo|censys|zgrab|masscan|axios|node-fetch|feed|rss|validator|checker|scan|http\.rb|"
                         r"dalvik|^-$|^$", re.I)
NOT_A_PAGE = (".css", ".js", ".webp", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".mp4", ".webm", ".json", ".woff", ".woff2", ".pdf", ".map", ".zip", ".vtt")
GUIDES = {"/robots.txt": "robots.txt", "/sitemap.xml": "sitemap.xml", "/llms.txt": "llms.txt", "/es/llms.txt": "llms-es.txt"}


def who(ua):
    """(kind, name): kind is ai, crawler, robot or person."""
    for key, name in AI:
        if key in ua:
            return "ai", name
    for key, name in CRAWLERS:
        if key in ua:
            return "crawler", name
    if OTHER_ROBOT.search(ua):
        return "robot", "Other robots"
    return "person", ""


def page_of(path):
    """The page an address names, or None when it is a file of the site, the editing page, or not a page."""
    path = path.split("?")[0].split("#")[0]
    if path.startswith(("/assets/", "/edit", "/.well-known", "/.dh-diag", "/_assets")) or ".." in path:
        return None
    if path in GUIDES:
        return None
    low = path.lower()
    if low.endswith(NOT_A_PAGE):
        return None
    if "." in path.rsplit("/", 1)[-1] and not low.endswith(".html"):
        return None
    if low.endswith(".html"):
        path = path[:-5]
    if path.endswith("/index"):
        path = path[:-6]
    path = path.rstrip("/") or "/"
    return path[:120]


def empty(day):
    return dict(date=day, requests=0, visitors=0, views=dict(person=0, crawler=0, ai=0, robot=0), pages={}, referrers={},
                es=0, en=0, agents={}, status={}, missing={}, guides={}, hours=[0] * 24, edit=0, countries={})


def load_day(day):
    p = os.path.join(DAYS, day + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else empty(day)


def save_day(d):
    os.makedirs(DAYS, exist_ok=True)
    p = os.path.join(DAYS, d["date"] + ".json")
    json.dump(d, open(p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(p + ".tmp", p)


def top(counter, n):
    """Keeps a dict of counts short: the n largest."""
    if len(counter) > n * 3:
        return dict(sorted(counter.items(), key=lambda kv: -kv[1])[:n])
    return counter



# ---------------------------------------------------------------------------------------------- countries
COUNTRY = {}        # loaded on first use: (v4 starts, v4 ends, v4 codes, v6 starts, v6 ends, v6 codes)


def geo_file():
    """This month's list, downloaded if it is not here yet. Last month's is kept while the download fails."""
    os.makedirs(GEO, exist_ok=True)
    month = time.strftime("%Y-%m")
    path = os.path.join(GEO, "dbip-country-lite-%s.csv.gz" % month)
    if not os.path.exists(path):
        try:
            req = urllib.request.Request("https://download.db-ip.com/free/dbip-country-lite-%s.csv.gz" % month,
                                         headers={"User-Agent": "unitednotions.film visitors page (python-urllib)"})
            with urllib.request.urlopen(req, timeout=120) as r, open(path + ".tmp", "wb") as f:
                f.write(r.read())
            os.replace(path + ".tmp", path)
            for old in os.listdir(GEO):
                if old != os.path.basename(path) and not old.endswith(".tmp"):
                    os.remove(os.path.join(GEO, old))
        except Exception:
            if os.path.exists(path + ".tmp"):
                os.remove(path + ".tmp")
    have = sorted(f for f in os.listdir(GEO) if f.endswith(".csv.gz"))
    return os.path.join(GEO, have[-1]) if have else None


def load_geo():
    """The list as six sorted arrays, kept beside the file in a form that loads in a moment."""
    src = geo_file()
    if not src:
        return None
    cache = src[:-7] + ".pickle"
    if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(src):
        return pickle.load(open(cache, "rb"))
    v4, v6 = [], []
    with gzip.open(src, "rt", encoding="utf-8") as f:
        for line in f:
            a, b, cc = line.rstrip("\n").split(",")
            try:
                lo, hi = ipaddress.ip_address(a), ipaddress.ip_address(b)
            except ValueError:
                continue
            (v6 if lo.version == 6 else v4).append((int(lo), int(hi), cc))
    v4.sort()
    v6.sort()
    data = ([r[0] for r in v4], [r[1] for r in v4], [r[2] for r in v4], [r[0] for r in v6], [r[1] for r in v6], [r[2] for r in v6])
    pickle.dump(data, open(cache + ".tmp", "wb"))
    os.replace(cache + ".tmp", cache)
    return data


def country(ip):
    """The two-letter code of the country an address is in, or "" when unknown."""
    if not COUNTRY:
        COUNTRY["data"] = load_geo()
    data = COUNTRY["data"]
    if not data:
        return ""
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return ""
    starts, ends, codes = data[3:] if a.version == 6 else data[:3]
    n = int(a)
    i = bisect.bisect_right(starts, n) - 1
    if i >= 0 and ends[i] >= n and codes[i] != "ZZ":
        return codes[i]
    return ""


NAMES = {"AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan", "AG": "Antigua and Barbuda", "AL": "Albania", "AM": "Armenia", "AO": "Angola",
 "AR": "Argentina", "AT": "Austria", "AU": "Australia", "AZ": "Azerbaijan", "BA": "Bosnia and Herzegovina", "BB": "Barbados", "BD": "Bangladesh",
 "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria", "BH": "Bahrain", "BI": "Burundi", "BJ": "Benin", "BN": "Brunei", "BO": "Bolivia", "BR": "Brazil",
 "BS": "Bahamas", "BT": "Bhutan", "BW": "Botswana", "BY": "Belarus", "BZ": "Belize", "CA": "Canada", "CD": "Congo (DRC)", "CF": "Central African Republic",
 "CG": "Congo", "CH": "Switzerland", "CI": "Ivory Coast", "CL": "Chile", "CM": "Cameroon", "CN": "China", "CO": "Colombia", "CR": "Costa Rica", "CU": "Cuba",
 "CV": "Cape Verde", "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany", "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica", "DO": "Dominican Republic",
 "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt", "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia", "FI": "Finland", "FJ": "Fiji",
 "FR": "France", "GA": "Gabon", "GB": "United Kingdom", "GD": "Grenada", "GE": "Georgia", "GH": "Ghana", "GM": "Gambia", "GN": "Guinea", "GQ": "Equatorial Guinea",
 "GR": "Greece", "GT": "Guatemala", "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong Kong", "HN": "Honduras", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary",
 "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IN": "India", "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy", "JM": "Jamaica", "JO": "Jordan",
 "JP": "Japan", "KE": "Kenya", "KG": "Kyrgyzstan", "KH": "Cambodia", "KM": "Comoros", "KN": "Saint Kitts and Nevis", "KP": "North Korea", "KR": "South Korea",
 "KW": "Kuwait", "KZ": "Kazakhstan", "LA": "Laos", "LB": "Lebanon", "LC": "Saint Lucia", "LI": "Liechtenstein", "LK": "Sri Lanka", "LR": "Liberia", "LS": "Lesotho",
 "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya", "MA": "Morocco", "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro", "MG": "Madagascar",
 "MK": "North Macedonia", "ML": "Mali", "MM": "Myanmar", "MN": "Mongolia", "MO": "Macao", "MR": "Mauritania", "MT": "Malta", "MU": "Mauritius", "MV": "Maldives",
 "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia", "MZ": "Mozambique", "NA": "Namibia", "NE": "Niger", "NG": "Nigeria", "NI": "Nicaragua", "NL": "Netherlands",
 "NO": "Norway", "NP": "Nepal", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama", "PE": "Peru", "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan",
 "PL": "Poland", "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PY": "Paraguay", "QA": "Qatar", "RO": "Romania", "RS": "Serbia", "RU": "Russia",
 "RW": "Rwanda", "SA": "Saudi Arabia", "SB": "Solomon Islands", "SC": "Seychelles", "SD": "Sudan", "SE": "Sweden", "SG": "Singapore", "SI": "Slovenia",
 "SK": "Slovakia", "SL": "Sierra Leone", "SM": "San Marino", "SN": "Senegal", "SO": "Somalia", "SR": "Suriname", "SS": "South Sudan", "SV": "El Salvador",
 "SY": "Syria", "SZ": "Eswatini", "TD": "Chad", "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan", "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia",
 "TO": "Tonga", "TR": "Turkey", "TT": "Trinidad and Tobago", "TW": "Taiwan", "TZ": "Tanzania", "UA": "Ukraine", "UG": "Uganda", "US": "United States",
 "UY": "Uruguay", "UZ": "Uzbekistan", "VA": "Vatican City", "VC": "Saint Vincent and the Grenadines", "VE": "Venezuela", "VN": "Vietnam", "VU": "Vanuatu",
 "WS": "Samoa", "YE": "Yemen", "ZA": "South Africa", "ZM": "Zambia", "ZW": "Zimbabwe", "RE": "Réunion", "GP": "Guadeloupe", "MQ": "Martinique", "GF": "French Guiana",
 "NC": "New Caledonia", "PF": "French Polynesia", "AW": "Aruba", "CW": "Curaçao", "BM": "Bermuda", "KY": "Cayman Islands", "GI": "Gibraltar", "JE": "Jersey",
 "GG": "Guernsey", "IM": "Isle of Man", "FO": "Faroe Islands", "GL": "Greenland", "AX": "Åland Islands", "XK": "Kosovo", "EU": "Europe (unspecified)"}


def country_name(cc):
    return NAMES.get(cc, cc)


# ---------------------------------------------------------------------------------------------- reading the log
def read_logs():
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    days, seen = {}, {}
    for path in LOGS:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            first = f.readline()
            f.seek(0)
            st = os.stat(path)
            key = "%d:%s" % (st.st_ino, first[:60])
            done = state.get(path, {}).get("lines", 0) if state.get(path, {}).get("key") == key else 0
            n = 0
            for n, line in enumerate(f, 1):
                if n <= done:
                    continue
                count(line, days, seen)
            state[path] = dict(key=key, lines=max(n, done), run=time.strftime("%Y-%m-%d %H:%M"))
    for day, d in days.items():
        save_day(d)
        with open(os.path.join(DAYS, day + ".visitors"), "a", encoding="utf-8") as f:
            f.write("".join(v + "\n" for v in seen[day]["new"]))
    # the visitor lists of past days are not needed any more
    cutoff = (date.today() - timedelta(days=3)).isoformat()
    for f in os.listdir(DAYS) if os.path.isdir(DAYS) else []:
        if f.endswith(".visitors") and f[:10] < cutoff:
            os.remove(os.path.join(DAYS, f))
    os.makedirs(STATS, exist_ok=True)
    json.dump(state, open(STATE, "w"), indent=1)
    return days


def count(line, days, seen):
    m = LINE.match(line)
    if not m:
        return
    ip, user, when, method, path, status, size, ref, ua = m.groups()
    try:
        day = "%s-%02d-%s" % (when[7:11], MONTHS[when[3:6]], when[0:2])
        hour = int(when[12:14])
    except (KeyError, ValueError):
        return
    if ua.startswith("curl/"):            # the site's own checks
        return
    if day not in days:
        days[day] = load_day(day)
        vf = os.path.join(DAYS, day + ".visitors")
        seen[day] = dict(known=set(open(vf).read().split()) if os.path.exists(vf) else set(), new=set())
    d = days[day]
    d["requests"] += 1
    d["status"][status] = d["status"].get(status, 0) + 1
    kind, name = who(ua)
    if name:
        d["agents"][name] = d["agents"].get(name, 0) + 1
    if path.startswith("/edit"):
        d["edit"] += 1
        return
    clean = path.split("?")[0]
    if clean in GUIDES and status in ("200", "304"):
        g = d["guides"].setdefault(GUIDES[clean], dict(person=0, crawler=0, ai=0, robot=0))
        g[kind] += 1
        return
    if status == "404":
        p = clean[:120]
        d["missing"][p] = d["missing"].get(p, 0) + 1
        d["missing"] = top(d["missing"], 40)
        return
    if method != "GET" or status not in ("200", "304"):
        return
    page = page_of(path)
    if page is None:
        return
    d["views"][kind] += 1
    if kind != "person":
        return
    d["hours"][hour] += 1
    if page == "/es" or page.startswith("/es/"):
        d["es"] += 1
    else:
        d["en"] += 1
    d["pages"][page] = d["pages"].get(page, 0) + 1
    d["pages"] = top(d["pages"], 200)
    host = re.sub(r"^https?://(www\.)?", "", ref).split("/")[0].lower() if ref and ref != "-" else ""
    if host and not host.endswith("unitednotions.film"):
        d["referrers"][host] = d["referrers"].get(host, 0) + 1
        d["referrers"] = top(d["referrers"], 60)
    v = hashlib.sha256(("%s|%s|%s" % (ip, ua, day)).encode()).hexdigest()[:16]
    s = seen[day]
    if v not in s["known"] and v not in s["new"]:
        s["new"].add(v)
        d["visitors"] += 1
        cc = country(ip) or "?"
        d.setdefault("countries", {})
        d["countries"][cc] = d["countries"].get(cc, 0) + 1


# ---------------------------------------------------------------------------------------------- the page
def history(n):
    """The last n days, oldest first, with empty days filled in."""
    today = date.today()
    out = []
    for i in range(n - 1, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        out.append(load_day(day))
    return out


def title_of(page):
    """The title of a page of the site, read from its file, so the table reads as words and not addresses."""
    rel = ("index" if page == "/" else page.strip("/")) + ".html"
    if page in ("/es", "/es/"):
        rel = "es/index.html"
    p = os.path.join(SITE, rel)
    if os.path.isfile(p):
        head = open(p, encoding="utf-8", errors="replace").read(4000)
        m = re.search(r"<title>(.*?)</title>", head, re.S)
        if m:
            return html.unescape(re.sub(r"\s*\|\s*United Notions Film\s*$", "", m.group(1).strip()))
    return page


def fmt(n):
    return "{:,}".format(n)


def nice_max(v):
    """A round top for an axis: 0, 10, 20, 50, 100, 200, 500 ..."""
    if v <= 0:
        return 4
    import math
    exp = 10 ** math.floor(math.log10(v))
    for k in (1, 2, 2.5, 5, 10):
        if k * exp >= v:
            return int(k * exp) if k * exp >= 4 else 4
    return int(10 * exp)


def columns(days, series, labels, colors, caption, note):
    """A column chart as inline SVG: one slot per day, bars at most 24px wide, rounded at the top, stacked with a 2px gap.
    series: list of functions day -> number, in the order they stack from the baseline."""
    W, H, L, R, T, B = 720, 220, 40, 10, 14, 30
    n = len(days)
    slot = (W - L - R) / n
    bw = min(24, slot * 0.64)
    totals = [sum(f(d) for f in series) for d in days]
    top_v = nice_max(max(totals) if totals else 0)
    scale = (H - T - B) / top_v
    g = []
    ticks = [0, top_v // 2, top_v] if top_v % 2 == 0 else [0, top_v]
    for t in ticks:
        y = H - B - t * scale
        g.append('<line class="grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/><text class="tick" x="%d" y="%.1f">%s</text>' % (L, y, W - R, y, L - 6, y + 4, fmt(t)))
    gap = 2
    for i, d in enumerate(days):
        x = L + i * slot + (slot - bw) / 2
        y0 = H - B
        parts = []
        for k, f in enumerate(series):
            v = f(d)
            if v <= 0:
                continue
            h = v * scale
            y1 = y0 - h
            is_top = all(f2(d) <= 0 for f2 in series[k + 1:])
            if is_top and h >= 4:
                r = 4
                path = ("M%.1f %.1fv%.1fa%d %d 0 0 1 %d -%dh%.1fa%d %d 0 0 1 %d %dv%.1fz"
                        % (x, y0, -(h - r), r, r, r, r, bw - 2 * r, r, r, r, r, h - r))
                parts.append('<path fill="%s" d="%s"/>' % (colors[k], path))
            else:
                parts.append('<rect fill="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (colors[k], x, y1, bw, max(h - (gap if not is_top else 0), 0.5)))
            y0 = y1
        label = d["date"][8:10].lstrip("0") + " " + ("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[int(d["date"][5:7]) - 1])
        tip = ", ".join("%s %s" % (fmt(f(d)), lab.lower()) for f, lab in zip(series, labels))
        if (n - 1 - i) % 5 == 0 or n <= 10:          # today, and every fifth day back from it
            g.append('<text class="x" x="%.1f" y="%d">%s</text>' % (x + bw / 2, H - 8, E(label)))
        g.append('<g class="slot" data-tip="%s">%s<rect class="hit" x="%.1f" y="%d" width="%.1f" height="%d"/><title>%s</title></g>'
                 % (E(label + ": " + tip), "".join(parts), L + i * slot, T, slot, H - T - B, E(label + ": " + tip)))
    legend = ""
    if len(series) > 1:
        legend = '<p class="legend">%s</p>' % "".join('<span><i style="background:%s"></i>%s</span>' % (c, E(l)) for c, l in zip(colors, labels))
    return ('<figure class="chart"><figcaption><b>%s</b> <span>%s</span></figcaption>%s'
            '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg></figure>' % (E(caption), E(note), legend, W, H, E(caption), "".join(g)))



def bars(rows, caption, note, color="var(--s1)"):
    """Horizontal bars for a short ranked list: name on the left, bar, value at its tip. One series, so no legend."""
    if not rows:
        return '<figure class="chart"><figcaption><b>%s</b> <span>%s</span></figcaption><p class="none">Nothing yet.</p></figure>' % (E(caption), E(note))
    W, L, R, row, bh = 720, 170, 56, 26, 16
    H = row * len(rows) + 8
    top_v = max(v for _, v in rows) or 1
    g = []
    for i, (name, v) in enumerate(rows):
        y = 4 + i * row
        w = max((W - L - R) * v / top_v, 1)
        r = min(4, w / 2)
        path = "M%d %.1fh%.1fa%d %d 0 0 1 %d %dv%.1fa%d %d 0 0 1 -%d %dh-%.1fz" % (L, y, w - r, r, r, r, r, bh - 2 * r, r, r, r, r, w - r)
        g.append('<g class="slot" data-tip="%s"><text class="name" x="%d" y="%.1f">%s</text><path fill="%s" d="%s"/>'
                 '<text class="val" x="%.1f" y="%.1f">%s</text><rect class="hit" x="0" y="%.1f" width="%d" height="%d"/><title>%s</title></g>'
                 % (E("%s: %s" % (name, fmt(v))), L - 10, y + bh - 4, E(name[:26]), color, path, L + w + 8, y + bh - 4, fmt(v), y - 2, W, row, E("%s: %s" % (name, fmt(v)))))
    return ('<figure class="chart"><figcaption><b>%s</b> <span>%s</span></figcaption>'
            '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg></figure>' % (E(caption), E(note), W, H, E(caption), "".join(g)))


def table(headers, rows, cls=""):
    if not rows:
        return '<p class="none">Nothing yet.</p>'
    return ('<table class="%s"><tr>%s</tr>%s</table>'
            % (cls, "".join("<th%s>%s</th>" % (' class="n"' if i else "", E(h)) for i, h in enumerate(headers)),
               "".join("<tr>%s</tr>" % "".join("<td%s>%s</td>" % (' class="n"' if i else "", c) for i, c in enumerate(r)) for r in rows)))


def render():
    last30, last90 = history(30), history(90)
    today = last30[-1]
    week = last30[-7:]
    sum30 = lambda key, sub=None: sum((d[key][sub] if sub else d[key]) for d in last30)
    views30 = sum30("views", "person")
    es30 = sum30("es")
    ai30 = sum30("views", "ai") + sum(sum(g["ai"] for g in d["guides"].values()) for d in last30)
    pages, refs, agents, missing, last_seen, kinds = Counter(), Counter(), Counter(), Counter(), {}, {}
    for d in last30:
        pages.update(d["pages"])
        refs.update(d["referrers"])
        agents.update(d["agents"])
        missing.update(d["missing"])
        for a in d["agents"]:
            last_seen[a] = d["date"]
    for key, name in AI:
        kinds[name] = "AI"
    for key, name in CRAWLERS:
        kinds[name] = "search and links"
    kinds["Other robots"] = "other"
    refused = Counter()
    for d in last30:
        if d["status"].get("429"):
            refused["all"] += d["status"]["429"]
    guides = Counter()
    for d in last30:
        for g, k in d["guides"].items():
            guides[g] += k["ai"] + k["crawler"]
    tiles = [("Visitors today", fmt(today["visitors"]), "people, so far"),
             ("Last 7 days", fmt(sum(d["visitors"] for d in week)), "visitors, counted once a day"),
             ("Last 30 days", fmt(sum(d["visitors"] for d in last30)), "visitors, counted once a day"),
             ("Pages read", fmt(views30), "by people, last 30 days"),
             ("In Spanish", ("%d%%" % round(100 * es30 / max(views30, 1))), "of the pages read"),
             ("Read by AI assistants", fmt(ai30), "pages and guides, last 30 days")]
    light, dark = ("#2a78d6", "#eb6834", "#1baf7a"), ("#3987e5", "#d95926", "#199e70")
    chart1 = columns(last30, [lambda d: d["visitors"]], ["visitors"], ["var(--s1)"], "Visitors by day", "people, each counted once a day, last 30 days")
    chart2 = columns(last30, [lambda d: d["views"]["person"], lambda d: d["views"]["crawler"] + d["views"]["robot"], lambda d: d["views"]["ai"]],
                     ["People", "Search engines and link previews", "AI assistants"], ["var(--s1)", "var(--s2)", "var(--s3)"],
                     "Pages read by day", "who asked, last 30 days")
    chart3 = columns(last90, [lambda d: d["visitors"]], ["visitors"], ["var(--s1)"], "Visitors by day", "last 90 days") if any(d["visitors"] for d in last90[:60]) else ""
    countries = Counter()
    for d in last30:
        countries.update(d.get("countries", {}))
    known = sum(v for k, v in countries.items() if k != "?")
    chart_c = bars([(country_name(cc), n) for cc, n in countries.most_common(12) if cc != "?"], "Visitors by country",
                   "people, last 30 days, each counted once a day" + (", %s of unknown origin" % fmt(countries["?"]) if countries.get("?") else ""))
    rows_countries = [(E(country_name(cc)), fmt(n), "%d%%" % round(100 * n / max(known, 1))) for cc, n in countries.most_common(40) if cc != "?"]
    rows_pages = [(E(title_of(p)) + ' <small>%s</small>' % E(p), fmt(c)) for p, c in pages.most_common(15)]
    rows_refs = [(E(h), fmt(c)) for h, c in refs.most_common(15)]
    rows_agents = [(E(a), E(kinds.get(a, "other")), fmt(c), E(last_seen.get(a, ""))) for a, c in agents.most_common(25)]
    rows_missing = [("<small>%s</small>" % E(p), fmt(c)) for p, c in missing.most_common(10)]
    rows_days = [(d["date"], fmt(d["visitors"]), fmt(d["views"]["person"]), fmt(d["views"]["crawler"] + d["views"]["robot"]), fmt(d["views"]["ai"]),
                  fmt(d["status"].get("404", 0)), fmt(d["status"].get("429", 0))) for d in reversed(last30) if d["requests"]]
    guides_line = ", ".join("%s %s" % (fmt(c), g) for g, c in guides.most_common()) or "none yet"
    since = min((f[:10] for f in os.listdir(DAYS) if f.endswith(".json")), default=today["date"]) if os.path.isdir(DAYS) else today["date"]
    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Visitors | United Notions Film</title>
<style>
  :root { color-scheme: light dark; --ink:#0b0b0b; --ink2:#52514e; --mute:#8a8984; --paper:#fcfcfb; --line:#e3e2de; --soft:#f3f2ef; --go:#0b57d0; --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; }
  @media (prefers-color-scheme: dark) { :root { --ink:#fff; --ink2:#c3c2b7; --mute:#8d8c86; --paper:#1a1a19; --line:#33332f; --soft:#242422; --go:#8ab4f8; --s1:#3987e5; --s2:#d95926; --s3:#199e70; } }
  * { box-sizing:border-box; }
  body { margin:0; padding:20px 16px 60px; font:15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--ink); background:var(--paper); }
  .wrap { max-width:1100px; margin:0 auto; }
  h1 { font-size:20px; margin:0 0 2px; } h2 { font-size:16px; margin:36px 0 10px; }
  p.lead { margin:0 0 20px; color:var(--ink2); } a { color:var(--go); }
  .top { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; }
  .btn { font:inherit; padding:8px 14px; border:1px solid var(--line); background:var(--soft); color:var(--ink); border-radius:6px; text-decoration:none; }
  .tiles { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin:8px 0 28px; }
  .tile { border:1px solid var(--line); border-radius:10px; padding:14px 16px; background:var(--soft); }
  .tile .l { font-size:13px; color:var(--ink2); } .tile .v { font-size:34px; line-height:1.1; font-weight:600; margin:4px 0 2px; } .tile .s { font-size:12.5px; color:var(--mute); }
  .chart { margin:0 0 28px; } .chart figcaption { margin:0 0 6px; } .chart figcaption span { color:var(--mute); font-size:13.5px; margin-left:6px; }
  .chart svg { width:100%%; height:auto; display:block; background:var(--paper); }
  .grid { stroke:var(--line); stroke-width:1; } .tick { font-size:11px; fill:var(--mute); text-anchor:end; } .x { font-size:11px; fill:var(--mute); text-anchor:middle; }
  .hit { fill:transparent; } .slot:hover .hit { fill:var(--ink); fill-opacity:.05; }
  .name { font-size:12.5px; fill:var(--ink2); text-anchor:end; } .val { font-size:12px; fill:var(--ink2); font-variant-numeric:tabular-nums; }
  .legend { margin:0 0 8px; font-size:13px; color:var(--ink2); } .legend span { margin-right:16px; } .legend i { display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; vertical-align:-1px; }
  table { width:100%%; border-collapse:collapse; } th, td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  th { font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--mute); font-weight:600; } th.n, td.n { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
  td small { color:var(--mute); display:block; font-size:12px; } .none { color:var(--mute); }
  .cols { display:grid; grid-template-columns:1fr 1fr; gap:32px; } @media (max-width:800px) { .cols { grid-template-columns:1fr; } }
  details { margin-top:16px; } summary { cursor:pointer; color:var(--ink2); }
  #tip { position:fixed; pointer-events:none; background:var(--ink); color:var(--paper); padding:6px 10px; border-radius:6px; font-size:12.5px; display:none; z-index:9; max-width:320px; }
  p.how { color:var(--mute); font-size:13px; margin-top:36px; }
</style>
</head>
<body>
<div class="wrap">
<div class="top"><div><h1>United Notions Film: visitors</h1><p class="lead">What the server saw, counted every quarter hour, since %(since)s. Updated %(now)s, server time.</p></div><a class="btn" href="../">Editing</a></div>
<div class="tiles">%(tiles)s</div>
%(chart1)s
%(chart2)s
%(chart3)s
%(chart_c)s
<details><summary>Every country, last 30 days</summary>%(countries)s</details>
<div class="cols">
<div><h2>Most read pages</h2>%(pages)s</div>
<div><h2>Where visitors came from</h2>%(refs)s<p class="how" style="margin-top:10px">Only visits that arrived from another site are listed. Most visits name no origin: a typed address, a message, or a browser that keeps it private.</p></div>
</div>
<h2>Robots, crawlers and AI assistants</h2>
<p class="lead" style="margin-bottom:8px">Requests of any kind, last 30 days. The guides were read %(guides)s times by robots.%(refused)s</p>
%(agents)s
<div class="cols">
<div><h2>Addresses that did not exist</h2>%(missing)s</div>
<div><h2>Day by day</h2>%(days)s</div>
</div>
<p class="how">How this is made: the server writes one line per request to its log. Every quarter hour a small program reads the new lines and adds to one summary per day:
how many different people (one count per address and browser per day, kept only as a hash and not kept at all after two days), which pages they read, where they came from,
and which robots called. No script runs on the site for this, no cookie is set, and no address or name is stored. A person who reads the site from two devices counts twice;
a shared office address counts once. Days are the server's, in US Pacific time. Countries come from the free address-to-country list of
<a href="https://db-ip.com" rel="noopener">DB-IP</a> (IP geolocation by DB-IP, CC BY 4.0), fetched to the server once a month; the lookup happens on the server and no address leaves it.</p>
</div>
<div id="tip"></div>
<script>
(function(){var t=document.getElementById('tip');document.querySelectorAll('.slot').forEach(function(s){s.addEventListener('mousemove',function(e){t.textContent=s.getAttribute('data-tip');t.style.display='block';t.style.left=Math.min(e.clientX+14,window.innerWidth-330)+'px';t.style.top=(e.clientY+14)+'px';});s.addEventListener('mouseleave',function(){t.style.display='none';});});})();
</script>
</body>
</html>
""" % dict(
        since=E(since), now=E(time.strftime("%-d %B %Y, %H:%M")),
        tiles="".join('<div class="tile"><div class="l">%s</div><div class="v">%s</div><div class="s">%s</div></div>' % (E(l), v, E(s)) for l, v, s in tiles),
        chart1=chart1, chart2=chart2, chart3=chart3, chart_c=chart_c, countries=table(["Country", "Visitors", "Share"], rows_countries),
        pages=table(["Page", "Read"], rows_pages), refs=table(["Site", "Visits"], rows_refs),
        agents=table(["Who", "Kind", "Requests", "Last seen"], rows_agents),
        missing=table(["Address", "Asked"], rows_missing),
        days=table(["Day", "Visitors", "Pages, people", "Crawlers", "AI", "404", "429"], rows_days),
        guides=E(guides_line),
        refused=(" The server refused %s requests with 429 (too many requests); that is DreamHost's own protection, not the site." % fmt(refused["all"])) if refused["all"] else "")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT + ".tmp", "w", encoding="utf-8") as f:
        f.write(page)
    os.replace(OUT + ".tmp", OUT)


if __name__ == "__main__":
    os.makedirs(DAYS, exist_ok=True)
    read_logs()
    render()
