#!/bin/bash
# bundle.sh — make a SELF-CONTAINED copy for Shaka's laptop.
#
#   ./bundle.sh
#     → /shared/ohana-bot/totem-web/        (browsable)
#     → /shared/ohana-bot/totem-web.tar.gz  (downloadable)
#
# The bundle carries its own bridge/ + personas/ + packs/, so it runs anywhere
# with Python 3 — no /shared, no Taurus, no network.
set -u
cd "$(dirname "$0")"
SRC=/shared/ohana-bot
OUT=/shared/ohana-bot/totem-web

./build.sh >/dev/null || { echo "build failed"; exit 2; }

rsync -a --delete \
  --exclude '__pycache__' --exclude '*.pyc' --exclude 'audio/cache' --exclude 'audio/ref' \
  --exclude '*.log' --exclude 'memory.json' --exclude 'smoke-memory.json' \
  --exclude 'src/.app.patched.js' \
  ./ "$OUT/"

# the mind travels with the body
rsync -a --exclude '__pycache__' --exclude 'memory.json' "$SRC/bridge/"   "$OUT/bridge/"
rsync -a "$SRC/personas/" "$OUT/personas/"
rsync -a "$SRC/packs/"    "$OUT/packs/"
cp "$SRC/HARDWARE.md" "$OUT/HARDWARE.md" 2>/dev/null

tar czf "$SRC/totem-web.tar.gz" -C "$SRC" totem-web
echo "bundled → $OUT"
du -sh "$OUT" "$SRC/totem-web.tar.gz"
