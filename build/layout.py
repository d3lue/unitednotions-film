"""Builds the maze for each screen width from the content and the colours."""
from __future__ import annotations

import json
import math
import os
import random

import content
import halls
import i18n
import typo
from colour import palette_position
from maze import Band, Card, Maze, Photo, Spec, Work, pack

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK_HEAD = -0.045          # letter spacing of the headline face, in em

# One maze per screen width.
# cols: grid columns. design: the screen width the sizes below are drawn for (px).
# from_px: the screen width from which this maze is used.
LAYOUTS = {
    "wide": dict(
        cols=24, design=1440, from_px=1200,
        spec=dict(tiers={"S": (12, 20), "M": (22, 34), "L": (38, 56)}, minw=3, minh=3, tol=0.15, corridor=0.7, work_gap=3),
        res=100, header=72,
        type=dict(pad=30, meta=13.5, tmax=132, tmin=58, quote=20, qlh=1.38, attr=13, link=15,
                  card=38, cardmax=54, intro=21, ilh=1.38, more=15, statement=64),
        work_side=(7, 9), work_room_w=(6, 10), work_stack=(9, 12),
        card_w=(5, 9), intro_w=(7, 10), statement_fit=True,
        density=0.56,
    ),
    "medium": dict(
        cols=16, design=900, from_px=700,
        spec=dict(tiers={"S": (9, 15), "M": (15, 24), "L": (28, 40)}, minw=3, minh=3, tol=0.16, corridor=0.6, work_gap=3),
        res=90, header=64,
        type=dict(pad=26, meta=13, tmax=104, tmin=48, quote=18, qlh=1.38, attr=12.5, link=14.5,
                  card=32, cardmax=44, intro=19, ilh=1.38, more=14.5, statement=56),
        work_side=None, work_room_w=(8, 13), work_stack=(8, 13),
        card_w=(5, 8), intro_w=(7, 10), statement_fit=True,
        density=0.56, exit_h=3,
    ),
    "narrow": dict(
        cols=12, design=390, from_px=0,
        spec=dict(tiers={"S": (12, 20), "M": (24, 36), "L": (40, 66)}, minw=4, minh=3, tol=0.17, corridor=0.5, work_gap=1, pass_w=1),
        res=80, header=60,
        type=dict(pad=20, meta=12.5, tmax=84, tmin=40, quote=17, qlh=1.4, attr=12.5, link=15,
                  card=30, cardmax=36, intro=18.5, ilh=1.38, more=15, statement=46),
        work_side=None, work_room_w=(11, 11), work_stack=(11, 11),
        card_w=(12, 12), intro_w=(12, 12), statement_fit=False,
        halls=False,        # no room for words in the corridors of a phone
        exit_h=7,
        density=0.6,
    ),
}


def unit(name):
    L = LAYOUTS[name]
    return L["design"] / L["cols"]


def load():
    colour = json.load(open(os.path.join(HERE, "data", "colour.json")))
    rend = json.load(open(os.path.join(HERE, "data", "renditions.json")))
    quotes = json.load(open(os.path.join(HERE, "data", "quotes-from-old-site.json")))
    return colour, rend, quotes


def palette_order(colour):
    def key(slug):
        g, t = palette_position(colour[slug], "day")
        return (g, t) if slug not in content.NUDGE else content.NUDGE[slug]
    return sorted((p["slug"] for p in content.PHOTOS), key=key)


def source_name(raw):
    return content.SOURCE_NAMES.get(raw, raw)


def work_note(work, quotes):
    """What a work's room says under its title: a press quote, or a fact."""
    if work.get("quote") is not None and work.get("qkey"):
        q = quotes[work["qkey"]]["quotes"][work["quote"]]
        return dict(kind="quote", text=q["text"], source=source_name(q["source"]))
    if work.get("award"):
        return dict(kind="fact", text=work["award"], source="")
    return dict(kind="fact", text=work["facts"][0], source="")


