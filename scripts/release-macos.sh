#!/usr/bin/env bash
# Build, sign, notarize and staple Sfarim for direct download (outside the Mac App Store).
#
#   ./scripts/release-macos.sh              → Apple Silicon only (arm64)
#   ./scripts/release-macos.sh --universal  → universal binary (arm64 + Intel, ~2x size)
#
# Produces a Developer ID signed, notarized and stapled .app + .dmg.

set -euo pipefail

cd "$(dirname "$0")/.."

# --- Apple credentials --------------------------------------------------------
# This repo is public, so no ids are hardcoded here: the notarization credentials
# are read from the hub DATA.md (outside the repo) under "### key notarytool".
# Override by exporting APPLE_API_ISSUER / APPLE_API_KEY / APPLE_API_KEY_PATH first.
DATA_MD="${DATA_MD:-$HOME/Developer/app-hub/DATA.md}"
SIGNING_IDENTITY="${SIGNING_IDENTITY:-Developer ID Application: Yechiel Ben David (6AL5F29Z3D)}"

if [ -z "${APPLE_API_ISSUER:-}" ] || [ -z "${APPLE_API_KEY:-}" ] || [ -z "${APPLE_API_KEY_PATH:-}" ]; then
  [ -f "$DATA_MD" ] || { echo "❌ no credentials: $DATA_MD not found (or export APPLE_API_* yourself)"; exit 1; }
  block="$(awk '/^### key notarytool/{f=1;next} /^###/{f=0} f' "$DATA_MD")"
  export APPLE_API_ISSUER="${APPLE_API_ISSUER:-$(echo "$block" | sed -n 's/^Issuer ID:[[:space:]]*//p' | head -1)}"
  export APPLE_API_KEY="${APPLE_API_KEY:-$(echo "$block" | sed -n 's/^key id:[[:space:]]*//p' | head -1)}"
  export APPLE_API_KEY_PATH="${APPLE_API_KEY_PATH:-$(echo "$block" | sed -n 's/^p8:[[:space:]]*//p' | head -1)}"
fi

[ -n "$APPLE_API_ISSUER" ] && [ -n "$APPLE_API_KEY" ] \
  || { echo "❌ could not read notarytool issuer/key id from $DATA_MD"; exit 1; }
[ -f "$APPLE_API_KEY_PATH" ] || { echo "❌ notarytool key not found: $APPLE_API_KEY_PATH"; exit 1; }
security find-identity -v -p codesigning | grep -q "$SIGNING_IDENTITY" \
  || { echo "❌ signing identity not in keychain: $SIGNING_IDENTITY"; exit 1; }

# --- Sparkle ------------------------------------------------------------------
SPARKLE_KEY="${SPARKLE_KEY:-$HOME/Developer/myData/Sparkle/sparkle_private_key.txt}"
SPARKLE_TOOLS="${SPARKLE_TOOLS:-$HOME/Developer/myData/Sparkle/bin}"
FEED_BASE="https://storage.bdtech.app/sfarim/releases"
STABLE_NAME="Sfarim.dmg"   # published name — never changes between versions

[ -d src-tauri/Frameworks/Sparkle.framework ] \
  || { echo "❌ Sparkle.framework missing — run ./scripts/fetch-sparkle.sh first"; exit 1; }

# Sparkle ships ad-hoc signed and Tauri won't deep-sign it — notarization would
# reject its nested binaries. Sign it before the bundler copies it in.
SIGNING_IDENTITY="$SIGNING_IDENTITY" ./scripts/sign-sparkle.sh

# --- Build --------------------------------------------------------------------
echo "▶︎ building (this signs + notarizes + staples the .app)…"
if [ "${1:-}" = "--universal" ]; then
  BUNDLE_DIR="src-tauri/target/universal-apple-darwin/release/bundle"
  pnpm tauri build --target universal-apple-darwin
else
  BUNDLE_DIR="src-tauri/target/release/bundle"
  pnpm tauri build
fi

APP="$BUNDLE_DIR/macos/Sfarim.app"
DMG="$(ls -t "$BUNDLE_DIR"/dmg/*.dmg | head -1)"

# --- Notarize the DMG itself too ---------------------------------------------
# Tauri notarizes and staples the .app, but not the disk image it ships in.
# Without this the user still gets a Gatekeeper warning when opening the .dmg.
echo "▶︎ signing dmg: $DMG"
codesign --force --sign "$SIGNING_IDENTITY" --timestamp "$DMG"

echo "▶︎ notarizing dmg (can take several minutes — the image is large)…"
xcrun notarytool submit "$DMG" \
  --key "$APPLE_API_KEY_PATH" \
  --key-id "$APPLE_API_KEY" \
  --issuer "$APPLE_API_ISSUER" \
  --wait

echo "▶︎ stapling dmg…"
xcrun stapler staple "$DMG"

# --- Appcast (Sparkle) --------------------------------------------------------
# The published DMG always carries the STABLE name (Sfarim.dmg) — same convention
# as the other direct apps (SnippetBar.dmg, Iconduit.dmg…). That keeps the
# download link on the website valid forever and is what the appcast enclosure
# points at; scripts/publish-r2.sh also archives a versioned copy under <version>/.
if [ -f "$SPARKLE_KEY" ] && [ -x "$SPARKLE_TOOLS/generate_appcast" ]; then
  mkdir -p releases
  rm -f releases/*.dmg          # only ever one DMG in the staging dir
  cp "$DMG" "releases/$STABLE_NAME"
  echo "▶︎ generating signed appcast…"
  "$SPARKLE_TOOLS/generate_appcast" \
    --ed-key-file "$SPARKLE_KEY" \
    --download-url-prefix "$FEED_BASE/" \
    --link "https://www.bdtech.app" \
    releases
else
  echo "⚠️  skipping appcast: Sparkle key or tools missing ($SPARKLE_KEY / $SPARKLE_TOOLS)"
fi

# --- Verify -------------------------------------------------------------------
echo
echo "════════ verification ════════"
codesign --verify --deep --strict --verbose=2 "$APP"
codesign --verify --strict --verbose=2 "$APP/Contents/Frameworks/Sparkle.framework"
spctl -a -t exec -vvv "$APP"
xcrun stapler validate "$APP"
xcrun stapler validate "$DMG"
echo
echo "✅ ready for direct download:"
ls -lh "$DMG"
if [ -f releases/appcast.xml ]; then
  echo
  echo "📤 staged in releases/ — publish with ./scripts/publish-r2.sh"
  ls -lh releases/
fi
