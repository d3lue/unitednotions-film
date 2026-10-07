#!/bin/sh
# Runs on the DreamHost server, in the workshop (~/unf-workshop). The editing page starts it, and so can a person:
#     ssh unfweb@iad1-shared-b7-43.dreamhost.com 'cd unf-workshop && sh server-publish.sh'
# It makes the web copies of new pictures and videos, builds the pages, copies them into the live folder and checks the site.
# Everything it says goes to publish.log. While it runs, publish.lock exists.

cd "$(dirname "$0")" || exit 1
LIVE="$HOME/unitednotions.film"
LOG="publish.log"
LOCK="publish.lock"
export PATH="$HOME/.local/bin:$PATH"

if [ -f "$LOCK" ] && [ "$(( $(date +%s) - $(stat -c %Y "$LOCK") ))" -lt 900 ]; then
  echo "A publish is already running." >> "$LOG"
  exit 1
fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT INT TERM

{
  echo "== Publish started $(date '+%Y-%m-%d %H:%M:%S')"
  echo "== 1. Pictures and videos"
  python3 build/make_research_media.py 2>&1
  echo "== 2. Building the pages"
  python3 build/build.py 2>&1 | tail -4
  echo "== 3. Into the live folder"
  rsync -rlt --delete \
    --exclude='.well-known' --exclude='.dh-diag' --exclude='edit' --exclude='assets/video' --exclude='.DS_Store' \
    site/ "$LIVE/" 2>&1 | tail -2
  find "$LIVE" -path "$LIVE/.dh-diag" -prune -o -type f -exec chmod 644 {} + 2>/dev/null
  find "$LIVE" -path "$LIVE/.dh-diag" -prune -o -type d -exec chmod 755 {} + 2>/dev/null
  echo "== 4. Checking the live site"
  sh check.sh https://unitednotions.film 2>&1 | grep -E '^(FAIL|passed)'
  echo "== Done $(date '+%Y-%m-%d %H:%M:%S')"
} >> "$LOG" 2>&1