# ------------------------------------------------------------------ how much room the words need
def work_room_type(name, work, note, w_cols, h_rows=None, compact=False):
    """Sizes for the text of a work's room that is w_cols wide. Returns None if it cannot fit.
    compact: the smallest comfortable setting, used to ask the maze for space.
    Without it the title grows to fill the room it was given."""
    L = LAYOUTS[name]
    T, u = L["type"], unit(name)
    tmax = T["tmax"] * (0.7 if compact else 1.0)
    inner = w_cols * u - 2 * T["pad"]
    words = work["title"].split()
    meta_h = T["meta"] * 1.5
    note_text = ("“%s”" % note["text"]) if note["kind"] == "quote" else note["text"]
    note_lines = typo.wrap(note_text, inner, "text", T["quote"], 0.01)
    note_h = len(note_lines) * T["quote"] * T["qlh"] + (8 + T["attr"] * 1.5 if note["source"] else 0)
    link_h = T["link"] * 1.5
    fixed = 2 * T["pad"] + meta_h + 6 + 16 + note_h + 16 + link_h
    best = None
    for n in range(1, min(len(words), 3) + 1):
        size, lines = typo.fit(work["title"], inner, n, "head", lo=T["tmin"] * 0.5, hi=tmax, tracking=TRACK_HEAD, step=1.0)
        if len(lines) > n or any(typo.width(l, "head", size, TRACK_HEAD) > inner for l in lines):
            continue
        if h_rows is not None:
            room = h_rows * u - fixed
            size = min(size, room / (len(lines) * 0.88))
        if size < T["tmin"]:
            continue
        total = fixed + len(lines) * size * 0.88
        cand = dict(size=round(size, 1), lines=lines, total=total, note_lines=len(note_lines))
        # fewer lines win unless more lines give clearly bigger letters
        score = size / (1 + 0.22 * (len(lines) - 1))
        if best is None or score > best[0]:
            best = (score, cand)
    return best[1] if best else None


def work_room_need(name, work, note):
    L = LAYOUTS[name]
    u = unit(name)
    need = {}
    for w in range(L["work_room_w"][0], L["work_room_w"][1] + 1):
        t = work_room_type(name, work, note, w, compact=True)
        if t:
            need[w] = max(4, math.ceil(t["total"] / u))
    return need


def card_type(name, text, source, w_cols, h_rows=None):
    L = LAYOUTS[name]
    T, u = L["type"], unit(name)
    inner = w_cols * u - 2 * T["pad"]
    attr_h = 10 + T["attr"] * 1.5
    best = None
    size = T["cardmax"] if h_rows is not None else T["card"]
    while size >= T["card"] * 0.6:
        lines = typo.wrap("“%s”" % text, inner, "head", size, -0.02)
        fits = all(typo.width(l, "head", size, -0.02) <= inner for l in lines)
        total = 2 * T["pad"] + len(lines) * size * 1.02 + attr_h
        if fits and (h_rows is None or total <= h_rows * u):
            best = dict(size=round(size, 1), lines=len(lines), total=total)
            break
        size -= 1
    return best


def card_need(name, text, source):
    L = LAYOUTS[name]
    u = unit(name)
    need = {}
    for w in range(L["card_w"][0], L["card_w"][1] + 1):
        t = card_type(name, text, source, w)
        if t and t["lines"] <= 5:
            need[w] = max(3, math.ceil(t["total"] / u))
    return need


def intro_need(name):
    L = LAYOUTS[name]
    T, u = L["type"], unit(name)
    need = {}
    for w in range(L["intro_w"][0], L["intro_w"][1] + 1):
        inner = w * u - 2 * T["pad"]
        a = typo.wrap(content.INTRO, inner, "text", T["intro"], 0.02)
        b = typo.wrap(content.INTRO_MORE, inner, "text", T["more"], 0.03)
        c = typo.wrap(content.HOW_TO_WALK, inner, "text", T["more"], 0.03)
        total = (2 * T["pad"] + len(a) * T["intro"] * T["ilh"] + 14 + len(b) * T["more"] * 1.5
                 + 12 + len(c) * T["more"] * 1.5 + 16 + T["link"] * 1.6)
        need[w] = math.ceil(total / u)
    return need


def title_type(name):
    """The big name at the top. One line on wide screens, three lines on a phone."""
    L = LAYOUTS[name]
    u = unit(name)
    inner = L["design"] - 2 * (24 if name != "narrow" else 16)
    if name == "narrow":
        lines = ["United", "Notions", "Film"]
    else:
        lines = ["United Notions Film"]
    widest = max(typo.width(l, "head", 100, TRACK_HEAD) for l in lines)
    size = inner / widest * 100
    block = len(lines) * size * 0.84
    rows = math.ceil((L["header"] + block + (30 if name != "narrow" else 26)) / u)
    return dict(size=round(size, 1), lines=lines, rows=rows)


