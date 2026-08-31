#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APK_PATH="$ROOT_DIR/app/build/outputs/apk/release/app-release.apk"

cd "$ROOT_DIR"

echo "== Running unit tests =="
./gradlew testDebugUnitTest

echo "== Building release APK =="
./gradlew assembleRelease

if [[ ! -f "$APK_PATH" ]]; then
  echo "Release APK not found: $APK_PATH" >&2
  exit 1
fi

APKSIGNER="${ANDROID_HOME:-}/build-tools/35.0.1/apksigner"
if [[ ! -x "$APKSIGNER" ]]; then
  APKSIGNER="$(find "${ANDROID_HOME:-$HOME/Library/Android/sdk}" "$HOME/Library/Android/sdk" -path '*build-tools*apksigner' -type f 2>/dev/null | sort | tail -n 1)"
fi

if [[ -z "${APKSIGNER:-}" || ! -x "$APKSIGNER" ]]; then
  echo "apksigner not found. APK was built, but signature was not verified." >&2
  echo "$APK_PATH"
  exit 1
fi

echo "== Verifying APK signature =="
"$APKSIGNER" verify --verbose --print-certs "$APK_PATH"

echo "== Release APK ready =="
ls -lh "$APK_PATH"
