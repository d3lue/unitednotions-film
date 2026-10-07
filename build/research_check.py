"""Checks a translated lab note against its English original.

    python3 build/research_check.py <note>          one note
    python3 build/research_check.py                 every note

A note passes when it has the same lines with the same tags, the same pictures, videos and link addresses,
and none of the things the house style forbids.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, "research", "en")
ES = os.path.join(HERE, "research", "es")
FIXED = ("IMG", "GAL", "VID", "YT", "VM", "EMBED", "MISSING-VIDEO")
TEXT = ("T", "D", "S", "H", "P", "+", "LI", "CAP", "A")
VOSEO = re.compile(r"\b(vos|tenés|podés|querés|sabés|mirá|hacé|decí|vení|andá|fijate|sos|estás viendo vos|pensá|imaginá|probá|usá|seguí|sumate|unite|escuchá|contanos|escribinos|vosotros|vuestr[oa]s?)\b", re.I)
SPAIN = re.compile(r"\b(ordenador(es)?|móvil(es)?|vídeos?|vale la pena|cabe destacar|es importante señalar|sin duda|no obstante)\b", re.I)


def split(line):
    tag, _, text = line.partition(":")
    return tag, text.strip()


def links(text):
    return re.findall(r"\]\(([^)]+)\)", text)


def check(slug):
    problems = []
    pe, ps = os.path.join(EN, slug + ".txt"), os.path.join(ES, slug + ".txt")
    if not os.path.exists(ps):
        return ["the Spanish file does not exist: " + ps]
    en = [l.rstrip("\n") for l in open(pe, encoding="utf-8") if l.strip()]
    es = [l.rstrip("\n") for l in open(ps, encoding="utf-8") if l.strip()]
    if len(en) != len(es):
        problems.append("the English file has %d lines and the Spanish file has %d" % (len(en), len(es)))
    for i, (a, b) in enumerate(zip(en, es), 1):
        ta, xa = split(a)
        tb, xb = split(b)
        where = "line %d (%s)" % (i, ta)
        if ta != tb:
            problems.append("%s: the tag is '%s' in Spanish. Lines are out of step from here." % (where, tb))
            break
        if ta in FIXED:
            if a != b:
                problems.append("%s: this line must be copied unchanged" % where)
            continue
        if ta not in TEXT:
            problems.append("%s: unknown tag" % where)
            continue
        if ta == "A":
            if xa.rsplit(" | ", 1)[-1] != xb.rsplit(" | ", 1)[-1]:
                problems.append("%s: the address after ' | ' changed" % where)
        if links(xa) != links(xb):
            problems.append("%s: the link addresses changed: %s -> %s" % (where, links(xa), links(xb)))
        if not xb:
            problems.append("%s: empty" % where)
        if "—" in xb or "–" in xb:
            problems.append("%s: long dash" % where)
        body = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", xb)
        for sentence in re.split(r"(?<=[.!?:…])\s+|^", body):
            if re.match(r"^[¿¡\"“'(]*Y[ ,]", sentence):
                problems.append("%s: a sentence begins with 'Y': %s" % (where, sentence[:60]))
        if re.search(r"\bsino\b", body, re.I) and xa != xb:
            problems.append("%s: 'sino'. Write the statement directly." % where)
        m = VOSEO.search(body)
        if m and xa != xb:
            problems.append("%s: voseo or 'vosotros': %s" % (where, m.group(0)))
        m = SPAIN.search(body)
        if m and xa != xb:
            problems.append("%s: word or filler to avoid: %s" % (where, m.group(0)))
        if re.search(r"por ciento", body, re.I):
            problems.append("%s: write the percentage with %%" % where)
        if xa == xb and ta in ("P", "+", "H", "LI", "T", "S", "D") and len(xa.split()) > 6 and not re.match(r'^[“"‘\']', xa) \
                and not re.search(r"\b(el|la|los|las|que|de|en|un|una|con|por)\b", xa) and "→" not in xa:
            problems.append("%s: still in English?" % where)
    return problems


if __name__ == "__main__":
    slugs = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(EN) if f.endswith(".txt"))
    bad = 0
    for slug in slugs:
        problems = check(slug)
        if problems:
            bad += 1
            print("%s: %d problem(s)" % (slug, len(problems)))
            for p in problems[:40]:
                print("   " + p)
        else:
            print("%s: OK" % slug)
    sys.exit(1 if bad else 0)