def statement_type(name, text):
    L = LAYOUTS[name]
    T, u = L["type"], unit(name)
    side = 24 if name != "narrow" else 16
    inner = L["design"] - 2 * side
    if L["statement_fit"]:
        size = inner / typo.width(text, "head", 100, TRACK_HEAD) * 100
        rows = max(2, math.ceil((size * 0.95 + 2 * 0.42 * u) / u))
        return dict(size=round(size, 1), lines=[text], rows=rows, fit=True)
    size = T["statement"]
    lines = typo.wrap(text, inner, "head", size, TRACK_HEAD)
    rows = math.ceil((len(lines) * size * 0.9 + 2 * 0.75 * u) / u)
    return dict(size=size, lines=lines, rows=rows, fit=False)


def hall_lines(quotes):
    """The short press lines for the corridors: with and without the name of the work."""
    out = []
    for w in content.WORKS:
        for qi in w["hall"]:
            q = quotes[w["qkey"]]["quotes"][qi]
            source = source_name(q["source"])
            out.append(dict(key="%s-%d" % (w["slug"], qi), work=w["slug"], title=w["title"], text=q["text"], source=source,
                            short="\u201c%s\u201d %s" % (q["text"], source),
                            long="\u201c%s\u201d %s%s%s" % (q["text"], source, i18n.t(", on "), w["title"])))
    return out


