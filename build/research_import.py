"""Reads the lab notes saved from the old site and turns each one into a plain list of blocks.

It was run once, for version 4. Running it again writes the English notes from scratch and loses what was corrected by hand.
    python3 build/research_import.py
Reads   the notes as the old site stored them: <note>/page-data.json and meta.json,
        in build/src-old/research or, when that folder is not there, in the backup beside the site
        (unitednotions-film-backup/site/pages/research)
Writes  build/research/en/<note>.txt                   one block per line, ready to be translated
        build/data/research.json                       the list of notes: title, date, place, summary, pictures, videos
        build/data/research-manifest.json              every picture of every note, for the script that makes the web copies

A block line starts with a tag:
    T:   title of the note                 D:   description for search engines
    S:   one-sentence summary
    H:   heading inside the note           P:   first line of a paragraph
    +:   next line of the same paragraph   LI:  list item
    A:   link text | address               IMG: number | address the picture links to (optional)
    GAL: numbers of the pictures of a gallery
    VID: file name of a short video        YT: / VM:  video id | title    (YouTube, Vimeo)
    EMBED: name | address | title          a thing that sits in the page (the pose carousel, a slide deck)
    MISSING-VIDEO: id                      a video that stayed on the old host

Inside a line, a link is written [text](address).
"""
import json
import os
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src-old")
if not os.path.isdir(SRC):
    for up in ("..", os.path.join("..", "..")):          # the build folder sits inside the site folder, or beside it
        backup = os.path.join(HERE, up, "unitednotions-film-backup", "site", "pages")
        if os.path.isdir(backup):
            SRC = backup
            break
OUT = os.path.join(HERE, "research", "en")

