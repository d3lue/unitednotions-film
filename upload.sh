#!/bin/sh
# Uploads site/ to DreamHost with rsync over SSH. Run from inside this folder:
#
#     sh upload.sh USERNAME              a dry run: shows what would change, uploads nothing
#     sh upload.sh USERNAME go           uploads
#
# USERNAME is the SFTP/SSH user DreamHost made for unitednotions.film. It asks for the password.
# The folder on the server is /home/USERNAME/unitednotions.film (DreamHost's usual place).
# Another folder:   UNF_DEST=/home/USERNAME/other.folder sh upload.sh USERNAME go
# Another server:   UNF_HOST=xyz.dreamhost.com sh upload.sh USERNAME go
#
# What it does:
#   - sends everything inside site/, including the hidden .htaccess files
#   - files become 644 and folders 755 on the server
#   - deletes on the server what is no longer in site/ (so an old page does not linger),
#     but leaves .well-known and .dh-diag alone: DreamHost uses them for the HTTPS certificate and diagnostics
#   - .DS_Store files of the Mac are not sent

set -eu
cd "$(dirname "$0")"

USER_NAME="${1:-}"
MODE="${2:-dry}"
HOST="${UNF_HOST:-iad1-shared-b7-43.dreamhost.com}"
DEST="${UNF_DEST:-/home/$USER_NAME/unitednotions.film}"

if [ -z "$USER_NAME" ]; then
  echo "usage: sh upload.sh USERNAME [go]" >&2
  exit 2
fi
if [ ! -f site/.htaccess ] || [ ! -f site/es/.htaccess ]; then
  echo "site/.htaccess or site/es/.htaccess is missing. Nothing uploaded." >&2
  exit 1
fi

if [ "$MODE" = "go" ]; then
  DRY=""
  echo "Uploading site/ to $USER_NAME@$HOST:$DEST"
else
  DRY="--dry-run"
  echo "DRY RUN (nothing is sent). Add 'go' to upload.  Target: $USER_NAME@$HOST:$DEST"
fi

rsync -rlt --progress --itemize-changes $DRY \
  --delete --exclude='.well-known' --exclude='.dh-diag' --exclude='.DS_Store' \
  site/ "$USER_NAME@$HOST:$DEST/"

echo
if [ "$MODE" = "go" ]; then
  echo "Setting files to 644 and folders to 755 on the server"
  ssh "$USER_NAME@$HOST" "find '$DEST' -type f -exec chmod 644 {} + ; find '$DEST' -type d -exec chmod 755 {} +"
  echo "Done. Now:  sh check.sh http://unitednotions.film 67.205.2.48   (before the DNS change)"
else
  echo "That was a dry run."
fi
