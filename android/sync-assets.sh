#!/usr/bin/env bash
# Copies the web app (index.html, app.js, styles.css, assets/) into the
# Android project's asset bundle (app/src/main/assets/). The Android build
# does NOT read those files from the repo root directly -- it only sees
# whatever was last copied here, so run this after any change to the web
# app and before rebuilding the APK.
set -euo pipefail
cd "$(dirname "$0")/.."

DEST="android/app/src/main/assets"
rm -rf "$DEST"
mkdir -p "$DEST/assets"
cp index.html app.js styles.css "$DEST/"
cp assets/*.png "$DEST/assets/"
echo "Synced web assets into $DEST"
