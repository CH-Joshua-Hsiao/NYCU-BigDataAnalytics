#!/usr/bin/env bash
# Download GH Archive hour files for a date range into HW2/raw.
# Usage: tools/download_raw.sh START_DATE END_DATE   (inclusive, YYYY-MM-DD, UTC)
# Skips files already present (resumable). Source: https://www.gharchive.org
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="${RAW_DIR:-$HERE/raw}"
mkdir -p "$RAW"
start="$1"; end="$2"
d="$start"; ok=0; skip=0; fail=0
while :; do
  for h in $(seq 0 23); do
    f="${d}-${h}.json.gz"; out="${RAW}/${f}"
    if [ -s "$out" ]; then skip=$((skip+1)); continue; fi
    if curl -fsS --retry 3 --retry-delay 2 -o "$out" "https://data.gharchive.org/${f}"; then
      ok=$((ok+1)); else fail=$((fail+1)); rm -f "$out"; fi
  done
  [ "$d" = "$end" ] && break
  d=$(date -u -d "$d +1 day" +%Y-%m-%d)
done
echo "DONE downloaded=$ok skipped=$skip failed=$fail"; du -sh "$RAW"