MONTHS = {"jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3, "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
          "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12}

# ---------------------------------------------------------------- written by hand
# key:    short name used for the files of the pictures
# title:  the title of the note, in sentence case
# keep:   the note opens with a second title on the old page. It stays as the first heading.
# date:   only for notes that carry no date line. (date, place)
NOTES = {
    "the-jaguaress-learns-her-own-skeleton": dict(key="jaguaress-skeleton", title="The jaguaress learns her own skeleton"),
    "the-whale-that-watches-back": dict(key="whale-watches", title="The whale that watches back"),
    "the-body-decides-the-interface": dict(key="body-decides", title="The body decides the interface"),
    "the-monkey-learns-the-shape-of-its-own-body": dict(key="monkey-body", title="The monkey learns the shape of its own body"),
    "the-monkey-learns-to-move": dict(key="monkey-moves", title="The monkey learns to move: quaternions, humanoid puppeteering"),
    "the-llama-learns-to-feel": dict(key="llama-feels", title="The llama learns to feel, the model learns to listen, and Yakumama is born"),
    "when-the-heartbeat-moves-the-flower": dict(key="heartbeat-flower", title="When the heartbeat moves the flower"),
    "the-spider-learns-to-weave-the-gecko-learns-to-feel": dict(key="spider-weaves", title="The spider learns to weave, the gecko learns to feel, and SIGGRAPH calls"),
    "the-gecko-learns-to-feel-qwen-finds-its-voice": dict(key="gecko-feels", title="The gecko learns to feel, Qwen 3.6 finds its voice, and the recording begins"),
    "15-creatures-14-pipelines-platform-agnostic-brain": dict(key="15-creatures", title="15 creatures, 14 pipelines and a platform-agnostic brain", keep=True),
    "the-water-lily-learns-to-breathe": dict(key="water-lily", title="The water lily learns to breathe, the sundew counts fingers, and the pipeline moves to WebSocket"),
    "the-tree-learns-fear-the-orchid-mourns-fire": dict(key="tree-fear", title="The tree learns fear, the orchid mourns fire, and the llama finds stillness", keep=True),
    "the-2-dollar-gyroscope": dict(key="gyroscope", title="The $2 gyroscope that solved what the neural network couldn’t"),
    "toward-embodied-intelligence-for-nonhuman-characters": dict(key="embodied-intelligence", title="Toward embodied intelligence for nonhuman characters"),
    "somatic-puppeteering-plants-condor-heartbeat-march-2026": dict(key="somatic-puppeteering", title="Somatic puppeteering across plants, birds and heartbeats"),
    "technologies-of-distribution-comteco-transparency": dict(key="comteco", title="Technologies of distribution, Comteco and the fight for transparency"),
    "when-documentary-begins-to-think": dict(key="documentary-thinks", title="When documentary begins to think", keep=True),
    "from-documentary-to-living-systems": dict(key="living-systems", title="From documentary to living systems"),
    "the-condor-obeyed-violetas-hand": dict(key="condor-hand", title="The condor obeyed Violeta’s hand"),
    "building-huk-v1-digital-deity-amazon": dict(key="building-huk", title="Building Huk V1.0: a digital deity for the burning Amazon"),
    "fair-future-feminist-ai": dict(key="feminist-ai", title="Two machines, one question: feminist AI at the VIP Studio", keep=True),
    "luna-feminist-ai": dict(key="luna", title="Violeta Ayala’s mission: creating LUNA, the future of feminist AI"),
    "prisonx-storytelling-evolution-through-gen-z": dict(key="prison-x-gen-z", title="Prison X: unlocking the Gen Z code"),
    "sxsw-sydney-2023": dict(key="sxsw-sydney", title="La Lucha and Prison X at SXSW Sydney"),
    "las-awichas-immersive-phygital-violeta-ayala-glow3-london-2024": dict(key="awichas-glow", title="Las Awichas selected for the major GLoW3 exhibition in London"),
    "redefining-reality-xr-ai-voices-of-vr-kent-bye": dict(key="voices-of-vr", title="Exploring the future of XR and AI: a conversation with Kent Bye", date=("2023", "")),
    "policy-recommendations-nsw-arts-culture-tech-equity": dict(key="nsw-policy", title="Shaping policy for the arts and cultural sector", date=("2023", "")),
    "aug-20-2023": dict(key="la-lucha-outreach", title="La Lucha receives support for outreach", date=("2023-08-20", "")),
    "aug-19-2023": dict(key="la-lucha-blackstar", title="La Lucha premieres at BlackStar Film Festival: a night to remember", date=("2023-08-19", "")),
    "brain-jam-games-for-change-nyc": dict(key="brain-jam", title="Violeta Ayala wins the XR Innovation 2023 award at Brain Jam, Games for Change, New York"),
}

# One-sentence summaries. The first group is written on the old archive page; the rest is the opening of each description.
SUMMARIES = {
    "the-jaguaress-learns-her-own-skeleton": "Huk the Jaguaress recovered her twenty-four real poses from an export that only looked finished: a faithful carousel exposed a smooth interpolation, an exporter rewritten to read the rig’s true keyframes brought the body back, and the question turned from how she moves to why.",
    "the-whale-that-watches-back": "YakuMama reads the colour of the room and answers with mood and song, decaying and reweighting ten emotions every frame, diving when the water is taken and singing when the rain comes, all running locally on one machine with no cloud.",
    "the-body-decides-the-interface": "The gecko learns finger puppeteering, the monkey begins to mirror directly, Huk the Jaguaress discovers her own skeletal logic, and a taxonomy of locomotion emerges.",
    "the-monkey-learns-the-shape-of-its-own-body": "Procedural tails, swing-twist quaternion decomposition, performer-centered quadruped animation, and the discovery that rest poses themselves carry assumptions about bodies, movement, and intelligence.",
    "the-monkey-learns-to-move": "Quaternion retargeting, hybrid body-hand tracking, spine cascade systems, and the first full-body humanoid creature pipeline inside our ecosystem.",
    "the-llama-learns-to-feel": "Neural network mood training, cardiac breathing systems, Yakumama’s emergence, and ch’ixi philosophy entering the animation pipeline.",
    "when-the-heartbeat-moves-the-flower": "Pulse sensors, ESP32 systems, systole and diastole translated into real-time plant animation and embodied computational creativity.",
    "the-spider-learns-to-weave-the-gecko-learns-to-feel": "Orb-web systems, gecko emotional memory, Qwen integration, and SIGGRAPH documentation.",
    "the-gecko-learns-to-feel-qwen-finds-its-voice": "Sensor fusion, emotional state systems, flavor memories, AI narration, and real-time creature cognition.",
    "15-creatures-14-pipelines-platform-agnostic-brain": "Building real-time creature intelligence systems across Blender, VR, sensors, and XR worlds.",
    "the-water-lily-learns-to-breathe": "Victoria Regia water sensing, Drosera finger tracking, hummingbird gaze systems, and WebSocket architecture migration.",
    "the-tree-learns-fear-the-orchid-mourns-fire": "NASA wildfire feeds, shy trees with infrared sensing, and calibration systems for nonhuman creature embodiment.",
    "the-2-dollar-gyroscope": "Sensor fusion, 360° body tracking, gyroscopes, MediaPipe limitations, and embodied spatial intelligence.",
    "toward-embodied-intelligence-for-nonhuman-characters": "Depth sensing, robotic cameras, MediaPipe integration, and spatial movement systems beyond human pose datasets.",
    "somatic-puppeteering-plants-condor-heartbeat-march-2026": "March 2026 research sprint exploring real-time body-driven creature systems across plants, condors, shaders, and pulse-responsive environments.",
}

SUMMARIES.update({
    "when-documentary-begins-to-think": "Two weeks on two fronts. In the lab, motion systems and pixel surfaces that react to movement. In the streets of Cochabamba, the Comteco vigil filmed and streamed as it happens.",
    "technologies-of-distribution-comteco-transparency": "For 88 days the senior shareholders of the telecom cooperative Comteco hold a vigil for elections, audits and answers. TikTok becomes a living archive of the protest.",
    "from-documentary-to-living-systems": "Affective computing between Montreal and La Paz, new worlds for Huk, and public subsidies, music interfaces, electoral data and aqueducts read as technologies of distribution.",
    "the-condor-obeyed-violetas-hand": "At the opening of Surreality in Guangzhou a digital condor follows Violeta Ayala’s hand in real time. No motion capture suit. An early public demonstration of somatic puppeteering.",
    "building-huk-v1-digital-deity-amazon": "Huk the Jaguaress begins with the fires in the Amazon. Her first version connects wildfire alerts, plant bioelectricity, dancers and edge AI.",
    "fair-future-feminist-ai": "Violeta Ayala and Yasmeen Hitti join the Feminist AI residency at the University of Nottingham’s VIP Studio. They build the VIP Chatbot, where OpenAI and DeepSeek answer the same prompt side by side.",
    "luna-feminist-ai": "Violeta Ayala introduces LUNA, Learning Unbiased Neural Algorithm: a project and a documentary about building an AI that challenges bias.",
    "prisonx-storytelling-evolution-through-gen-z": "From Sundance to Paris and SXSW Sydney, Gen Z visitors move through Prison X by instinct while older audiences walk in circles.",
    "sxsw-sydney-2023": "The Australian premiere of La Lucha and the Sydney premiere of Prison X at SXSW Sydney.",
    "las-awichas-immersive-phygital-violeta-ayala-glow3-london-2024": "Las Awichas is one of four new commissions of the GLoW3 Artist Programme at King’s College London. How the work began in Tiupampa and Pocoata, and a diary of the first days in London.",
    "redefining-reality-xr-ai-voices-of-vr-kent-bye": "Violeta Ayala talks with Kent Bye on the Voices of VR podcast about XR, AI and creative sovereignty.",
    "policy-recommendations-nsw-arts-culture-tech-equity": "The submission of United Notions Film to the NSW Arts, Culture and Creative Industries policy: interdisciplinary programs, cultural diversity and an art and technology exchange.",
    "aug-20-2023": "The Perspective Fund backs the outreach of La Lucha across Latin America.",
    "aug-19-2023": "La Lucha premieres at BlackStar Film Festival in Philadelphia. The team, the guests, the reviews and the opening night.",
    "brain-jam-games-for-change-nyc": "At Brain Jam in New York six creators build twelve worlds of self-representation in 27 hours, starting from Aunt Victoria in Tiupampa. The work wins an Innovation Award.",
})

TRACKING = {"igshid", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "fbclid", "lid", "_r", "_t", "mibextid", "m"}


def clean(text):
    """Typography of the house: no long dashes, no stray marks."""
    text = text.replace("�", "").replace("​", "").replace(" ", " ").replace("\t", " ")
    text = re.sub(r"\s+[—–]\s+", ", ", text)           # word — word
    text = re.sub(r"(?<=\w)—(?=\w)", ", ", text)       # word—word
    text = re.sub(r"(?<=\w)–\s+", ", ", text)          # word– word
    text = re.sub(r"(?<=\w)–(?=\w)", "-", text)        # hand–command
    text = text.replace("—", ", ").replace("–", "-")
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*,", ",", text)
    text = text.replace("Daniel Fallshaw", "Dan Fallshaw")
    text = re.sub(r"[ ]+", " ", text).strip()
    return text


def tidy_link(href):
    """Drop the tracking codes. A link to another note of the old site becomes a link inside the new one."""
    href = href.strip()
    m = re.match(r"^https?://(?:www\.)?unitednotions\.film/(?:updates|research)/([a-z0-9-]+)/?$", href)
    if m and m.group(1) in NOTES:
        return "note:" + m.group(1)
    parts = urlsplit(href)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in TRACKING]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, safe="@,:"), parts.fragment))


