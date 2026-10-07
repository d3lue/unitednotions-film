#!/bin/sh
# Publishes from this Mac. The workshop on the server (~/unf-workshop) is the one that counts:
# the editing page at https://unitednotions.film/edit/ writes there, and the server builds the site from it.
# This script brings down what the server has, sends up what is new here, and asks the server to build.
#
#     sh publish.sh              bring down, send up, build on the server, check the live site
#     sh publish.sh --down       only bring the server's workshop down here (to look, or to edit)
#
# The SSH user is danfal17 unless UNF_USER says otherwise. The originals of the lab videos (build/video-in, 1.2 GB)
# stay here: the server has their web copies. A new video goes up with the page that shows it, through the editing page.
# Files travel as tar over ssh: the rsync and scp of this Mac do not always deliver.

set -eu
cd "$(dirname "$0")"
USER_NAME="${UNF_USER:-danfal17}"
HOST="${UNF_HOST:-iad1-shared-b7-43.dreamhost.com}"
W="unf-workshop"
AT="$USER_NAME@$HOST"

echo "== 1. Bringing down what the server's workshop has (pages added on the editing page, dates, pictures)"
mkdir -p build/pages-in build/picture-in
rm -rf build/pages-in/*
ssh "$AT" "cd $W/build && tar cf - pages-in data research picture-in 2>/dev/null" | tar xf - -C build
if [ "${1:-}" = "--down" ]; then
  echo "Done. The workshop here now matches the server."
  exit 0
fi

echo "== 2. Sending up what is here"
tar cf - --exclude='video-in' --exclude='__pycache__' --exclude='.DS_Store' -C build . | ssh "$AT" "tar xf - -C $W/build"
ssh "$AT" "cat > $W/check.sh" < check.sh
ssh "$AT" "cat > $W/server-publish.sh && chmod 755 $W/server-publish.sh" < server/server-publish.sh
# The editing page (server/edit/) is put on the server by hand, once: see EDITING.txt.

echo "== 3. Building on the server (about two minutes)"
ssh "$AT" "cd $W && rm -f publish.log && sh server-publish.sh; cat publish.log"
