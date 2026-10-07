"""Packs the site for whoever puts it on the server.

    python3 build/make_zip.py

Writes unitednotions-film-for-dan.zip beside the folder of the site. Inside the zip:

    unitednotions-film/FOR-DAN.txt                   how to put it on DreamHost, step by step
    unitednotions-film/site/                         the site: what goes on the server
    unitednotions-film/build/                        this workshop, so the pages can be changed and rebuilt
    unitednotions-film/htaccess.txt                  a spare copy of site/.htaccess
    unitednotions-film/robots-no-ai-training.txt     the other robots.txt

Left out: README.txt (notes for home), the originals in build/video-in, the copies of the old site in build/src-old.
Run the build first, so the zip holds the pages as they are now.
"""
import json
import os
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
HOLDER = os.path.abspath(os.path.join(HERE, ".."))          # the folder that holds build
if not os.path.isdir(SITE):
    SITE = HOLDER                                             # the build folder sits inside the site folder
SITE = os.path.abspath(SITE)
TOP = "unitednotions-film"
OUT = os.path.join(os.path.dirname(HOLDER), "unitednotions-film-for-dan.zip")
ALREADY_SMALL = (".webp", ".jpg", ".jpeg", ".png", ".ico", ".mp4", ".woff2", ".zip")
NEVER = ("__pycache__", ".DS_Store", "Thumbs.db")
NOT_PUBLIC = ("README.txt", "FOR-DAN.txt", "htaccess.txt", "robots-no-ai-training.txt")
NOT_IN_BUILD = ("video-in", "src-old")

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

VIDEOS_MISSING = """BEFORE THE DOMAIN MOVES: THE LAB VIDEOS

  %d videos of the lab notes are not in this zip. The old site only streams them, from its own video host,
  and it still hands each one out as an MP4. They can be fetched only while unitednotions.film is the old site.
  Once the domain points to DreamHost, that door is closed.

  From inside this folder:
    python3 build/fetch_lab_videos.py        takes them from the old site into build/video-in. About 1 GB.
    python3 build/make_research_media.py     makes a web copy and a still of each one. Needs ffmpeg (brew install ffmpeg).
    python3 build/build.py                   puts them in their notes. Needs: pip3 install pillow numpy fonttools brotli
  Then upload site/.

  Violeta can also run the first line on her Mac and have the rest done there. Ask her which of you does it,
  so it is done once. Until then %d lab notes show without their videos."""

VIDEOS_IN = """THE LAB VIDEOS

  Every video of the lab notes is in this zip. Nothing is left to fetch from the old site."""


def packed_line():
    now = time.localtime()
    return "Packed on %d %s %d." % (now.tm_mday, MONTHS[now.tm_mon], now.tm_year)


def videos_section():
    path = os.path.join(HERE, "data", "research-missing.json")
    missing = json.load(open(path, encoding="utf-8")).get("videos", []) if os.path.exists(path) else []
    if not missing:
        return VIDEOS_IN
    return VIDEOS_MISSING % (len(missing), len({slug for slug, _ in missing}))


def add(z, name, data, mtime=None, folder=False):
    """Everything goes in with plain permissions: files 644, folders 755. A file that only its owner can read
    would be refused by the web server."""
    info = zipfile.ZipInfo(name + ("/" if folder else ""), time.localtime(mtime or time.time())[:6])
    info.create_system = 3
    info.external_attr = ((0o40755 if folder else 0o100644) << 16) | (0x10 if folder else 0)
    info.compress_type = zipfile.ZIP_STORED if folder or name.lower().endswith(ALREADY_SMALL) else zipfile.ZIP_DEFLATED
    z.writestr(info, data)


def walk(root, skip_top=()):
    """Every file under root, as (path on disk, path inside root), folders first, in a steady order."""
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in NEVER and not (folder == root and d in skip_top))
        for f in sorted(files):
            if f in NEVER or f.endswith((".part", ".pyc")):
                continue
            full = os.path.join(folder, f)
            yield full, os.path.relpath(full, root).replace(os.sep, "/")


def main():
    for needed in ("index.html", ".htaccess", "robots.txt", "llms.txt", "sitemap.xml", "404.html", os.path.join("es", "index.html"), os.path.join("es", "llms.txt")):
        if not os.path.exists(os.path.join(SITE, needed)):
            sys.exit("%s is not in the site folder. Run   python3 build/build.py   first." % needed)
    letter = open(os.path.join(HERE, "for-dan", "FOR-DAN.txt"), encoding="utf-8").read()
    letter = letter.replace("{{PACKED}}", packed_line()).replace("{{VIDEOS}}", videos_section())
    counts = {"site": 0, "build": 0}
    part = OUT + ".part"
    with zipfile.ZipFile(part, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        add(z, TOP, b"", folder=True)
        add(z, TOP + "/FOR-DAN.txt", letter.encode("utf-8"))
        add(z, TOP + "/htaccess.txt", open(os.path.join(SITE, ".htaccess"), "rb").read())
        add(z, TOP + "/robots-no-ai-training.txt", open(os.path.join(HERE, "for-dan", "robots-no-ai-training.txt"), "rb").read())
        # the site: everything in its folder but the workshop and the notes for home
        build_inside = os.path.abspath(HERE).startswith(SITE + os.sep)
        for full, rel in walk(SITE, skip_top=("build",) if build_inside else ()):
            if "/" not in rel and rel in NOT_PUBLIC:
                continue
            add(z, "%s/site/%s" % (TOP, rel), open(full, "rb").read(), os.path.getmtime(full))
            counts["site"] += 1
        # the workshop
        for full, rel in walk(HERE, skip_top=NOT_IN_BUILD):
            data = open(full, "rb").read()
            if rel == "captions.html" and build_inside:
                # in the zip the site sits beside the workshop, so the sheet of captions finds its pictures one folder further
                data = data.replace(b'"../assets/img/maze/', b'"../site/assets/img/maze/')
            add(z, "%s/build/%s" % (TOP, rel), data, os.path.getmtime(full))
            counts["build"] += 1
    if os.path.exists(OUT):
        try:
            os.remove(OUT)
        except OSError:
            pass                              # a place where nothing may be deleted: the new zip takes another name below
    try:
        os.replace(part, OUT)
        out = OUT
    except OSError:
        out = OUT[:-4] + time.strftime("-%Y%m%d-%H%M") + ".zip"
        os.rename(part, out)
    print("%s" % out)
    print("%.0f MB: %d files of the site, %d files of the workshop" % (os.path.getsize(out) / 1e6, counts["site"], counts["build"]))
    print(videos_section().splitlines()[0])


if __name__ == "__main__":
    main()
