#!/bin/sh
# Puts the editing page on the DreamHost server. Run once, from this folder on a Mac:
#     sh server/install-editing.sh
# It sends the workshop up (the program that writes the pages), puts the editing page at /edit/ in the site,
# adds the cron line that runs a publish when the editing page asks for one, and checks that /edit/ asks for a password.
# Running it again is harmless: it only replaces what it put there before.
# The password file must be readable by the web server (644): Apache runs as another user and answers 500 otherwise.
#
# The password file is made once, by hand, and asks you to type the password:
#     ssh unfweb@iad1-shared-b7-43.dreamhost.com 'htpasswd -cB ~/unf-workshop/.htpasswd unf'
# Files travel as tar over ssh: the rsync and scp of this Mac do not always deliver.

set -eu
cd "$(dirname "$0")/.."
USER_NAME="${UNF_USER:-unfweb}"
HOST="${UNF_HOST:-iad1-shared-b7-43.dreamhost.com}"
AT="$USER_NAME@$HOST"
W="unf-workshop"
SITE="unitednotions.film"

echo "== 1. The workshop: the program that writes the pages, the publish script, the checks"
# the pages written on the editing page are never sent up: the server's are the ones that count
tar cf - --exclude='video-in' --exclude='__pycache__' --exclude='.DS_Store' --exclude='./pages-in' --exclude='./picture-in' --exclude='./data/research*.json' -C build . \
  | ssh "$AT" "mkdir -p $W/build && tar xf - -C $W/build && mkdir -p $W/build/pages-in $W/build/picture-in"
ssh "$AT" "cat > $W/check.sh && chmod 755 $W/check.sh" < check.sh
ssh "$AT" "cat > $W/server-publish.sh && chmod 755 $W/server-publish.sh" < server/server-publish.sh
ssh "$AT" "echo \"   pages from the editing page: \$(grep -c inbox_pages $W/build/make_research_media.py) (1 or more is right)\""

echo "== 2. The editing page, at https://$SITE/edit/"
ssh "$AT" "mkdir -p $SITE/edit && cat > $SITE/edit/index.php" < server/edit/index.php
# the password file is named with its full path, which has the user in it
sed "s|/home/[a-z0-9_]*/unf-workshop/.htpasswd|/home/$USER_NAME/unf-workshop/.htpasswd|" server/edit/.htaccess \
  | ssh "$AT" "cat > $SITE/edit/.htaccess && chmod 644 $SITE/edit/index.php $SITE/edit/.htaccess"

echo "== 3. The cron lines: once a minute, run a publish if the editing page asked for one; every quarter hour, count the visitors"
ssh "$AT" 'LINE="* * * * * cd \$HOME/unf-workshop && if [ -f publish.requested ]; then rm -f publish.requested; sh server-publish.sh; fi >/dev/null 2>&1"; VIS="*/15 * * * * cd \$HOME/unf-workshop && python3 build/visitors.py >/dev/null 2>&1"; (crontab -l 2>/dev/null | grep -v -e publish.requested -e visitors.py; echo "$LINE"; echo "$VIS") | crontab -; echo "   $(crontab -l | grep -c -e publish.requested -e visitors.py) cron lines in place"'

echo "== 4. The password file"
ssh "$AT" "if [ -s $W/.htpasswd ]; then chmod 644 $W/.htpasswd; echo \"   exists, names: \$(cut -d: -f1 $W/.htpasswd | tr '\n' ' ')\"; else echo \"   MISSING. Make it:  ssh $AT 'htpasswd -cB ~/$W/.htpasswd unf'\"; fi"

echo "== 5. Does the page ask for a password?"
CODE=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "https://$SITE/edit/")
if [ "$CODE" = "401" ]; then echo "   yes: /edit/ answers 401 until a name and password are given. Done."
else echo "   no: /edit/ answered $CODE. Look at the folder $SITE/edit on the server."; fi
