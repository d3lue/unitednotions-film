"""Brings home the lab videos that the old site only streams.

    python3 build/fetch_lab_videos.py

Run it on the Mac, in Terminal. It needs the internet, and it needs the old site to still be on unitednotions.film:
run it before the domain moves to the new host.

For every video a lab note is waiting for, it asks the old site for the file:
    https://www.unitednotions.film/_api/v1/videos/<number>/file
The old site answers with the address of an MP4 on its video host. This script takes the best copy kept there
(high.mp4, then medium.mp4, then low.mp4) and saves it as build/video-in/<name>.mp4.
A video that is already in build/video-in is not fetched again, so the script can be run again after a broken connection.

    --medium     take the medium copies: a third of the size, and less sharp
    --list       only show what would be fetched

If the old site moves to another address before this is run, give that address:
    UNF_OLD_SITE=https://the-other-address python3 build/fetch_lab_videos.py

Then:
    python3 build/make_research_media.py     makes the web copies and a still of each video (needs ffmpeg)
    python3 build/build.py                   puts them in their notes
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(HERE, "video-in")
OLD_SITE = os.environ.get("UNF_OLD_SITE", "https://www.unitednotions.film")
AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
CURL = shutil.which("curl")


def head(url):
    """Asks for the headers of a file, following the old site wherever it sends us.
    Returns (the address in the end, the size in bytes or 0). Raises IOError when the file is not there."""
    if CURL:
        done = subprocess.run([CURL, "-sS", "-L", "-I", "--connect-timeout", "30", "-A", AGENT, "-e", OLD_SITE + "/", "-w", "\n%{http_code} %{url_effective}", url],
                              capture_output=True, text=True)
        lines = done.stdout.strip().splitlines()
        code, _, address = (lines[-1] if lines else "").partition(" ")
        if done.returncode != 0 or code != "200":
            raise IOError("answer %s %s" % (code or "none", done.stderr.strip()[:120]))
        size = 0
        for line in lines[:-1]:
            name, _, value = line.partition(":")
            if name.strip().lower() == "content-length" and value.strip().isdigit():
                size = int(value.strip())          # the last one belongs to the file itself
        return address, size
    request = urllib.request.Request(url, headers={"User-Agent": AGENT}, method="HEAD")
    with urllib.request.urlopen(request, timeout=40) as answer:
        return answer.geturl(), int(answer.headers.get("Content-Length") or 0)


def download(url, target):
    part = target + ".part"
    if CURL:
        done = subprocess.run([CURL, "-L", "-f", "--connect-timeout", "30", "-A", AGENT, "--retry", "3", "-C", "-", "--progress-bar", "-o", part, url])
        if done.returncode != 0:
            raise IOError("the download stopped (curl said %d). Run the script again to go on." % done.returncode)
    else:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=120) as answer, open(part, "wb") as f:
            shutil.copyfileobj(answer, f, 1 << 20)
    os.replace(part, target)


def main():
    notes = json.load(open(os.path.join(HERE, "data", "research.json"), encoding="utf-8"))
    wanted = [(n, ident, "%s-%s" % (n["key"], ident)) for n in notes for ident in n.get("missing", [])]
    order = ["medium.mp4", "low.mp4"] if "--medium" in sys.argv else ["high.mp4", "medium.mp4", "low.mp4"]
    os.makedirs(INBOX, exist_ok=True)
    have = {os.path.splitext(f)[0].lower() for f in os.listdir(INBOX) if not f.endswith(".part")}
    todo = [w for w in wanted if w[2].lower() not in have]
    print("The lab notes wait for %d videos. %d already in build/video-in. %d to fetch from %s" % (len(wanted), len(wanted) - len(todo), len(todo), OLD_SITE))
    got, failed, total = 0, [], 0
    for n, ident, name in todo:
        try:
            address, size = head("%s/_api/v1/videos/%s/file" % (OLD_SITE, ident))
            base, choice = address.split("?")[0].rsplit("/", 1)
            for copy in order:
                try:
                    _, size = head("%s/%s" % (base, copy))
                    choice = copy
                    break
                except IOError:
                    continue
            print("%-34s %-11s %5.1f MB   %s" % (name, choice, (size or 0) / 1e6, n["title"][:60]))
            total += size or 0
            if "--list" in sys.argv:
                continue
            download("%s/%s" % (base, choice), os.path.join(INBOX, name + ".mp4"))
            got += 1
        except Exception as e:
            failed.append((name, str(e)[:200]))
            print("%-34s could not be fetched: %s" % (name, str(e)[:200]))
    if "--list" in sys.argv:
        print("In all: %.0f MB. Nothing was fetched." % (total / 1e6))
        return
    print("\nFetched: %d, %.0f MB. Not fetched: %d." % (got, total / 1e6, len(failed)))
    if got:
        print("Now run:   python3 build/make_research_media.py   and then   python3 build/build.py")


if __name__ == "__main__":
    main()
