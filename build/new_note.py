"""Starts a new lab note: the two text files, and its line in the list of notes.

    python3 build/new_note.py "The title of the note"
    python3 build/new_note.py "The title of the note" --place Cochabamba --date 2026-10-07 --key short-name

Then write the note in build/research/en/<name>.txt, translate it into build/research/es/<name>.txt,
put its pictures in build/picture-in and its videos in build/video-in, and run   sh publish.sh

The name of the note's address (/research/<name>) is made from the title. The key is a short name used for the
files of its pictures and videos (<key>-01.jpg, <key>-02.mp4). Both can be chosen with --slug and --key.
Nothing is overwritten: if the note exists, the script stops.
"""
import datetime
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(HERE, "data", "research.json")
STOP = {"the", "a", "an", "of", "and", "to", "in", "on", "for", "at", "by", "with", "from", "that", "this", "its", "is", "are", "how", "when", "what", "el", "la", "los", "las", "de", "del", "y", "en", "un", "una"}


def ascii_slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", text)


def short_key(slug, taken):
    words = [w for w in slug.split("-") if w not in STOP] or slug.split("-")
    key = "-".join(words[:2])
    n = 2
    while key in taken:
        n += 1
        key = "-".join(words[:n]) if n <= len(words) else "%s-%d" % ("-".join(words[:2]), n)
    return key


def option(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            value = sys.argv[i + 1]
            del sys.argv[i:i + 2]
            return value
    return default


def main():
    date = option("--date", datetime.date.today().isoformat())
    place = option("--place", "")
    want_slug = option("--slug")
    want_key = option("--key")
    words = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not words:
        print(__doc__)
        sys.exit(2)
    title = " ".join(words).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        sys.exit("The date must be written 2026-10-07.")

    notes = json.load(open(NOTES, encoding="utf-8"))
    slugs = {n["slug"] for n in notes}
    keys = {n["key"] for n in notes}
    slug = ascii_slug(want_slug or title)
    key = ascii_slug(want_key) if want_key else short_key(slug, keys)
    if not slug or not key:
        sys.exit("The title gives no usable name. Give one with --slug.")
    if slug in slugs:
        sys.exit("A note already has the address /research/%s. Choose another title, or give --slug." % slug)
    if key in keys:
        sys.exit("The key %s is taken by another note. Give another with --key." % key)
    en = os.path.join(HERE, "research", "en", slug + ".txt")
    es = os.path.join(HERE, "research", "es", slug + ".txt")
    if os.path.exists(en) or os.path.exists(es):
        sys.exit("A text file for %s already exists. Nothing was changed." % slug)

    body = "T: %s\nD: %s\nS: %s\nP: \n" % (title, title, title)
    os.makedirs(os.path.dirname(en), exist_ok=True)
    os.makedirs(os.path.dirname(es), exist_ok=True)
    open(en, "w", encoding="utf-8").write(body)
    open(es, "w", encoding="utf-8").write(body)
    notes.append(dict(slug=slug, key=key, title=title, page_title=title, iso=date, place=place,
                      images=[], sizes={}, videos=[], posters={}, missing=[], embeds=[], changed=date, blocks=0))
    text = json.dumps(notes, ensure_ascii=False, indent=1)
    open(NOTES, "w", encoding="utf-8").write(text)

    print("The note is started. Its address will be /research/%s and its key is %s." % (slug, key))
    print()
    print("1. Write it:        build/research/en/%s.txt" % slug)
    print("     T: the title.  D: one sentence for search engines.  S: a one-sentence summary.")
    print("     P: a paragraph.  H: a heading.  LI: a list item.  CAP: the caption of the picture or video above it.")
    print("     A: link text | https://address      Links inside a line are written [text](https://address).")
    print("     The first three lines must stay T, D, S, in that order.")
    print("2. Pictures:        build/picture-in/%s-01.jpg, %s-02.jpg ...   then a line   IMG: 1   where it goes." % (key, key))
    print("     Two IMG lines one after the other stand side by side. A line  IMG: 1 | https://address  makes it a link.")
    print("3. Videos:          build/video-in/%s-01.mp4 (or .mov) ...      then a line   VIDEO: 01 | 16:9   (the shape: 16:9, 9:16, 1:1)." % key)
    print("     A video of a few seconds plays by itself and loops. A longer one waits for the visitor. Needs ffmpeg.")
    print("     Or:  YT: id | title   for YouTube,   VM: id | title   for Vimeo.")
    print("4. Spanish:         build/research/es/%s.txt" % slug)
    print("     Same lines, same tags, same order, translated. build/research/BRIEF-es.md has the rules.")
    print("     (For now it holds the English, so the Spanish site shows English until it is translated.)")
    print("5. Describe the pictures for people who cannot see them: build/research/alts.json, under \"%s\"." % slug)
    print("6. Publish:         sh publish.sh")
    print()
    print("Date %s%s. Change them in build/data/research.json under \"slug\": \"%s\"." % (date, (", place " + place) if place else ", no place given (--place)", slug))


if __name__ == "__main__":
    main()
