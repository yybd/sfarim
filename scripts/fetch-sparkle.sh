#!/usr/bin/env bash
# Fetch the Sparkle framework into src-tauri/Frameworks/ (gitignored — it is a
# 3 MB binary and this repo is public). Run once per clone / machine.
#
# The version is pinned and the download is checksum-verified.

set -euo pipefail
cd "$(dirname "$0")/.."

SPARKLE_VERSION="2.8.1"
SPARKLE_SHA256="5cddb7695674ef7704268f38eccaee80e3accbf19e61c1689efff5b6116d85be"
URL="https://github.com/sparkle-project/Sparkle/releases/download/${SPARKLE_VERSION}/Sparkle-${SPARKLE_VERSION}.tar.xz"

if [ -d src-tauri/Frameworks/Sparkle.framework ]; then
  echo "✅ Sparkle.framework already present — nothing to do."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "▶︎ downloading Sparkle ${SPARKLE_VERSION}…"
curl -fsSL -o "$TMP/sparkle.tar.xz" "$URL"

echo "▶︎ verifying checksum…"
echo "${SPARKLE_SHA256}  $TMP/sparkle.tar.xz" | shasum -a 256 -c - \
  || { echo "❌ checksum mismatch — refusing to install"; exit 1; }

tar -xJf "$TMP/sparkle.tar.xz" -C "$TMP"
mkdir -p src-tauri/Frameworks
cp -R "$TMP/Sparkle.framework" src-tauri/Frameworks/

# The signing/appcast tools are studio-wide, next to the shared EdDSA key.
TOOLS_DIR="$HOME/Developer/myData/Sparkle/bin"
if [ ! -x "$TOOLS_DIR/generate_appcast" ]; then
  mkdir -p "$TOOLS_DIR"
  cp "$TMP"/bin/{BinaryDelta,generate_appcast,generate_keys,sign_update} "$TOOLS_DIR/"
  echo "▶︎ installed Sparkle tools into $TOOLS_DIR"
fi

echo "✅ Sparkle ${SPARKLE_VERSION} installed into src-tauri/Frameworks/"