def asset_id(url):
    m = re.search(r"/_assets/([0-9A-Za-z-]+)", url or "")
    return m.group(1).lower() if m else None


# ---------------------------------------------------------------- dates
def parse_date(line):
    m = re.match(r"^([A-Za-zÀ-ÿ .]+?)\s*/\s*(?:(\d{1,2})\s*/\s*)?([A-Za-z]+)\s*/\s*(\d{4})$", line.strip())
    if not m:
        return None
    place, day, month, year = m.group(1).strip(), m.group(2), m.group(3).lower(), int(m.group(4))
    if month not in MONTHS:
        return None
    iso = "%04d-%02d" % (year, MONTHS[month]) + ("-%02d" % int(day) if day else "")
    return iso, place


# ---------------------------------------------------------------- reading one note
def children(grid):
    kids = grid.get("children") or []
    return sorted(kids, key=lambda k: (k.get("position", {}).get("y", 0), k.get("position", {}).get("x", 0), k.get("position", {}).get("z", 0)))


def runs_of(utf):
    """The pieces of a text block: text, bold or not, and the address it links to."""
    utf = utf or {}
    c = utf.get("content") or {}
    heavy = ("bold", "black", "heavy")
    if c.get("type") == "text":
        return [dict(text=c.get("value", ""), bold=(utf.get("style") or {}).get("weight") in heavy, href=None)]
    out = []
    for r in c.get("value", []) if c.get("type") == "children" else []:
        att = r.get("attachment") or {}
        out.append(dict(text=(r.get("content") or {}).get("value", ""), bold=(r.get("style") or {}).get("weight") in heavy,
                        href=att.get("value") if att.get("type") == "href" else None))
    return out


