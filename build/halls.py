"""Short press lines written along the corridors of the maze.

Before the maze is cut, each line looks for a border that runs beside pictures of its own work.
That border is then kept as a corridor, and the thread stays out of it.
"""
import math

import content
import typo

SIZE, TRACK = 12.5, 0.13          # px and em, as in the CSS for .hall


def find(mz, unit, corridor, texts):
    """texts: list of dict(key, work, short, long).
    Returns ({key: dict(x, y, upright, form)}, [segments to keep open for each line])."""
    photos = {p["slug"]: p for p in content.PHOTOS}
    nine = {w["slug"] for w in content.WORKS}

    def works_at(kind, at, pos):
        if kind == "h":
            cells = [mz.cell(int(pos), at - 1), mz.cell(int(pos), at)]
        else:
            cells = [mz.cell(at - 1, int(pos)), mz.cell(at, int(pos))]
        return [photos[mz.rects[i].id]["work"] for i in cells if i is not None and i >= 0]

    # every straight line of borders, as a sorted list of (start, end, segment index)
    lines = {}
    for k, s in enumerate(mz.segments):
        (x0, y0), (x1, y1) = s.p, s.q
        if s.horizontal:
            lines.setdefault(("h", y0), []).append((min(x0, x1), max(x0, x1), k))
        else:
            lines.setdefault(("v", x0), []).append((min(y0, y1), max(y0, y1), k))
    runs = []
    for (kind, at), items in lines.items():
        items.sort()
        cur = [items[0]]
        for it in items[1:]:
            if it[0] == cur[-1][1]:
                cur.append(it)
            else:
                runs.append((kind, at, cur))
                cur = [it]
        runs.append((kind, at, cur))

    taken = set()
    found, reserved = {}, []
    for t in texts:
        best = None
        for form in ("long",):      # the line always names its work, so nobody can misread it
            need = typo.width(t[form], "text", SIZE, TRACK) / unit + 0.6
            for kind, at, items in runs:
                lo, hi = items[0][0] + 0.25, items[-1][1] - 0.25
                start = lo
                while start + need <= hi + 1e-9:
                    segs = [k for (a, b, k) in items if a < start + need and b > start]
                    if not any(k in taken for k in segs):
                        beside = other = n = 0
                        pos = math.floor(start) + 0.5
                        while pos < start + need:
                            here = works_at(kind, at, pos)
                            n += 1
                            if t["work"] in here:
                                beside += 1
                            if any(w in nine and w != t["work"] for w in here):
                                other += 1
                            pos += 1
                        ok = (other == 0 and beside / n >= 0.6) if form == "short" else (other / n <= 0.34 and beside / n >= 0.4)
                        if ok:
                            score = (0 if form == "short" else 1, other, 0 if kind == "h" else 1, -(beside / n), len(segs), start)
                            if best is None or score < best[0]:
                                best = (score, kind, at, start, segs, form)
                    start += 0.5
            if best is not None:
                break
        if best is None:
            continue
        _, kind, at, start, segs, form = best
        taken.update(segs)
        reserved.append(segs)
        found[t["key"]] = dict(x=start if kind == "h" else at, y=at if kind == "h" else start, upright=kind == "v", form=form)
    return found, reserved
