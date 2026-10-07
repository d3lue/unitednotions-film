#!/bin/sh
# Moves the workshop and the editing page from one DreamHost user to another, once. The site then runs under a user
# that owns nothing else, so the editing page can reach nothing else. Run from this folder on a Mac, after:
#     1. the panel has a new shell user (Users > Manage Users), and unitednotions.film is set to run under it
#        (Websites > Manage Websites > Edit): DreamHost copies the site's files across itself;
#     2. the new user accepts your key:   ssh-copy-id NEW@iad1-shared-b7-43.dreamhost.com
# Then:
#     sh server/move-to-user.sh OLD NEW        for example   sh server/move-to-user.sh danfal17 unfweb
# The old user's folders are left in place, to delete when you are sure. Its cron line and editing page are removed.

set -eu
cd "$(dirname "$0")/.."
OLD="${1:?the old user, for example danfal17}"
NEW="${2:?the new user, for example unfweb}"
HOST="${UNF_HOST:-iad1-shared-b7-43.dreamhost.com}"

echo "== 0. Both users answer?"
ssh "$OLD@$HOST" 'echo "   $USER: ok"'
ssh "$NEW@$HOST" 'echo "   $USER: ok, site folder has $(find ~/unitednotions.film -type f 2>/dev/null | wc -l) files"'

echo "== 1. The workshop, from $OLD to $NEW (the pages written so far, their pictures, the password file; not the videos)"
ssh "$OLD@$HOST" "tar cf - --exclude='unf-workshop/site/assets/video' unf-workshop" | ssh "$NEW@$HOST" 'tar xf - && echo "   copied: $(du -sh ~/unf-workshop | cut -f1)"'

echo "== 2. Python packages for $NEW"
ssh "$NEW@$HOST" 'python3 -m pip install --user -q --break-system-packages pillow numpy fonttools brotli 2>&1 | grep -viE "notice|warning|already" | tail -1; python3 -c "import PIL, numpy, fontTools, brotli; print(\"   packages OK\")"'

echo "== 3. The GitHub deploy key, so Actions can publish as $NEW"
ssh "$NEW@$HOST" 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && cat >> ~/.ssh/authorized_keys && echo "   added"' < ~/.ssh/unf-deploy-key.pub

echo "== 4. The editing page, the program and the cron line, under $NEW"
UNF_USER="$NEW" sh server/install-editing.sh

echo "== 5. The editing page and the cron line leave $OLD (its folders stay)"
ssh "$OLD@$HOST" '(crontab -l 2>/dev/null | grep -v publish.requested) | crontab - 2>/dev/null || true; rm -rf ~/unitednotions.film/edit; echo "   done"'

echo "== 6. A publish under $NEW, to be sure the build runs there (about two minutes)"
ssh "$NEW@$HOST" 'cd ~/unf-workshop && rm -f publish.log && sh server-publish.sh; tail -3 publish.log'
echo "Done. The site and its editing page now run under $NEW."