def lines_of(runs):
    """Split the pieces at every line break. Returns a list of lines; a line is a list of pieces."""
    lines, cur = [], []
    for r in runs:
        parts = r["text"].split("\n")
        for i, part in enumerate(parts):
            if i:
                lines.append(cur)
                cur = []
            if part:
                cur.append(dict(r, text=part))
    lines.append(cur)
    return lines


def line_text(pieces):
    out = ""
    for p in pieces:
        t = p["text"]
        if p["href"] and t.strip():
            lead, core, tail = t[:len(t) - len(t.lstrip())], t.strip(), t[len(t.rstrip()):]
            out += "%s[%s](%s)%s" % (lead, core.replace("[", "(").replace("]", ")"), tidy_link(p["href"]), tail)
        else:
            out += t
    return clean(out)


DECORATION = re.compile(r"^[\s—–\-•·_*=~.,]+$")
BULLET = re.compile(r"^(?:•|\*|-|–|·)\s+(.*)$")


class Note:
    def __init__(self, slug):
        self.slug = slug
        self.hand = NOTES[slug]
        self.blocks = []
        self.images = []          # asset ids, in the order of the page
        self.sizes = {}           # asset id -> (width, height), as far as the old page tells
        self.videos = []
        self.posters = {}
        self.missing = []
        self.embeds = []
        self.iso, self.place = self.hand.get("date", ("", ""))
        self.dated = False
        self.seen_title = False
        self.page_title = ""

    # ---- pictures
    def image(self, url, size=None):
        a = asset_id(url)
        if a is None:
            return None
        if a not in self.images:
            self.images.append(a)
        if size and size[0] and size[1]:
            self.sizes.setdefault(a, [int(size[0]), int(size[1])])
        return self.images.index(a) + 1

    # ---- text
    def text(self, c, link):
        purpose = c.get("purpose")
        runs = runs_of(c.get("utf"))
        lines = lines_of(runs)
        plain = [line_text(l) for l in lines]
        whole = " ".join(t for t in plain if t)
        raw = "".join(r["text"] for r in runs)
        if not whole or DECORATION.match(raw) or DECORATION.match(whole):
            return
        # the date line
        if len(whole) < 40:
            d = parse_date(whole)
            if d:
                if not self.dated:
                    self.iso, self.place = d
                    self.dated = True
                return
        if whole.lower() in ("unitednotions.film", "united notions film"):
            return
        # the title of the page
        if purpose in ("sectionTitle", "pageTitle") and not self.seen_title:
            self.seen_title = True
            self.page_title = whole
            if self.hand.get("keep"):
                self.blocks.append(("H", whole.rstrip(".")))
            return
        if purpose == "heading" and not self.seen_title and self.hand.get("keep") and len(whole) < 140:
            self.seen_title = True
            self.page_title = whole
            self.blocks.append(("H", whole.rstrip(".")))
            return
        # a short text that is a link as a whole
        if link and len(whole) < 140:
            self.blocks.append(("A", "%s | %s" % (re.sub(r"\[(.*?)\]\(.*?\)", r"\1", whole), tidy_link(link))))
            return
        # headings
        short = len(whole) < 140 and not any(not t for t in plain[1:-1])
        if purpose in ("sectionTitle", "pageTitle") and short:
            self.blocks.append(("H", whole.rstrip(".")))
            return
        if purpose == "heading" and short and len(whole) < 90:
            self.blocks.append(("H", whole.rstrip(".")))
            return
        # body text, line by line
        some_plain = any(any(not p["bold"] and p["text"].strip() for p in l) for l in lines)
        open_par = False
        for pieces, t in zip(lines, plain):
            if not t or DECORATION.match(t) or DECORATION.match("".join(p["text"] for p in pieces)):
                open_par = False
                continue
            bold = all(p["bold"] for p in pieces if p["text"].strip())
            m = BULLET.match(t)
            if m:
                self.blocks.append(("LI", m.group(1)))
                open_par = False
            elif bold and some_plain and len(t) < 90 and "](" not in t:
                self.blocks.append(("H", t.rstrip(".")))
                open_par = False
            elif open_par:
                self.blocks.append(("+", t))
            else:
                self.blocks.append(("P", t))
                open_par = True

    # ---- a grid: reading order, and the short labels that belong to a picture or a video
    def grid(self, c):
        kids = children(c)
        kind_of = lambda k: ((k.get("block") or {}).get("content") or {}).get("contentType")
        def rect(k):
            p, z = k.get("position") or {}, k.get("size") or {}
            return p.get("x", 0), p.get("y", 0), z.get("width", 1), z.get("height", 1)
        def label(k):
            if kind_of(k) != "text":
                return None
            cc = k["block"]["content"]
            if cc.get("purpose") in ("sectionTitle", "pageTitle", "heading"):
                return None
            raw = "".join(r["text"] for r in runs_of(cc.get("utf")))
            text = " ".join(raw.split())
            if not text or len(text) > 44 or DECORATION.match(text) or parse_date(text) or "kutikama" in text:
                return None
            if (k["block"].get("actions") or {}).get("tap"):
                return None
            return text
        media = [k for k in kids if kind_of(k) in ("video", "image", "photoGallery")]
        owner, taken = {}, set()
        for k in kids:
            if label(k) is None:
                continue
            x, y, w, h = rect(k)
            best = None
            for m in media:
                mx, my, mw, mh = rect(m)
                if x < mx + mw and mx < x + w and y < my + mh and my < y + h:       # the label sits on it
                    best = m
                    break
            if best is None:
                for m in media:
                    mx, my, mw, mh = rect(m)
                    if kind_of(m) == "video" and my == y + h and x < mx + mw and mx < x + w:   # the label sits right above a video
                        best = m
                        break
            if best is not None:
                owner.setdefault(id(best), []).append(k)
                taken.add(id(k))
        for k in kids:
            if id(k) in taken:
                continue
            self.block(k["block"])
            for t in owner.get(id(k), []):
                self.caption(t["block"]["content"])

    def caption(self, c):
        pieces = [p for line in lines_of(runs_of(c.get("utf"))) for p in line + [dict(text=" ", bold=False, href=None)]]
        t = " ".join(line_text(pieces).split())
        m = re.fullmatch(r"(.*?)\[(.+?)\]\((.+?)\)(.*)", t)
        if m:
            before, inside, href, after = m.group(1).strip(), m.group(2).strip(), m.group(3), m.group(4).strip()
            wordy = lambda x: not x or re.fullmatch(r"[\w .'’-]+", x)
            if wordy(before) and wordy(after):
                t = "[%s](%s)" % (" ".join(x for x in (before, inside, after) if x), href)
            elif wordy(after):
                t = "%s [%s](%s)" % (before, " ".join(x for x in (inside, after) if x), href)
        self.blocks.append(("CAP", t))

    # ---- everything
    def block(self, b):
        c = b.get("content") or {}
        kind = c.get("contentType")
        link = None
        for t in (b.get("actions") or {}).get("tap") or []:
            if t.get("type") == "linkToWeb" and t.get("destination"):
                link = t["destination"]
        if kind in ("flexGrid", "grid"):
            self.grid(c)
        elif kind == "text":
            self.text(c, link)
        elif kind == "image":
            o = c.get("originalSize") or {}
            n = self.image((c.get("picture") or {}).get("fullSizeImageUrl") or (c.get("picture") or {}).get("imageUrl"), (o.get("width"), o.get("height")))
            if n:
                self.blocks.append(("IMG", "%d | %s" % (n, tidy_link(link)) if link else str(n)))
        elif kind == "photoGallery":
            ns = []
            for p in c.get("pictures") or []:
                v = ((p.get("variations") or {}).get("default") or [{}])[-1]
                ns.append(self.image(p.get("fullSizeImageUrl") or p.get("imageUrl"), (v.get("width"), v.get("height"))))
            ns = [n for n in ns if n]
            if ns:
                self.blocks.append(("GAL", " ".join(str(n) for n in ns)))
        elif kind == "video":
            name = (c.get("videoUrl") or "").rsplit("/", 1)[-1]
            if name:
                self.videos.append(name)
                poster = asset_id(c.get("placeholderUrl"))
                if poster:
                    self.posters[name] = poster
                self.blocks.append(("VID", name))
        elif kind == "longVideo":
            vid = str(c.get("videoId"))
            self.missing.append(vid)
            ratio = (c.get("contentHeight") or {}).get("value") or {}
            self.blocks.append(("MISSING-VIDEO", "%s | %s:%s" % (vid, ratio.get("width", 16), ratio.get("height", 9))))
        elif kind in ("youtube", "vimeo"):
            url = c.get("contentUrl") or ""
            m = re.search(r"(?:v=|youtu\.be/|vimeo\.com/)([A-Za-z0-9_-]+)", url)
            if m:
                self.blocks.append(("YT" if kind == "youtube" else "VM", "%s | %s" % (m.group(1), clean(c.get("title") or ""))))
        elif kind == "code":
            code = c.get("code") or ""
            m = re.search(r'<iframe[^>]*src="([^"]+)"[^>]*?(?:title="([^"]*)")?[^>]*>', code)
            if m and len(code) < 2000:
                title = re.search(r'title="([^"]*)"', code)
                self.blocks.append(("EMBED", "slides | %s | %s" % (m.group(1), title.group(1) if title else "")))
                self.embeds.append("slides")
            else:
                name = self.hand["key"] + "-widget"
                self.blocks.append(("EMBED", "%s | | " % name))
                self.embeds.append(name)
                save_embed(name, code)
        # shapes are decoration: nothing to keep


