"""The maze.

Step 1, pack():   lay the pictures and the text rooms on a grid, in palette order,
                  like a collage. Pictures keep their shape as far as possible.
Step 2, carve():  every border between two pictures can be a corridor. A real maze
                  is cut into those borders: one tree of corridors, no loops, so there
                  is exactly one way between any two rooms. Where a border stays closed
                  the two pictures touch, and together the pictures form the walls.
Step 3, thread(): the one route that leads from the entrance through the rooms to the exit.

All coordinates are in grid units. Nothing here knows about pixels or HTML.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


# ------------------------------------------------------------------ items to place
@dataclass
class Photo:
    slug: str
    aspect: float          # width / height of the picture
    tier: str = "M"        # S, M, L, XL
    maxw: int = 99         # widest it may be shown (low resolution pictures stay small)


@dataclass
class Card:                # a black room with text
    id: str
    role: str              # intro, quote
    need: dict             # width in columns -> rows the text needs at that width
    grow: int = 1          # how many extra rows it may take to line up with a neighbour


@dataclass
class Work:                # the key picture of a work with its room attached
    id: str
    photo: Photo
    need: dict             # room width in columns -> rows its text needs
    side_h: tuple = (7, 9)       # picture beside room: allowed heights
    stack_w: tuple = (9, 12)     # picture above room: allowed widths
    orient: str = "any"    # side, stack, any


@dataclass
class Band:                # a room as wide as the page
    id: str
    role: str              # title, statement, exit
    h: int
    slack: int = 0         # how many more pictures may be placed first, waiting for an even row


@dataclass
class Spec:
    cols: int
    tiers: dict            # tier -> (area_min, area_max) in grid cells
    minw: int = 3
    minh: int = 3
    tol: float = 0.15      # how far a picture may be cropped (log of the ratio)
    work_gap: int = 0      # columns a work must leave free beside it, so a corridor can pass
    pass_w: int = 0        # narrow screens: no picture is as wide as the page, this many columns stay free as a way past
    lookahead: int = 3
    corridor: float = 0.7  # corridor width in grid units


@dataclass
class Rect:
    id: str
    kind: str              # photo, room
    x: int
    y: int
    w: int
    h: int
    role: str = ""
    crop: float = 0.0

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h


# ------------------------------------------------------------------ step 1: pack
class Packer:
    def __init__(self, spec: Spec, rng: random.Random):
        self.spec = spec
        self.rng = rng
        self.C = spec.cols
        self.H = [0] * self.C
        self.rects: list[Rect] = []
        self.void = 0
        self.cost = 0.0

    # -- helpers
    def lowest_slot(self):
        y = min(self.H)
        x0 = self.H.index(y)
        x1 = x0
        while x1 < self.C and self.H[x1] == y:
            x1 += 1
        hl = self.H[x0 - 1] - y if x0 > 0 else None
        hr = self.H[x1] - y if x1 < self.C else None
        return x0, x1, y, hl, hr

    def put(self, rect: Rect):
        self.rects.append(rect)
        for c in range(rect.x, rect.x1):
            self.H[c] = rect.y1

    def raise_to(self, x0, x1, top):
        """Fill the columns x0..x1 up to `top`. Stretch the tiles above the gap when
        they can take it, otherwise leave the gap black (it becomes open floor)."""
        c = x0
        while c < x1:
            y = self.H[c]
            e = c
            while e < x1 and self.H[e] == y:
                e += 1
            gap = top - y
            if gap > 0:
                above = [r for r in self.rects if r.y1 == y and r.x >= c and r.x1 <= e]
                covered = sum(r.w for r in above)
                for r in above:
                    ok = True
                    if r.kind == "photo":
                        new = abs(math.log((r.w / (r.h + gap)) / r._aspect))
                        ok = new <= self.spec.tol * 1.35
                        if ok:
                            self.cost += (new - r.crop) * 3.0
                            r.crop = new
                    else:
                        ok = False
                    if ok:
                        r.h += gap
                    else:
                        self.void += r.w * gap
                self.void += (e - c - covered) * gap
                for k in range(c, e):
                    self.H[k] = top
            c = e

    def rooms_touching(self, x, y, w, h):
        """How many text rooms a new room at this place would touch. Two rooms side by side
        read as one black block, so the maze keeps them apart where it can."""
        n = 0
        for r in self.rects:
            if r.kind != "room" or r.role in ("title", "statement", "exit"):
                continue
            overlap_y = min(r.y1, y + h) - max(r.y, y)
            overlap_x = min(r.x1, x + w) - max(r.x, x)
            if overlap_y > 0 and (r.x1 == x or r.x == x + w):
                n += 1
            elif overlap_x > 0 and (r.y1 == y or r.y == y + h):
                n += 1
        return n

    # -- pictures
    def photo_options(self, p: Photo, sw, hl, hr, relax=1.0):
        s = self.spec
        a0, a1 = s.tiers[p.tier]
        out = []
        for w in range(s.minw, min(sw, p.maxw) + 1):
            rem = sw - w
            if s.pass_w and sw == self.C:
                if rem != s.pass_w and rem < s.minw:
                    continue        # a picture as wide as the page would close the maze
            elif rem != 0 and rem < s.minw:
                continue
            ideal = w / p.aspect
            cands = {round(ideal), math.floor(ideal), math.ceil(ideal)}
            for snap in (hl, hr):
                if snap:
                    cands.add(snap)
            for h in cands:
                if h < s.minh:
                    continue
                err = abs(math.log((w / h) / p.aspect))
                if err > s.tol * relax:
                    continue
                area = w * h
                if area < a0 * 0.75 / relax or area > a1 * 1.3 * relax:
                    continue
                cost = err * 3.0
                if area < a0:
                    cost += (a0 - area) / a0 * 1.6
                if area > a1:
                    cost += (area - a1) / a1 * 1.6
                if h == hl or h == hr:
                    cost -= 0.4
                if rem == 0:
                    cost -= 0.3
                cost += self.rng.random() * 0.25
                out.append((cost, w, h, err))
        return out

    def card_options(self, c: Card, sw, hl, hr):
        s = self.spec
        out = []
        for w, need in c.need.items():
            if w > sw:
                continue
            rem = sw - w
            if rem != 0 and rem < s.minw:
                continue
            for h in range(need, need + c.grow + 1):
                cost = 0.2 + (h - need) * 0.25 + w * h * 0.012 + self.rng.random() * 0.25
                if h == hl or h == hr:
                    cost -= 0.4
                if rem == 0:
                    cost -= 0.3
                out.append((cost, w, h, 0.0))
        return out

    def place_in_slot(self, item, opts, x0, x1, y, hl, hr):
        cost, w, h, err = min(opts)
        rem = (x1 - x0) - w
        if rem == 0:
            x = x0
        elif isinstance(item, Card) and item.role == "intro":
            x = x0
        elif isinstance(item, Card):
            left = self.rooms_touching(x0, y, w, h)
            right = self.rooms_touching(x1 - w, y, w, h)
            x = x0 if left < right else (x1 - w if right < left else (x0 if self.rng.random() < 0.5 else x1 - w))
            self.cost += min(left, right) * 0.8
        elif h == hl and h != hr:
            x = x0
        elif h == hr and h != hl:
            x = x1 - w
        else:
            x = x0 if self.rng.random() < 0.5 else x1 - w
        if isinstance(item, Photo):
            r = Rect(item.slug, "photo", x, y, w, h, crop=err)
            r._aspect = item.aspect
        else:
            r = Rect(item.id, "room", x, y, w, h, role=item.role)
        self.cost += cost
        self.put(r)

    # -- works: a key picture with its room
    def work_options(self, wk: Work):
        s = self.spec
        a = wk.photo.aspect
        out = []
        if wk.orient in ("side", "any"):
            for rw, need in wk.need.items():
                for h in range(max(need, wk.side_h[0]), wk.side_h[1] + 1):
                    for wp in {round(a * h), math.floor(a * h), math.ceil(a * h)}:
                        if wp < s.minw or wp > wk.photo.maxw or wp + rw > self.C - s.work_gap:
                            continue
                        err = abs(math.log((wp / h) / a))
                        if err > s.tol:
                            continue
                        out.append(("side", wp + rw, h, wp, h, rw, h, err))
        if wk.orient in ("stack", "any"):
            for w in range(wk.stack_w[0], min(wk.stack_w[1], wk.photo.maxw, self.C - s.work_gap) + 1):
                if w not in wk.need:
                    continue
                for hp in {round(w / a), math.floor(w / a), math.ceil(w / a)}:
                    if hp < s.minh:
                        continue
                    err = abs(math.log((w / hp) / a))
                    if err > s.tol:
                        continue
                    out.append(("stack", w, hp + wk.need[w], w, hp, w, wk.need[w], err))
        return out

    def try_work(self, wk: Work, force=False, limit=5):
        s = self.spec
        base = min(self.H)
        best = None
        for (orient, W, Hh, wp, hp, rw, rh, err) in self.work_options(wk):
            for x in range(0, self.C - W + 1):
                if x != 0 and x < s.minw and x != s.pass_w:
                    continue
                right = self.C - (x + W)
                if right != 0 and right < s.minw and right != s.pass_w:
                    continue
                y = max(self.H[x:x + W])
                waste = sum(y - self.H[c] for c in range(x, x + W))
                # gaps left beside the block must stay usable
                lgap = self.H[x - 1] - y if x > 0 else 99
                rgap = self.H[x + W] - y if x + W < self.C else 99
                cost = (y - base) * 3.0 + waste * 1.0 + err * 30 + self.rng.random() * 2.0
                cost -= W * 0.6  # bigger is better for a key picture
                if lgap > 0 or rgap > 0:
                    cost -= 1.0  # tucked against a taller neighbour
                cand = (cost, x, y, orient, W, Hh, wp, hp, rw, rh, err, waste)
                if best is None or cand < best:
                    best = cand
        if best is None:
            return False
        cost, x, y, orient, W, Hh, wp, hp, rw, rh, err, waste = best
        if not force and (y - base > limit or waste > W * 2.5):
            return False
        self.raise_to(x, x + W, y)
        room_first = self.rng.random() < 0.5
        if orient == "side":
            a = self.rooms_touching(x, y, rw, rh)              # room on the left
            b = self.rooms_touching(x + wp, y, rw, rh)         # room on the right
            if a != b:
                room_first = a < b
            self.cost += min(a, b) * 0.8
            px = x + (rw if room_first else 0)
            rx = x if room_first else x + wp
            pr = Rect(wk.photo.slug, "photo", px, y, wp, hp, crop=err)
            rr = Rect(wk.id, "room", rx, y, rw, rh, role="work")
        else:
            pr = Rect(wk.photo.slug, "photo", x, y, wp, hp, crop=err)
            rr = Rect(wk.id, "room", x, y + hp, rw, rh, role="work")
            self.cost += self.rooms_touching(x, y + hp, rw, rh) * 0.8
        pr._aspect = wk.photo.aspect
        pr._key = True
        self.put(pr)
        self.put(rr)
        self.cost += err * 3.0
        return True

    # -- main loop
    def run(self, seq):
        s = self.spec
        pending = list(seq)
        waiting: list[tuple[Work, int]] = []   # works that wait for a good place
        slack = {it.id: it.slack for it in seq if isinstance(it, Band)}
        guard = 0
        while pending or waiting:
            guard += 1
            if guard > 5000:
                raise RuntimeError("packer does not finish")
            # works that are waiting go first
            if waiting:
                wk, tries = waiting[0]
                if self.try_work(wk, force=tries >= 6):
                    waiting.pop(0)
                    continue
                waiting[0] = (wk, tries + 1)
                if not pending:
                    self.try_work(wk, force=True)
                    waiting.pop(0)
                    continue
            item = pending[0]
            if isinstance(item, Band):
                top = max(self.H)
                ragged = sum(top - v for v in self.H)
                nxt = pending[1] if len(pending) > 1 else None
                if slack[item.id] > 0 and ragged > self.C * 0.6 and isinstance(nxt, (Photo, Card)):
                    # not even yet: let the next picture in first
                    slack[item.id] -= 1
                    pending[0], pending[1] = pending[1], pending[0]
                    item = pending[0]
                else:
                    while waiting:
                        self.try_work(waiting.pop(0)[0], force=True)
                    top = max(self.H)
                    self.raise_to(0, self.C, top)
                    self.put(Rect(item.id, "room", 0, top, self.C, item.h, role=item.role))
                    pending.pop(0)
                    continue
            if isinstance(item, Work):
                pending.pop(0)
                if not self.try_work(item):
                    waiting.append((item, 0))
                continue
            x0, x1, y, hl, hr = self.lowest_slot()
            sw = x1 - x0
            if sw < s.minw:
                lows = [v for v in (hl, hr) if v]
                self.raise_to(x0, x1, y + min(lows))
                continue
            # the next picture that fits, looking a few ahead
            chosen = None
            for k in range(min(s.lookahead + 1, len(pending))):
                cand = pending[k]
                if isinstance(cand, (Band, Work)):
                    break
                opts = (self.photo_options(cand, sw, hl, hr) if isinstance(cand, Photo)
                        else self.card_options(cand, sw, hl, hr))
                if opts:
                    chosen = (k, cand, opts)
                    self.cost += k * 0.15
                    break
            if chosen is None and isinstance(item, Photo):
                opts = self.photo_options(item, sw, hl, hr, relax=1.7)
                if opts:
                    chosen = (0, item, opts)
                    self.cost += 1.0
            if chosen is None:
                lows = [v for v in (hl, hr) if v]
                if not lows:   # a flat page and nothing fits: should not happen
                    raise RuntimeError("nothing fits a flat row: %r" % (item,))
                self.raise_to(x0, x1, y + min(lows))
                continue
            k, cand, opts = chosen
            pending.pop(k)
            self.place_in_slot(cand, opts, x0, x1, y, hl, hr)
        return self


def grow_into_gaps(rects, cols, rows, tol, keep_pass=False):
    """After packing, let pictures spread into empty floor beside them, as long as
    their shape allows. Returns the number of empty cells that are left."""
    grid = [[None] * cols for _ in range(rows)]
    for i, r in enumerate(rects):
        for y in range(r.y, min(r.y1, rows)):
            for x in range(r.x, r.x1):
                grid[y][x] = i
    changed = True
    while changed:
        changed = False
        for i, r in enumerate(rects):
            if r.kind != "photo" or getattr(r, "_key", False):
                continue
            best = None
            for side in ("down", "up", "right", "left"):
                if side == "down":
                    cells = [(x, r.y1) for x in range(r.x, r.x1)]
                    nw, nh = r.w, r.h + 1
                elif side == "up":
                    cells = [(x, r.y - 1) for x in range(r.x, r.x1)]
                    nw, nh = r.w, r.h + 1
                elif side == "right":
                    cells = [(r.x1, y) for y in range(r.y, r.y1)]
                    nw, nh = r.w + 1, r.h
                else:
                    cells = [(r.x - 1, y) for y in range(r.y, r.y1)]
                    nw, nh = r.w + 1, r.h
                if any(not (0 <= x < cols and 0 <= y < rows) or grid[y][x] is not None for x, y in cells):
                    continue
                if keep_pass and nw >= cols:
                    continue        # leave the way past open
                err = abs(math.log((nw / nh) / r._aspect))
                if err > tol:
                    continue
                if best is None or err < best[0]:
                    best = (err, side, cells)
            if best:
                err, side, cells = best
                for x, y in cells:
                    grid[y][x] = i
                if side == "down":
                    r.h += 1
                elif side == "up":
                    r.y -= 1
                    r.h += 1
                elif side == "right":
                    r.w += 1
                else:
                    r.x -= 1
                    r.w += 1
                r.crop = err
                changed = True
    return sum(1 for row in grid for c in row if c is None)


def pack(seq, spec: Spec, tries=400, seed=1):
    """Try many seeds, keep the layout with the least empty floor and the least cropping."""
    best = None
    for t in range(tries):
        rng = random.Random(seed * 100003 + t)
        try:
            p = Packer(spec, rng).run(seq)
        except RuntimeError:
            continue
        rows = max(p.H)
        left = grow_into_gaps(p.rects, spec.cols, rows, spec.tol * 1.3, keep_pass=bool(spec.pass_w))
        crop = sum(r.crop for r in p.rects if r.kind == "photo")
        score = left * 1.0 + p.cost * 2.0 + crop * 4.0 + rows * 0.15
        if best is None or score < best[0]:
            best = (score, p, t, left)
    if best is None:
        raise RuntimeError("no layout found")
    score, p, t, left = best
    return p.rects, max(p.H), dict(score=round(score, 1), void=left, cost=round(p.cost, 1), seed=t)


# ------------------------------------------------------------------ step 2: carve
@dataclass
class Segment:
    a: object              # node at one end
    b: object              # node at the other end
    p: tuple               # lattice point at end a
    q: tuple               # lattice point at end b
    open: bool = False

    @property
    def horizontal(self):
        return self.p[1] == self.q[1]

    @property
    def length(self):
        return abs(self.p[0] - self.q[0]) + abs(self.p[1] - self.q[1])


class Maze:
    def __init__(self, rects, cols, rows):
        self.rects = rects
        self.C, self.R = cols, rows
        # who owns each cell: index of a photo, or -1 for open floor
        self.owner = [[-1] * cols for _ in range(rows)]
        for i, r in enumerate(rects):
            if r.kind == "photo":
                for yy in range(r.y, r.y1):
                    for xx in range(r.x, r.x1):
                        self.owner[yy][xx] = i
        self._regions()
        self._segments()

    def cell(self, x, y):
        if 0 <= x < self.C and 0 <= y < self.R:
            return self.owner[y][x]
        return None        # outside the page

    # open floor: rooms and gaps, joined where they touch
    def _regions(self):
        self.region = [[-1] * self.C for _ in range(self.R)]
        self.regions = []
        for y in range(self.R):
            for x in range(self.C):
                if self.owner[y][x] == -1 and self.region[y][x] == -1:
                    rid = len(self.regions)
                    cells = []
                    stack = [(x, y)]
                    self.region[y][x] = rid
                    while stack:
                        cx, cy = stack.pop()
                        cells.append((cx, cy))
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < self.C and 0 <= ny < self.R and self.owner[ny][nx] == -1 and self.region[ny][nx] == -1:
                                self.region[ny][nx] = rid
                                stack.append((nx, ny))
                    self.regions.append(cells)
        # which region does each room rect belong to
        self.room_region = {}
        for r in self.rects:
            if r.kind == "room":
                self.room_region[r.id] = self.region[r.y][r.x]

    def node_at(self, i, j):
        """The node a lattice point belongs to: a room if it touches open floor."""
        for dx, dy in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
            x, y = i + dx, j + dy
            if 0 <= x < self.C and 0 <= y < self.R and self.owner[y][x] == -1:
                return ("R", self.region[y][x])
        return ("P", i, j)

    def _is_wall(self, a, b):
        return a is not None and b is not None and a >= 0 and b >= 0 and a != b

    def unit_edges(self, i, j):
        """Borders between two different pictures that leave the lattice point (i, j)."""
        out = []
        if self._is_wall(self.cell(i, j - 1), self.cell(i, j)):
            out.append((1, 0))
        if self._is_wall(self.cell(i - 1, j - 1), self.cell(i - 1, j)):
            out.append((-1, 0))
        if self._is_wall(self.cell(i - 1, j), self.cell(i, j)):
            out.append((0, 1))
        if self._is_wall(self.cell(i - 1, j - 1), self.cell(i, j - 1)):
            out.append((0, -1))
        return out

    def _is_junction(self, i, j):
        if self.node_at(i, j)[0] == "R":
            return True
        e = self.unit_edges(i, j)
        if len(e) != 2:
            return True
        return not (e[0][0] == -e[1][0] and e[0][1] == -e[1][1])

    def _segments(self):
        self.segments: list[Segment] = []
        seen = set()
        for j in range(self.R + 1):
            for i in range(self.C + 1):
                if not self.unit_edges(i, j) or not self._is_junction(i, j):
                    continue
                for dx, dy in self.unit_edges(i, j):
                    if (i, j, dx, dy) in seen:
                        continue
                    x, y = i + dx, j + dy
                    while not self._is_junction(x, y):
                        x, y = x + dx, y + dy
                    seen.add((i, j, dx, dy))
                    seen.add((x, y, -dx, -dy))
                    self.segments.append(Segment(self.node_at(i, j), self.node_at(x, y), (i, j), (x, y)))
        self.adj = {}
        for k, s in enumerate(self.segments):
            if s.a == s.b:
                continue       # both ends in the same room: stays a wall
            self.adj.setdefault(s.a, []).append((k, s.b))
            self.adj.setdefault(s.b, []).append((k, s.a))

    # -- the tree of corridors
    def carve(self, waypoints, rng: random.Random, prune=0.0, thread=True, density=1.0, reserved=()):
        """waypoints: room nodes in the order the thread should visit them.
        density: share of the borders between pictures that become corridors.
        1.0 is a full maze where a corridor reaches every corner. Lower values leave
        more pictures touching, so the walls get heavier."""
        usable = sum(1 for s in self.segments if s.a != s.b)
        budget = int(round(usable * density))
        # reserved: borders that must be corridors and that the thread must leave alone
        kept = {k for run in reserved for k in run}
        visited = set()
        tree = set()
        main = []                       # segment indices of the thread, in order
        nodes_on_thread = []
        spurs = []

        def path(start, goal, banned):
            """A wandering path from start to goal that avoids `banned` nodes."""
            import heapq
            dist = {start: 0.0}
            prev = {}
            heap = [(0.0, 0, start)]
            n = 0
            while heap:
                d, _, u = heapq.heappop(heap)
                if u == goal:
                    break
                if d > dist.get(u, 1e18):
                    continue
                for k, v in self.adj.get(u, []):
                    if k in kept or (v in banned and v != goal):
                        continue
                    nd = d + self.segments[k].length * (0.35 + rng.random() * 1.6)
                    if nd < dist.get(v, 1e18):
                        dist[v] = nd
                        prev[v] = (u, k)
                        n += 1
                        heapq.heappush(heap, (nd, n, v))
            if goal not in prev and goal != start:
                return None
            out = []
            u = goal
            while u != start:
                pu, k = prev[u]
                out.append((k, u))
                u = pu
            return out[::-1]

        # rooms that no corridor can reach are left out of the thread
        waypoints = [w for w in waypoints if self.adj.get(w)]
        if not waypoints:
            waypoints = [next(iter(self.adj))] if self.adj else []
        if waypoints:
            cur = waypoints[0]
            visited.add(cur)
            nodes_on_thread.append(cur)
        for goal in waypoints[1:]:
            if goal in visited:
                continue
            pth = path(cur, goal, visited)
            if pth is None:
                # blocked: reach the goal from anywhere on the tree and note it as a side branch
                best = None
                for src in sorted(visited):          # sorted: the maze must not depend on the order Python keeps a set in
                    alt = path(src, goal, visited - {src})
                    if alt is not None and (best is None or len(alt) < len(best[1])):
                        best = (src, alt)
                if best is None:
                    continue
                for k, v in best[1]:
                    tree.add(k)
                    visited.add(v)
                spurs.append([k for k, _ in best[1]])
                continue
            for k, v in pth:
                tree.add(k)
                visited.add(v)
                main.append(k)
                nodes_on_thread.append(v)
            cur = goal
        # grow the rest of the maze: long branches first (a hunt-and-kill walk).
        # Parts that no corridor connects to the rest get a maze of their own.
        def grow(frontier):
            # short branches from many places, so the corridors spread over the whole page
            while frontier and len(tree) < budget:
                u = frontier.pop(rng.randrange(len(frontier)))
                steps = rng.randint(2, 6)
                while len(tree) < budget and steps > 0:
                    nxt = [(k, v) for k, v in self.adj.get(u, []) if v not in visited]
                    if not nxt:
                        break
                    k, v = rng.choice(nxt)
                    tree.add(k)
                    visited.add(v)
                    frontier.append(u)
                    frontier.append(v)
                    u = v
                    steps -= 1

        # the reserved corridors: open them, and join each one to the maze if it stands alone
        for run in reserved:
            nodes = set()
            for k in run:
                sg = self.segments[k]
                nodes.add(sg.a)
                nodes.add(sg.b)
            alone = not (nodes & visited)
            for k in run:
                tree.add(k)
            if alone:
                # the shortest way from this corridor to the maze, through corners no corridor uses yet
                prev = {n: None for n in nodes}
                queue = sorted(nodes)
                hit = None
                while queue and hit is None:
                    u = queue.pop(0)
                    for k, v in self.adj.get(u, []):
                        if k in kept or v in prev:
                            continue
                        prev[v] = (u, k)
                        if v in visited:
                            hit = v
                            break
                        queue.append(v)
                while hit is not None and prev[hit] is not None:
                    u, k = prev[hit]
                    tree.add(k)
                    visited.add(hit)
                    hit = u
            visited |= nodes
        grow(sorted(visited))
        for node in sorted(self.adj, key=str):
            if node not in visited and len(tree) < budget:
                visited.add(node)
                grow([node])
        self.visited = visited
        for k in tree:
            self.segments[k].open = True
        # optional: close some dead ends so the walls get heavier
        if prune > 0:
            keep = set(main) | {k for sp in spurs for k in sp}
            changed = True
            while changed:
                changed = False
                deg = {}
                for k, s in enumerate(self.segments):
                    if s.open:
                        deg[s.a] = deg.get(s.a, 0) + 1
                        deg[s.b] = deg.get(s.b, 0) + 1
                for k, s in enumerate(self.segments):
                    if not s.open or k in keep:
                        continue
                    for end in (s.a, s.b):
                        if end[0] == "P" and deg.get(end, 0) == 1 and not self._on_edge(end) and rng.random() < prune:
                            s.open = False
                            changed = True
                            break
        self.main = main if thread else []
        self.thread_nodes = nodes_on_thread if thread else []
        self.spurs = spurs if thread else []
        self.reached = visited
        return self

    def _on_edge(self, node):
        return node[0] == "P" and (node[1] in (0, self.C) or node[2] in (0, self.R))

    # -- geometry for drawing
    def open_degree(self):
        deg = {}
        for s in self.segments:
            if s.open:
                for end, pt in ((s.a, s.p), (s.b, s.q)):
                    deg.setdefault(pt, []).append(s)
        return deg

    def bands(self, width):
        """Black rectangles (x0, y0, x1, y1) for the open corridors."""
        half = width / 2.0
        at = self.open_degree()
        out = []
        for s in self.segments:
            if not s.open:
                continue
            ext = []
            for node, pt in ((s.a, s.p), (s.b, s.q)):
                e = 0.0
                if node[0] == "P":
                    for o in at.get(pt, []):
                        if o is not s and o.horizontal != s.horizontal:
                            e = half
                ext.append(e)
            (x0, y0), (x1, y1) = s.p, s.q
            if s.horizontal:
                a, b = (x0, ext[0]), (x1, ext[1])
                if a[0] > b[0]:
                    a, b = b, a
                out.append((a[0] - a[1], y0 - half, b[0] + b[1], y0 + half))
            else:
                a, b = (y0, ext[0]), (y1, ext[1])
                if a[0] > b[0]:
                    a, b = b, a
                out.append((x0 - half, a[0] - a[1], x0 + half, b[0] + b[1]))
        return out

    # -- the paths a visitor can walk
    def _router(self, rid, keep_out):
        """Cost of standing on a quarter-lattice point inside one region of open floor."""
        Q = 4
        cells = set(self.regions[rid])
        zones = [(r.x + keep_out, r.y + keep_out, r.x1 - keep_out, r.y1 - keep_out)
                 for r in self.rects if r.kind == "room" and self.room_region.get(r.id) == rid]

        def inside(a, b):
            xs = [a // Q] if a % Q else [a // Q - 1, a // Q]
            ys = [b // Q] if b % Q else [b // Q - 1, b // Q]
            return any((x, y) in cells for x in xs for y in ys)

        def cost(a, b):
            c = 0.25
            for da in (-1, 1):
                for db in (-1, 1):
                    if (int((a + da * 0.5) // Q), int((b + db * 0.5) // Q)) not in cells:
                        c += 1.5        # hugging a wall or the edge of the page
                        break
                else:
                    continue
                break
            x, y = a / Q, b / Q
            if any(x0 < x < x1 and y0 < y < y1 for (x0, y0, x1, y1) in zones):
                c += 15.0               # walking over the words
            return c

        return inside, cost

    def _route(self, rid, start, goals, keep_out):
        """The tidiest path from `start` to the nearest point in `goals`, inside one region."""
        import heapq
        inside, cost = self._router(rid, keep_out)
        dist = {(start, None): 0.0}
        prev = {}
        heap = [(0.0, 0, start, None)]
        n = 0
        end = None
        while heap:
            d, _, u, du = heapq.heappop(heap)
            if u in goals:
                end = (u, du)
                break
            if d > dist.get((u, du), 1e18):
                continue
            for dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = (u[0] + dv[0], u[1] + dv[1])
                if not inside(*v):
                    continue
                nd = d + cost(*v) + (0.35 if du is not None and dv != du else 0.0)
                if nd < dist.get((v, dv), 1e18):
                    dist[(v, dv)] = nd
                    prev[(v, dv)] = (u, du)
                    n += 1
                    heapq.heappush(heap, (nd, n, v, dv))
        if end is None:
            return None
        out = [end[0]]
        cur = end
        while cur in prev:
            cur = prev[cur]
            out.append(cur[0])
        return out[::-1]

    def walk_graph(self, spots, keep_out=0.375, spacing=4):
        """Everything a visitor can walk on, as a graph of short straight steps.
        A corridor is walked down its middle. Inside a room the paths run along the walls,
        around the words, and join every door to the place where a visitor stands.
        spots: {room id: (x, y)} in grid units, multiples of a quarter.
        Returns dict(nodes=[x, y, ...] in quarter units, edges=[a, b, ...], spots={room id: node})."""
        from collections import defaultdict
        Q = 4
        steps = defaultdict(set)

        def link(path):
            for u, v in zip(path, path[1:]):
                if u != v:
                    steps[u].add(v)
                    steps[v].add(u)

        doors = defaultdict(set)
        for sg in self.segments:
            if not sg.open:
                continue
            (x0, y0), (x1, y1) = sg.p, sg.q
            n = (abs(x1 - x0) + abs(y1 - y0)) * Q
            dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
            link([(x0 * Q + dx * k, y0 * Q + dy * k) for k in range(n + 1)])
            for node, pt in ((sg.a, sg.p), (sg.b, sg.q)):
                if node[0] == "R":
                    doors[node[1]].add((pt[0] * Q, pt[1] * Q))
        spot_pts = {}
        by_region = defaultdict(list)
        for rid_room, (x, y) in spots.items():
            pt = (int(round(x * Q)), int(round(y * Q)))
            spot_pts[rid_room] = pt
            by_region[self.room_region[rid_room]].append(pt)
        for rid in range(len(self.regions)):
            terminals = sorted(doors.get(rid, ())) + sorted(by_region.get(rid, ()))
            if not terminals:
                continue
            tree = {terminals[0]}
            for t in terminals[1:]:
                if t in tree:
                    continue
                path = self._route(rid, t, tree, keep_out)
                if path is None:
                    continue
                link(path)
                tree.update(path)
        # keep the points where something happens, and one point per grid unit in between
        special = set(spot_pts.values())

        def keeps(p):
            nb = steps[p]
            if len(nb) != 2 or p in special:
                return True
            a, b = tuple(nb)
            return (a[0] - p[0], a[1] - p[1]) != (p[0] - b[0], p[1] - b[1])

        kept = {p for p in steps if keeps(p)}
        index = {}
        nodes, edges = [], []

        def node(p):
            if p not in index:
                index[p] = len(index)
                nodes.extend(p)
            return index[p]

        done = set()
        for u in sorted(kept):
            for v in sorted(steps[u]):
                if (u, v) in done:
                    continue
                run = [u, v]
                while run[-1] not in kept:
                    nxt = [w for w in steps[run[-1]] if w != run[-2]]
                    if not nxt:
                        break
                    run.append(nxt[0])
                done.add((u, v))
                done.add((run[-1], run[-2]))
                last = node(u)
                for k in range(spacing, len(run) - 1, spacing):
                    cur = node(run[k])
                    edges.extend((last, cur))
                    last = cur
                edges.extend((last, node(run[-1])))
        return dict(nodes=nodes, edges=edges, spots={k: index[p] for k, p in spot_pts.items() if p in index})

    # -- the thread
    def thread(self, inset=0.25, keep_out=0.375):
        """The thread as a list of points. In a corridor it runs down the middle.
        In a room it walks along the walls, around the words, from door to door."""
        if not self.main:
            return []
        pts = []
        node = self.thread_nodes[0]
        runs = []
        for idx, k in enumerate(self.main):
            s = self.segments[k]
            nxt = self.thread_nodes[idx + 1]
            if s.a == node and s.b == nxt:
                p, q = s.p, s.q
            else:
                p, q = s.q, s.p
            runs.append((node, p, q))
            node = nxt
        for idx, (node, p, q) in enumerate(runs):
            if idx > 0 and node[0] == "R":
                door_in = runs[idx - 1][2]
                if door_in != p:
                    pts.extend(self._cross_room(node[1], door_in, p, keep_out))
            pts.append((float(p[0]), float(p[1])))
            pts.append((float(q[0]), float(q[1])))
        return _tidy(pts)

    def _cross_room(self, rid, door_in, door_out, keep_out):
        """Shortest tidy path through a region of open floor on a quarter-unit lattice.
        Hugging a wall costs more than walking a step away from it, and walking over
        the words of a room costs a lot."""
        import heapq
        Q = 4
        cells = set(self.regions[rid])
        zones = [(r.x + keep_out, r.y + keep_out, r.x1 - keep_out, r.y1 - keep_out)
                 for r in self.rects if r.kind == "room" and self.room_region.get(r.id) == rid]

        def touches(a, b):
            """Cells that the lattice point (a, b) touches."""
            xs = [a // Q] if a % Q else [a // Q - 1, a // Q]
            ys = [b // Q] if b % Q else [b // Q - 1, b // Q]
            return [(x, y) for x in xs for y in ys]

        def inside(a, b):
            return any(c in cells for c in touches(a, b))

        def clear(a, b):
            """A quarter unit away from every wall and from the edge of the page."""
            for da in (-1, 1):
                for db in (-1, 1):
                    x, y = (a + da * 0.5) // Q, (b + db * 0.5) // Q
                    if (int(x), int(y)) not in cells:
                        return False
            return True

        def in_words(a, b):
            x, y = a / Q, b / Q
            return any(x0 < x < x1 and y0 < y < y1 for (x0, y0, x1, y1) in zones)

        def cost(a, b):
            c = 0.25
            if not clear(a, b):
                c += 1.5
            if in_words(a, b):
                c += 15.0
            return c

        start = (int(door_in[0] * Q), int(door_in[1] * Q))
        goal = (int(door_out[0] * Q), int(door_out[1] * Q))
        dist = {(start, None): 0.0}
        prev = {}
        heap = [(0.0, 0, start, None)]
        n = 0
        end = None
        while heap:
            d, _, u, du = heapq.heappop(heap)
            if u == goal:
                end = (u, du)
                break
            if d > dist.get((u, du), 1e18):
                continue
            for dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = (u[0] + dv[0], u[1] + dv[1])
                if not inside(*v):
                    continue
                nd = d + cost(*v) + (0.35 if du is not None and dv != du else 0.0)
                if nd < dist.get((v, dv), 1e18):
                    dist[(v, dv)] = nd
                    prev[(v, dv)] = (u, du)
                    n += 1
                    heapq.heappush(heap, (nd, n, v, dv))
        if end is None:
            return []
        out = []
        cur = end
        while cur in prev:
            out.append((cur[0][0] / Q, cur[0][1] / Q))
            cur = prev[cur]
        out.append((start[0] / Q, start[1] / Q))
        return out[::-1]


def _tidy(pts):
    """Remove repeated points and points in the middle of straight runs."""
    clean = []
    for p in pts:
        if clean and abs(clean[-1][0] - p[0]) < 1e-9 and abs(clean[-1][1] - p[1]) < 1e-9:
            continue
        clean.append((float(p[0]), float(p[1])))
    out = []
    for k, b in enumerate(clean):
        if 0 < k < len(clean) - 1:
            a, c = clean[k - 1], clean[k + 1]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
            if abs(cross) < 1e-9 and dot > 0:
                continue
        out.append(b)
    return out
