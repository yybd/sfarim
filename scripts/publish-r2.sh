#!/usr/bin/env bash
# Publish the staged release in releases/ to Cloudflare R2.
#
# Layout on R2 (same as the other direct-download apps — SnippetBar, Iconduit…):
#
#   apps/sfarim/releases/Sfarim.dmg                  ← stable name: the website
#                                                       link and the appcast
#                                                       enclosure both point here
#   apps/sfarim/releases/<version>/Sfarim-<v>.dmg    ← versioned archive copy
#   apps/sfarim/releases/appcast.xml                 ← Sparkle feed
#
# Served at https://storage.bdtech.app/sfarim/releases/
#
# The DMG is uploaded first and the appcast last, so the feed never advertises a
# build that isn't downloadable yet.

set -euo pipefail
cd "$(dirname "$0")/.."

REMOTE="${REMOTE:-r2:apps/sfarim/releases}"
STABLE_NAME="Sfarim.dmg"
DMG="releases/$STABLE_NAME"
APPCAST="releases/appcast.xml"

[ -f "$DMG" ] || { echo "❌ $DMG not found — run ./scripts/release-macos.sh first"; exit 1; }
[ -f "$APPCAST" ] || { echo "❌ $APPCAST not found — run ./scripts/release-macos.sh first"; exit 1; }

VERSION="$(python3 -c "import json;print(json.load(open('src-tauri/tauri.conf.json'))['version'])")"
ARCHIVE="${DMG%.dmg}-${VERSION}.dmg"
ARCHIVE="$(basename "$ARCHIVE")"

echo "▶︎ publishing version $VERSION to $REMOTE"
echo "   $(du -h "$DMG" | cut -f1) — this takes a while"

rclone copyto "$DMG" "$REMOTE/$STABLE_NAME"          --progress --s3-chunk-size 64M
rclone copyto "$DMG" "$REMOTE/$VERSION/$ARCHIVE"     --progress --s3-chunk-size 64M
rclone copyto "$APPCAST" "$REMOTE/appcast.xml"       --progress

echo
echo "════════ published ════════"
rclone ls "$REMOTE"
echo
echo "✅ download:  https://storage.bdtech.app/sfarim/releases/$STABLE_NAME"
echo "✅ appcast:   https://storage.bdtech.app/sfarim/releases/appcast.xml"