def save_embed(name, code):
    """A thing that sits in a page is a small page of its own. It is saved in assets/embeds and shown in a frame.
    Its background is set to black so it sits on the page without a border."""
    site = os.path.join(HERE, "..", "site")
    if not os.path.isdir(site):
        site = os.path.join(HERE, "..")
    folder = os.path.join(site, "assets", "embeds")
    os.makedirs(folder, exist_ok=True)
    patch = "<style>body{background:#000;padding:0 0 12px;min-height:0}.stage{border-radius:0}</style>"
    code = code.replace("</head>", patch + "</head>", 1) if "</head>" in code else patch + code
    code = code.replace(" \u2014 ", ", ")           # the house writes no long dashes
    with open(os.path.join(folder, name + ".html"), "w", encoding="utf-8") as f:
        f.write(code)


def read_note(slug):
    d = json.load(open(os.path.join(SRC, "research", slug, "page-data.json"), encoding="utf-8"))
    doc = d["props"]["pageProps"]["value"]["document"]
    root = doc["content"]["content"]
    note = Note(slug)
    for page in root.get("pages") or []:
        if page.get("contentType") == "section" and page.get("content"):
            sec = page["content"]
            for b in (sec if isinstance(sec, list) else [sec]):
                note.block(b)
    meta = json.load(open(os.path.join(SRC, "research", slug, "meta.json"), encoding="utf-8"))
    note.description = clean(meta.get("description") or "").strip("“”\"")
    note.changed = (meta.get("last_changed") or "")[:10]
    return note


