#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
LOCAL="$ROOT/_local"
DIST="$LOCAL/dist"
BUILD="$LOCAL/build/appimage"
VERSION=$(cat "$ROOT/VERSION")
VARIANT="${VARIANT:-universal}"
BINARY="${BINARY:-$DIST/universal/QTranslateRemake}"
APPDIR="$BUILD/QTranslateRemake-$VARIANT.AppDir"
OUT="$DIST/QTranslateRemake-$VERSION-linux-$VARIANT-x86_64.AppImage"
TOOL="${APPIMAGETOOL:-}"

if [ ! -x "$BINARY" ]; then
    echo "Build the Linux binary first: packaging/linux/build.sh" >&2
    exit 1
fi
if [ -z "$TOOL" ]; then
    TOOL=$(command -v appimagetool 2>/dev/null || true)
fi
if [ -z "$TOOL" ]; then
    echo "appimagetool not found. Set APPIMAGETOOL=/path/to/appimagetool." >&2
    exit 1
fi

rm -rf "$BUILD"
mkdir -p "$APPDIR/usr/bin" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$BINARY" "$APPDIR/usr/bin/QTranslateRemake"
chmod 755 "$APPDIR/usr/bin/QTranslateRemake"

cp "$ROOT/packaging/linux/qtranslate-remake.png" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps/qtranslate-remake.png"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/qtranslate-remake.png" \
    "$APPDIR/qtranslate-remake.png"

sed "s|^Exec=.*|Exec=QTranslateRemake|" \
    "$ROOT/packaging/linux/qtranslate-remake.desktop" \
    > "$APPDIR/qtranslate-remake.desktop"
cp "$APPDIR/qtranslate-remake.desktop" \
    "$APPDIR/usr/share/applications/qtranslate-remake.desktop"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$HERE/usr/bin/QTranslateRemake" "$@"
EOF
chmod 755 "$APPDIR/AppRun"

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" "$APPDIR" "$OUT"

echo "AppImage: $OUT"
