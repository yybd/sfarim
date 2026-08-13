#!/usr/bin/env bash
# Publish a staged release to Cloudflare R2.
#
#   ./scripts/publish-r2.sh                      → macOS (releases/ from release-macos.sh)
#   ./scripts/publish-r2.sh --windows <file.exe> → Windows installer built by CI
#
# Layout on R2 (same as the other direct-download apps — SnippetBar, Iconduit…):
#
#   apps/sfarim/releases/Sfarim.dmg                          ← stable name: the website
#                                                               link and the appcast
#                                                               enclosure both point here
#   apps/sfarim/releases/<version>/Sfarim-<v>.dmg            ← versioned archive copy
#   apps/sfarim/releases/appcast.xml                         ← Sparkle feed
#   apps/sfarim/releases/windows/Sfarim-Setup.exe            ← stable name, Windows
#   apps/sfarim/releases/windows/<version>/Sfarim-Setup-<v>.exe
#
# Served at https://storage.bdtech.app/sfarim/releases/
#
# On macOS the DMG is uploaded first and the appcast last, so the feed never
# advertises a build that isn't downloadable yet. Windows has no update feed —
# Sparkle is macOS-only — so it is just the two copies of the installer.

set -euo pipefail
cd "$(dirname "$0")/.."

REMOTE="${REMOTE:-r2:apps/sfarim/releases}"
VERSION="$(python3 -c "import json;print(json.load(open('src-tauri/tauri.conf.json'))['version'])")"

# --- Windows ------------------------------------------------------------------
if [ "${1:-}" = "--windows" ]; then
  SRC="${2:-}"
  [ -n "$SRC" ] && [ -f "$SRC" ] \
    || { echo "❌ usage: $0 --windows <path-to-installer.exe>"; exit 1; }

  STABLE="Sfarim-Setup.exe"
  echo "▶︎ publishing Windows $VERSION to $REMOTE/windows"
  echo "   $(du -h "$SRC" | cut -f1) — this takes a while"

  rclone copyto "$SRC" "$REMOTE/windows/$STABLE"                              --progress --s3-chunk-size 64M
  rclone copyto "$SRC" "$REMOTE/windows/$VERSION/Sfarim-Setup-$VERSION.exe"   --progress --s3-chunk-size 64M

  echo
  echo "════════ published ════════"
  rclone ls "$REMOTE/windows"
  echo
  echo "✅ download:  https://storage.bdtech.app/sfarim/releases/windows/$STABLE"
  exit 0
fi

# --- macOS --------------------------------------------------------------------
STABLE_NAME="Sfarim.dmg"
DMG="releases/$STABLE_NAME"
APPCAST="releases/appcast.xml"

[ -f "$DMG" ] || { echo "❌ $DMG not found — run ./scripts/release-macos.sh first"; exit 1; }
[ -f "$APPCAST" ] || { echo "❌ $APPCAST not found — run ./scripts/release-macos.sh first"; exit 1; }

ARCHIVE="$(basename "${DMG%.dmg}")-${VERSION}.dmg"

echo "▶︎ publishing macOS $VERSION to $REMOTE"
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