# ------------------------------------------------------------------ the order of things
def sequence(name, colour, rend, quotes):
    L = LAYOUTS[name]
    photos = {p["slug"]: p for p in content.PHOTOS}
    order = palette_order(colour)
    keys = {w["key"]: w for w in content.WORKS}

    def photo(slug, tier=None):
        r = rend[slug]
        return Photo(slug, r["ow"] / r["oh"], tier or photos[slug]["tier"], maxw=max(L["spec"]["minw"], r["ow"] // L["res"]))

    cards_after = {}
    for w in content.WORKS:
        if not w["cards"]:
            continue
        mine = [s for s in order if photos[s]["work"] == w["slug"] and s != w["key"]]
        for n, qi in enumerate(w["cards"]):
            host = mine[n % len(mine)] if mine else w["key"]
            q = quotes[w["qkey"]]["quotes"][qi]
            need = card_need(name, q["text"], source_name(q["source"]))
            cards_after.setdefault(host, []).append(Card("quote-%s-%d" % (w["slug"], qi), "quote", need))

    seq = [Band("title", "title", title_type(name)["rows"]), Card("intro", "intro", intro_need(name), grow=0)]
    n = len(order)
    marks = {round(n * f): i for i, f in enumerate((0.22, 0.52, 0.80))}
    for i, slug in enumerate(order):
        if i in marks:
            k = marks[i]
            seq.append(Band("statement-%d" % k, "statement", statement_type(name, content.STATEMENTS[k])["rows"], slack=5))
        if slug in keys:
            w = keys[slug]
            need = work_room_need(name, w, work_note(w, quotes))
            seq.append(Work("work-" + w["slug"], photo(slug, "L"), need,
                            side_h=L["work_side"] or (0, -1), stack_w=L["work_stack"],
                            orient="any" if L["work_side"] else "stack"))
        else:
            seq.append(photo(slug))
        seq.extend(cards_after.get(slug, []))
    seq.append(Band("exit", "exit", L.get("exit_h", 2)))
    return seq, order


def spots_for(rects):
    """Where a visitor stands in each room: a quarter unit inside its top left corner.
    In the room of the big name it is the bottom left corner, under the letters."""
    out = {}
    for r in rects:
        if r.kind != "room":
            continue
        if r.role == "title":
            out[r.id] = (r.x + 0.25, r.y1 - 0.25)
        else:
            out[r.id] = (r.x + 0.25, r.y + 0.25)
    return out


def reachable(graph, start):
    n = len(graph["nodes"]) // 2
    adj = [[] for _ in range(n)]
    e = graph["edges"]
    for k in range(0, len(e), 2):
        adj[e[k]].append(e[k + 1])
        adj[e[k + 1]].append(e[k])
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def guide(out):
    """The line that leads a visitor through the maze as the page scrolls.
    It starts under the big name and passes every main room from top to bottom: the introduction, the works, the three lines, the exit.
    Returns the nodes of the walk graph it passes, in order."""
    import heapq
    g = out["walk"]
    nodes, edges, spots = g["nodes"], g["edges"], g["spots"]
    n = len(nodes) // 2
    adj = [[] for _ in range(n)]
    for k in range(0, len(edges), 2):
        a, b = edges[k], edges[k + 1]
        d = abs(nodes[2 * a] - nodes[2 * b]) + abs(nodes[2 * a + 1] - nodes[2 * b + 1])
        adj[a].append((b, d))
        adj[b].append((a, d))

    def route(a, b):
        dist, prev = {a: 0}, {}
        heap = [(0, a)]
        while heap:
            d, u = heapq.heappop(heap)
            if u == b:
                break
            if d > dist.get(u, 1e18):
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist.get(v, 1e18):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(heap, (nd, v))
        if b not in dist:
            return None
        path = [b]
        while path[-1] != a:
            path.append(prev[path[-1]])
        return path[::-1]

    start = spots.get("title")
    if start is None:
        return []
    rooms = [r for r in out["rects"] if r.kind == "room" and r.role in ("intro", "work", "statement", "exit") and r.id in spots]
    rooms.sort(key=lambda r: (nodes[2 * spots[r.id] + 1], nodes[2 * spots[r.id]]))
    path = [start]
    for r in rooms:
        leg = route(path[-1], spots[r.id])
        if leg:
            path += leg[1:]
    return path


def build(name, tries=600, seed=1, carve_seed=None, prune=0.0, density=None, attempts=20):
    colour, rend, quotes = load()
    L = LAYOUTS[name]
    spec = Spec(cols=L["cols"], **L["spec"])
    seq, order = sequence(name, colour, rend, quotes)
    best = None
    for attempt in range(attempts):
        rects, rows, info = pack(seq, spec, tries=tries, seed=seed + attempt)
        mz = Maze(rects, spec.cols, rows)
        # corridors are cut from room to room: first the big name, the works, the three lines and the exit,
        # in the order of their height on the page, then every other room
        rooms = [r for r in rects if r.kind == "room"]
        main = sorted((r for r in rooms if r.role in ("title", "work", "statement", "exit")), key=lambda r: (r.y + r.h / 2.0, r.x))
        rest = sorted((r for r in rooms if r.role not in ("title", "work", "statement", "exit")), key=lambda r: (r.y, r.x))
        waypoints = []
        for r in main + rest:
            node = ("R", mz.room_region[r.id])
            if node not in waypoints:
                waypoints.append(node)
        rng = random.Random((carve_seed if carve_seed is not None else seed + attempt) * 7919 + 13)
        placed, reserved = ({}, [])
        if L.get("halls", True):
            placed, reserved = halls.find(mz, unit(name), spec.corridor, hall_lines(quotes))
        mz.carve(waypoints, rng, prune=prune, density=L.get("density", 1.0) if density is None else density, reserved=reserved)
        mz.halls = placed
        info["attempt"] = attempt
        info["halls"] = len(placed)
        # a good maze: a visitor who starts under the big name can walk to every room
        spots = spots_for(rects)
        graph = mz.walk_graph(spots)
        start = graph["spots"].get("title")
        seen = reachable(graph, start) if start is not None else set()
        lost = [rid for rid in spots if graph["spots"].get(rid) not in seen]
        lost_works = [rid for rid in lost if rid.startswith("work-")]
        info["lost"] = lost
        quality = (len(lost_works) * 10 + len(lost) + (0 if start is not None else 100), info["score"])
        if best is None or quality < best[0]:
            best = (quality, rects, rows, info, mz, graph)
        if not lost and start is not None:
            break
    _, rects, rows, info, mz, graph = best
    area = spec.cols * rows
    photo_area = sum(r.w * r.h for r in rects if r.kind == "photo")
    info["photo_share"] = round(photo_area / area, 3)
    info["walk_nodes"] = len(graph["nodes"]) // 2
    return dict(name=name, layout=L, spec=spec, rects=rects, rows=rows, maze=mz, info=info, order=order, quotes=quotes, walk=graph)


if __name__ == "__main__":
    import sys
    for nm in sys.argv[1:] or ["wide"]:
        out = build(nm)
        mz = out["maze"]
        nopen = sum(1 for s in mz.segments if s.open)
        print(nm, "rows", out["rows"], out["info"], "segments", len(mz.segments), "open", nopen)
