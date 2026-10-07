#!/bin/sh
# Builds the site, uploads it to DreamHost and checks it. One command, from inside this folder:
#
#     sh publish.sh                 build, upload, check
#     sh publish.sh --no-build      upload and check what is in site/ now
#     sh publish.sh --dry           build, then only show what the upload would change
#
# The SSH user is danfal17 unless UNF_USER says otherwise:   UNF_USER=someone sh publish.sh
# Before the first run on a new Mac:   pip3 install --user pillow numpy fonttools brotli

set -eu
cd "$(dirname "$0")"
USER_NAME="${UNF_USER:-danfal17}"
MODE="${1:-}"

if [ "$MODE" != "--no-build" ]; then
  echo "== 1. Pictures and videos that are new since last time"
  python3 build/make_research_media.py
  echo
  echo "== 2. Building the pages (about two minutes)"
  python3 build/build.py | tail -3
  echo
fi

if [ "$MODE" = "--dry" ]; then
  echo "== 3. What the upload would change (dry run)"
  sh upload.sh "$USER_NAME" | grep -E '^(<f|cd|\*deleting)' || true
  exit 0
fi

echo "== 3. Uploading"
sh upload.sh "$USER_NAME" go | grep -vE '^ +[0-9]' || true
echo
echo "== 4. Checking the live site"
sh check.sh https://unitednotions.film