# Repairs written by hand, note by note.
#   ("head", start)            the paragraph that starts like this is a heading
#   ("head", start, new text)  the same, with the heading written again
#   ("join", start)            the paragraph that starts like this and the next one are one sentence
#   ("letters", new heading)   a word set one letter per line becomes a heading
FIXES = {
    "sxsw-sydney-2023": [("head", "ABOUT LA LUCHA", "About La Lucha"), ("head", "ABOUT PRISONX", "About Prison X"),
                         ("head", "Highlights and Reviews", "Highlights and reviews")],
    "aug-19-2023": [("head", "Highlights and Reviews", "Highlights and reviews")],
    "brain-jam-games-for-change-nyc": [("head", "In Which We Reflect")],
    "aug-20-2023": [("join", "Follow us on")],
    "policy-recommendations-nsw-arts-culture-tech-equity": [
        ("head", "Where should the NSW Government"), ("head", "What barriers can the NSW Government"),
        ("head", "What does NSW do well"), ("head", "What's your BIG idea"), ("head", "What’s your BIG idea"),
        ("letters", "Art Tech Exchange")],
}


def tidy(slug, blocks):
    """Small repairs after reading: drop doubles, then the repairs written by hand."""
    out = []
    for tag, text in blocks:
        if out and out[-1] == (tag, text) and tag in ("P", "H", "A"):
            continue
        out.append((tag, text))
    for fix in FIXES.get(slug, []):
        if fix[0] == "head":
            for i, (tag, text) in enumerate(out):
                if tag in ("P", "H") and text.startswith(fix[1]):
                    out[i] = ("H", fix[2] if len(fix) > 2 else text.rstrip(".:"))
        elif fix[0] == "join":
            for i, (tag, text) in enumerate(out[:-1]):
                if tag == "P" and text.startswith(fix[1]) and out[i + 1][0] == "P":
                    out[i:i + 2] = [("P", text + " " + out[i + 1][1])]
                    break
        elif fix[0] == "letters":
            keep, run = [], []
            for tag, text in out + [("END", "")]:
                if tag in ("P", "+") and len(text.replace(" ", "")) <= 2:
                    run.append(text)
                    continue
                if len(run) >= 5:
                    keep.append(("H", fix[1]))
                elif run:
                    keep += [("P", r) for r in run]
                run = []
                if tag != "END":
                    keep.append((tag, text))
            out = keep
    return out


