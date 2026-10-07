"""Makes the web copies of what the lab notes show: pictures, videos, and a still of each video.

    python3 build/make_research_media.py

It can be run as often as needed: what is already made is left alone. Run the build after it.

PICTURES   The originals are in the backup of the old site, beside this site:
               unitednotions-film-backup/site/pages/research/<note>/images
           The web copies go to assets/img/research/<name>-<width>.webp

VIDEOS     The short videos of the backup are copied to assets/video/research.
           A video that the old site only streamed has a place waiting in its note.
           build/fetch_lab_videos.py takes those from the old site and puts them in build/video-in.
           An original from somewhere else can go there too, with the name this script lists, for example
               build/video-in/whale-watches-340432.mov
           Any usual format works. The script makes a web copy in assets/video/research
           (MP4, at most 1920 wide) and a still for the moment before it plays.
           A file that is already a web copy can go straight into assets/video/research with that name.

RECORDS    build/data/research-renditions.json and build/data/research-videos.json. The build reads them.

It needs Pillow. The videos need ffmpeg:   brew install ffmpeg
    --secs 150     stop after this many seconds and go on next time (for a shell with a time limit)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
if not os.path.isdir(SITE):
    SITE = os.path.join(HERE, "..")              # the build folder sits inside the site folder
BACKUP = None
for up in ("..", os.path.join("..", "..")):
    candidate = os.path.join(HERE, up, "unitednotions-film-backup", "site")
    if os.path.isdir(candidate):
        BACKUP = candidate
        break
IMG = os.path.join(SITE, "assets", "img", "research")
VID = os.path.join(SITE, "assets", "video", "research")
INBOX = os.path.join(HERE, "video-in")
PIC_INBOX = os.path.join(HERE, "picture-in")      # pictures of new notes: <key>-01.jpg, <key>-02.png ...
PICTURE_TYPES = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic", ".gif")
DATA = os.path.join(HERE, "data")
LIMIT = float(sys.argv[sys.argv.index("--secs") + 1]) if "--secs" in sys.argv else None
T0 = time.time()
VIDEO_TYPES = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".ts", ".mts")


def out_of_time():
    return LIMIT is not None and time.time() - T0 > LIMIT


def read(name, empty):
    path = os.path.join(DATA, name)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else empty


def write(name, value):
    text = json.dumps(value, ensure_ascii=False, indent=1)       # made first, so a fault cannot leave half a file
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        f.write(text)


def has(tool):
    return shutil.which(tool) is not None


def still_name(key, file):
    """The name of the still of a video. research.py uses the same rule."""
    stem = file.rsplit(".", 1)[0]
    return "%s-poster-%s" % (key, stem[len(key) + 1:] if stem.startswith(key + "-") else stem[:8])


def made(name, rec):
    """Is this record good, and are its files there?"""
    if not rec or "error" in rec or not rec.get("widths"):
        return False
    return all(os.path.exists(os.path.join(IMG, "%s-%d.webp" % (name, w))) for w in rec["widths"])


def web_copies(im, name, want, quality):
    """Saves a picture in a few widths. Returns the record the build needs."""
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        black = Image.new("RGBA", im.size, (0, 0, 0, 255))
        black.alpha_composite(im)
        im = black
    im = im.convert("RGB")
    W, H = im.size
    widths = sorted(set([w for w in want if w < W] + [min(W, want[-1])]))
    rec = dict(ow=W, oh=H, widths=widths, bytes={})
    for w in widths:
        small = im.resize((w, round(H * w / W)), Image.LANCZOS) if w != W else im
        file = os.path.join(IMG, "%s-%d.webp" % (name, w))
        small.save(file, "WEBP", quality=quality, method=4)
        rec["bytes"][str(w)] = os.path.getsize(file)
    rec["w"], rec["h"] = widths[-1], round(H * widths[-1] / W)
    rec["mean"] = list(im.resize((1, 1), Image.BOX).getpixel((0, 0)))      # the colour shown while the picture loads
    return rec


# ---------------------------------------------------------------------------------------------- pictures
def original(note, asset, cache):
    folder = os.path.join(BACKUP, "pages", "research", note, "images")
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            if os.path.splitext(f)[0].lower() == asset:
                return os.path.join(folder, f)
    return os.path.join(BACKUP, "_cache", cache[asset]) if asset in cache else None


def pictures(db):
    manifest = [m for m in read("research-manifest.json", []) if "poster" not in m]
    todo = [m for m in manifest if not made(m["name"], db.get(m["name"]))]
    if not todo:
        return len(manifest), 0, []
    if not BACKUP:
        return len(manifest) - len(todo), 0, [m["name"] for m in todo]
    folder = os.path.join(BACKUP, "_cache")
    cache = {os.path.splitext(f)[0].lower(): f for f in os.listdir(folder)} if os.path.isdir(folder) else {}
    new, lost = 0, []
    for m in todo:
        if out_of_time():
            break
        src = original(m["note"], m["asset"], cache)
        if not src:
            lost.append(m["name"])
            continue
        try:
            im = Image.open(src)
            if im.format == "JPEG":
                im.draft("RGB", (3200, 3200))
            rec = web_copies(im, m["name"], (480, 960, 1600), 78)
            rec["file"] = os.path.relpath(src, os.path.join(BACKUP, "..", ".."))
            db[m["name"]] = rec
            new += 1
            write("research-renditions.json", db)
        except Exception as e:                       # a picture that cannot be read does not stop the others
            lost.append("%s (%s)" % (m["name"], str(e)[:80]))
    ready = sum(1 for m in manifest if made(m["name"], db.get(m["name"])))
    return ready, new, lost



def inbox_pictures(db):
    """The pictures of new notes, from build/picture-in. A file is named <key>-<number>.<type>, for example whale-watches-04.jpg,
    where key is the key of the note in research.json and the number is the one the note's IMG line names.
    A picture that is already made is left alone unless its file is newer."""
    if not os.path.isdir(PIC_INBOX):
        return 0, []
    keys = sorted((n["key"] for n in read("research.json", [])), key=len, reverse=True)
    new, bad = 0, []
    for f in sorted(os.listdir(PIC_INBOX)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in PICTURE_TYPES:
            continue
        name = stem.lower()
        m = re.match(r"^(.+)-(\d{2})$", name)
        if not m or m.group(1) not in keys:
            bad.append("%s: the name must be <key>-<two digits>, and the key must be one of a note in research.json" % f)
            continue
        src = os.path.join(PIC_INBOX, f)
        rec = db.get(name)
        if made(name, rec) and rec.get("mtime") == int(os.path.getmtime(src)):
            continue
        if out_of_time():
            break
        try:
            im = Image.open(src)
            if im.format == "JPEG":
                im.draft("RGB", (3200, 3200))
            rec = web_copies(im, name, (480, 960, 1600), 78)
            rec["file"] = "picture-in/" + f
            rec["mtime"] = int(os.path.getmtime(src))
            db[name] = rec
            new += 1
            write("research-renditions.json", db)
        except Exception as e:
            bad.append("%s (%s)" % (f, str(e)[:80]))
    return new, bad


# ---------------------------------------------------------------------------------------------- videos
def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path], capture_output=True, text=True)
    j = json.loads(p.stdout or "{}")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), None)
    w, h = v.get("width"), v.get("height")
    turn = 0
    for side in v.get("side_data_list", []) or []:
        if "rotation" in side:
            turn = int(side["rotation"])
    if (v.get("tags") or {}).get("rotate"):
        turn = int(v["tags"]["rotate"])
    if abs(turn) in (90, 270):
        w, h = h, w
    fmt = j.get("format", {})
    return dict(w=w, h=h, dur=round(float(fmt.get("duration", 0) or 0), 2), audio=bool(a), codec=v.get("codec_name"),
                acodec=a.get("codec_name") if a else None, rate=int(fmt.get("bit_rate", 0) or 0), bytes=os.path.getsize(path))


def web_video(src, dst):
    """A copy every browser plays: H.264 and AAC in an MP4 that starts before it has fully arrived."""
    info = probe(src)
    if not info["w"]:
        raise IOError("ffmpeg cannot read this file")
    work = tempfile.mkdtemp(prefix="unf-video-")
    part = os.path.join(work, "web.mp4")
    light = info["codec"] == "h264" and info["acodec"] in (None, "aac") and info["w"] <= 1920 and 0 < info["rate"] <= 6_500_000
    if light:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-movflags", "+faststart", part]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0?",
               "-vf", "scale='min(1920,iw)':-2", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", part]
    done = subprocess.run(cmd, capture_output=True, text=True)
    good = done.returncode == 0 and os.path.exists(part) and os.path.getsize(part) > 1000
    if good:
        shutil.copyfile(part, dst)
    shutil.rmtree(work, ignore_errors=True)
    if not good:
        raise IOError((done.stderr or "ffmpeg failed").strip()[-200:])


def still(path, name, dur, db):
    work = tempfile.mkdtemp(prefix="unf-still-")
    tmp = os.path.join(work, "still.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(min(0.5, dur / 2)), "-i", path, "-frames:v", "1", "-q:v", "2", tmp], capture_output=True)
    try:
        rec = web_copies(Image.open(tmp), name, (480, 960), 74)
        rec["file"] = "still of " + os.path.basename(path)
        db[name] = rec
    except Exception as e:
        db[name] = {"error": str(e)[:160]}
    shutil.rmtree(work, ignore_errors=True)


def videos(db, vdb):
    notes = read("research.json", [])
    tools = has("ffmpeg") and has("ffprobe")
    ready, new, waiting, queued, trouble = 0, 0, [], 0, []
    inbox = {}
    if os.path.isdir(INBOX):
        for f in sorted(os.listdir(INBOX)):
            stem, ext = os.path.splitext(f)
            if ext.lower() in VIDEO_TYPES:
                inbox[stem.lower()] = os.path.join(INBOX, f)
    for n in notes:
        idents = list(n.get("missing", []))
        text = os.path.join(HERE, "research", "en", n["slug"] + ".txt")       # a new note names its videos in its own text: VIDEO: 01 | 16:9
        if os.path.exists(text):
            for line in open(text, encoding="utf-8"):
                tag, _, rest = line.partition(":")
                ident = rest.split("|")[0].strip()
                if tag.strip() in ("VIDEO", "MISSING-VIDEO") and ident and ident not in idents:
                    idents.append(ident)
        wanted = [(f, None) for f in n.get("videos", [])] + [("%s-%s.mp4" % (n["key"], ident), ident) for ident in idents]
        for file, ident in wanted:
            dst = os.path.join(VID, file)
            late = out_of_time()            # when time is up nothing more is made, but what is ready is still counted
            try:
                if ident is None and not os.path.exists(dst) and BACKUP and not late:
                    src = os.path.join(BACKUP, "pages", "research", n["slug"], "videos", file)
                    if os.path.exists(src):
                        shutil.copyfile(src, dst)
                        new += 1
                if ident is not None:
                    src = inbox.get(file[:-4].lower())
                    if src and (not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)):
                        if late:
                            queued += 1
                            continue
                        if not tools:
                            if not src.lower().endswith(".mp4"):
                                raise IOError("ffmpeg is needed to turn this file into an MP4")
                            shutil.copyfile(src, dst)
                        else:
                            web_video(src, dst)
                        vdb.pop(file, None)
                        new += 1
                if not os.path.exists(dst):
                    if ident is not None:
                        waiting.append((n["title"], file[:-4]))
                    else:
                        trouble.append("%s: not in the backup" % file)
                    continue
                ready += 1
                name = still_name(n["key"], file)
                if tools and not late and (file not in vdb or vdb[file].get("bytes") != os.path.getsize(dst) or not made(name, db.get(name))):
                    info = probe(dst)
                    info["note"] = n["slug"]
                    vdb[file] = info
                    still(dst, name, info["dur"], db)
                    write("research-videos.json", vdb)
                    write("research-renditions.json", db)
            except Exception as e:
                trouble.append("%s: %s" % (file, str(e)[:160]))
    return ready, new, waiting, queued, trouble, tools


def main():
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(VID, exist_ok=True)
    os.makedirs(INBOX, exist_ok=True)
    db = read("research-renditions.json", {})
    vdb = read("research-videos.json", {})
    ready, new, lost = pictures(db)
    pnew, pbad = inbox_pictures(db)
    new += pnew
    print("Pictures: %d ready%s." % (ready + pnew, ", %d of them new" % new if new else ""))
    for line in pbad:
        print("  picture-in: " + line)
    if lost:
        where = "" if BACKUP else " The backup folder unitednotions-film-backup is not beside the site."
        print("  %d could not be made.%s" % (len(lost), where))
        for name in lost[:12]:
            print("    " + name)
    vready, vnew, waiting, queued, trouble, tools = videos(db, vdb)
    print("Videos: %d ready%s." % (vready, ", %d of them new" % vnew if vnew else ""))
    if queued:
        print("  %d more in build/video-in have no web copy yet." % queued)
    if not tools:
        print("  ffmpeg is not installed, so no video is converted or measured, and no still is made.")
    for line in trouble:
        print("  " + line)
    if waiting:
        print("  %s waiting. Take them from the old site with   python3 build/fetch_lab_videos.py" % ("1 video is" if len(waiting) == 1 else "%d videos are" % len(waiting)))
        print("  or put each original in build/video-in with this name (any usual video format):")
        last = None
        for title, name in waiting:
            if title != last:
                print("    %s" % title)
                last = title
            print("        %s" % name)
    if out_of_time():
        print("Time is up. Run it again to go on.")
    elif new or vnew:
        print("Now run the build:   python3 build/build.py")


if __name__ == "__main__":
    main()
