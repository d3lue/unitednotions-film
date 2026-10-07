#!/bin/sh
# Tries the addresses of FOR-DAN.txt step 5 on the server and says which answer as they should.
#
#     sh check.sh                                       the live site, https://unitednotions.film
#     sh check.sh http://unitednotions.film 67.205.2.48   the DreamHost server, before the DNS change
#                                                         (the second word is the server's IP; the
#                                                          request goes there whatever DNS says)
#     sh check.sh http://something.dreamhosters.com      a dreamhosters.com preview address
#
# Needs only curl. Prints one line per check, then a count.

BASE="${1:-https://unitednotions.film}"
IP="${2:-}"
HOSTNAME_PART=$(printf '%s' "$BASE" | sed -E 's#^https?://##; s#/.*$##')
RESOLVE=""
if [ -n "$IP" ]; then
  RESOLVE="--resolve $HOSTNAME_PART:80:$IP --resolve $HOSTNAME_PART:443:$IP"
fi

pass=0; fail=0
TMP=$(mktemp)

# check PATH EXPECTED_STATUS [EXPECTED_LOCATION_SUFFIX] [TEXT_THAT_MUST_BE_IN_BODY]
check() {
  path="$1"; want="$2"; loc="${3:-}"; text="${4:-}"
  out=$(curl -s -o "$TMP" -m 30 $RESOLVE -D - "$BASE$path" 2>/dev/null)
  code=$(printf '%s' "$out" | head -1 | awk '{print $2}')
  got_loc=$(printf '%s' "$out" | grep -i '^location:' | tail -1 | sed 's/^[Ll]ocation: *//' | tr -d '\r')
  ok=1
  [ "$code" = "$want" ] || ok=0
  if [ -n "$loc" ]; then
    case "$got_loc" in *"$loc") ;; *) ok=0;; esac
  fi
  if [ -n "$text" ]; then
    grep -q -- "$text" "$TMP" || ok=0
  fi
  if [ $ok = 1 ]; then
    pass=$((pass+1)); printf 'ok    %-45s %s %s\n' "$path" "$code" "$got_loc"
  else
    fail=$((fail+1)); printf 'FAIL  %-45s got %s %s   wanted %s %s %s\n' "$path" "${code:-nothing}" "$got_loc" "$want" "$loc" "${text:+(body: $text)}"
  fi
}

# header PATH HEADER_NAME TEXT_THAT_MUST_BE_IN_IT
header() {
  path="$1"; name="$2"; text="$3"
  val=$(curl -s -o /dev/null -m 30 $RESOLVE -H 'Accept-Encoding: gzip' -D - "$BASE$path" 2>/dev/null | grep -i "^$name:" | tr -d '\r')
  case "$val" in
    *"$text"*) pass=$((pass+1)); printf 'ok    %-45s %s\n' "$path" "$val";;
    *) fail=$((fail+1)); printf 'FAIL  %-45s %s header: got "%s", wanted "%s"\n' "$path" "$name" "$val" "$text";;
  esac
}

echo "Checking $BASE ${IP:+(at $IP)}"
echo "--- the pages"
check /                                       200 "" "United Notions"
check /es/                                    200 "" "United Notions"
check /about                                  200
check /research                               200
check /people                                 200
check /about.html                             200
check /research/the-whale-that-watches-back   200
check /es/about                               200
check /people/violeta-ayala                   200
check /work/la-lucha                          200
echo "--- the files"
check /robots.txt                             200 "" "User-agent"
check /llms.txt                               200 "" "United Notions Film"
check /es/llms.txt                            200 "" "United Notions Film"
check /sitemap.xml                            200 "" "<loc>"
check /favicon.ico                            200
echo "--- the old site's addresses"
check /for-press-media                        301 /press
check /research-archive                       301 /research
check /films                                  301 "/#works"
check /now-playing                            301 "/#now"
check /news/huk                               301 "/news#press-huk-the-jaguaress"
check /birdbot                                302 /
echo "--- the slash rules"
check /research/                              301 /research
check /people/                                301 /people
check /work                                   302 "/#works"
check /about/                                 301 /about
echo "--- wrong addresses"
check /this-is-wrong                          404 "" "United Notions"
check /es/esto-no-existe                      404 "" "United Notions"
check /build/build.py                         404
check /FOR-DAN.txt                            404
check /assets/                                403
echo "--- headers"
header /es/llms.txt     Content-Type       "utf-8"
header /about           Content-Encoding   "gzip"
header /about           X-Content-Type-Options "nosniff"
header /assets/         Server             "Apache"

rm -f "$TMP"
echo
echo "passed: $pass   failed: $fail"
[ "$fail" = 0 ]
