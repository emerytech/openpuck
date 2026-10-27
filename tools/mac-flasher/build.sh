#!/usr/bin/env bash
# Build "OpenPuck Flasher.app" from src/main.swift with swiftc (no Xcode project).
set -euo pipefail

APP="OpenPuck Flasher"
BUNDLE="$APP.app"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/build"
CONTENTS="$OUT/$BUNDLE/Contents"

rm -rf "$OUT/$BUNDLE"
mkdir -p "$CONTENTS/MacOS" "$CONTENTS/Resources"

echo "Compiling…"
xcrun swiftc -O -parse-as-library -target arm64-apple-macos13.0 \
    "$ROOT/src/main.swift" \
    -o "$CONTENTS/MacOS/$APP"

cp "$ROOT/Info.plist" "$CONTENTS/Info.plist"

# Ad-hoc sign so it runs locally (personal use). Swap `-` for your Developer ID
# + a notarize step if you ever want to hand it to someone else.
codesign --force --sign - "$OUT/$BUNDLE" >/dev/null 2>&1 || echo "(codesign skipped)"

echo "Built: $OUT/$BUNDLE"
echo "Run:   open \"$OUT/$BUNDLE\""
