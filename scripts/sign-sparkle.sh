#!/usr/bin/env bash
# Re-sign Sparkle.framework with our Developer ID, inside out.
#
# Sparkle ships ad-hoc signed, and Tauri's bundler only signs the app itself —
# it does not deep-sign the nested binaries inside a bundled framework
# (Autoupdate, Updater.app, the XPC services). Apple's notary service rejects
# those ("not signed with a valid Developer ID certificate" / "does not include
# a secure timestamp"), so we sign the framework in place BEFORE the build:
# Tauri then copies an already-valid framework into the .app.

set -euo pipefail
cd "$(dirname "$0")/.."

SIGNING_IDENTITY="${SIGNING_IDENTITY:-Developer ID Application: Yechiel Ben David (6AL5F29Z3D)}"
FW="src-tauri/Frameworks/Sparkle.framework"

[ -d "$FW" ] || { echo "❌ $FW not found — run ./scripts/fetch-sparkle.sh first"; exit 1; }

sign() {
  codesign --force --sign "$SIGNING_IDENTITY" --options runtime --timestamp "$@"
}

echo "▶︎ signing Sparkle internals (inside out)…"
sign "$FW/Versions/B/XPCServices/Downloader.xpc"
sign "$FW/Versions/B/XPCServices/Installer.xpc"
sign "$FW/Versions/B/Updater.app"
sign "$FW/Versions/B/Autoupdate"
sign "$FW/Versions/B"

echo "▶︎ verifying…"
codesign --verify --deep --strict --verbose=2 "$FW"
codesign -dv "$FW" 2>&1 | grep -E "Authority=Developer ID|Timestamp=" | head -2
echo "✅ Sparkle.framework signed with: $SIGNING_IDENTITY"