def summary_of(slug, description):
    if slug in SUMMARIES:
        return clean(SUMMARIES[slug])
    first = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ“\"])", description)
    s = first[0] if first else ""
    if len(s) < 70 and len(first) > 1:
        s += " " + first[1]
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    notes, manifest = [], []
    for slug, hand in NOTES.items():
        n = read_note(slug)
        blocks = tidy(slug, n.blocks)
        summary = summary_of(slug, n.description)
        lines = ["T: " + hand["title"], "D: " + n.description, "S: " + summary]
        lines += ["%s: %s" % (tag, text) for tag, text in blocks]
        with open(os.path.join(OUT, slug + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        notes.append(dict(slug=slug, key=hand["key"], title=hand["title"], page_title=n.page_title, iso=n.iso, place=n.place,
                          images=n.images, sizes=n.sizes, videos=n.videos, posters=n.posters, missing=n.missing, embeds=n.embeds,
                          changed=n.changed, blocks=len(blocks)))
        for i, a in enumerate(n.images, 1):
            manifest.append(dict(name="%s-%02d" % (hand["key"], i), note=slug, asset=a))
        for name, a in n.posters.items():
            manifest.append(dict(name="%s-poster-%s" % (hand["key"], name[:8]), note=slug, asset=a, poster=name))
    notes.sort(key=lambda x: x["iso"] + "~", reverse=True)
    json.dump(notes, open(os.path.join(HERE, "data", "research.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(manifest, open(os.path.join(HERE, "data", "research-manifest.json"), "w", encoding="utf-8"), indent=1)
    words = 0
    for n in notes:
        text = open(os.path.join(OUT, n["slug"] + ".txt"), encoding="utf-8").read()
        w = len(re.sub(r"^(IMG|GAL|VID|YT|VM|EMBED|MISSING-VIDEO):.*$", "", text, flags=re.M).split())
        words += w
        print("%-10s %-10s %4dw %2dimg %2dvid %dmiss %-3s %s" % (n["iso"] or "no date", n["place"][:10], w, len(n["images"]), len(n["videos"]),
                                                              len(n["missing"]), "emb" if n["embeds"] else "", n["title"][:58]))
    print(len(notes), "notes,", words, "words,", sum(len(n["images"]) for n in notes), "pictures,", sum(len(n["videos"]) for n in notes), "short videos,",
          sum(len(n["missing"]) for n in notes), "videos left on the old host,", len(manifest), "files to make")


if __name__ == "__main__":
    main()
