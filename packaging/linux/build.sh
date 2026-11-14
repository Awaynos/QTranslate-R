#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PYTHON="${PYTHON:-$ROOT/_local/.venv/bin/python}"
LOCAL="$ROOT/_local"
DIST="$LOCAL/dist"
BUILD="$LOCAL/build/linux"
VERSION=$(cat "$ROOT/VERSION")
VARIANT="${VARIANT:-arch}"
STAGE="$BUILD/QTranslateRemake-$VERSION-linux-$VARIANT"

if [ ! -x "$PYTHON" ]; then
    echo "Python environment not found: $PYTHON" >&2
    exit 1
fi
if ! "$PYTHON" -c "import PyInstaller" >/dev/null 2>&1; then
    echo "Install PyInstaller first:" >&2
    echo "  $PYTHON -m pip install pyinstaller" >&2
    exit 1
fi

rm -rf "$BUILD" "$DIST/$VARIANT"
mkdir -p "$BUILD" "$DIST"

"$PYTHON" -m PyInstaller \
    --noconfirm --clean --onefile \
    --name QTranslateRemake \
    --add-data "$ROOT/languages:languages" \
    --add-data "$ROOT/icons:icons" \
    --add-data "$ROOT/VERSION:." \
    --collect-submodules qtranslate_r \
    --workpath "$BUILD/pyinstaller" \
    --distpath "$DIST/$VARIANT" \
    --specpath "$BUILD" \
    "$ROOT/run.py"

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp "$DIST/$VARIANT/QTranslateRemake" "$STAGE/"
cp "$ROOT/packaging/linux/qtranslate-remake.desktop" "$STAGE/"
cp "$ROOT/packaging/linux/qtranslate-remake.png" "$STAGE/"
cp "$ROOT/LICENSE" "$ROOT/LICENSE.ru.md" "$STAGE/"
tar -C "$BUILD" -czf "$DIST/QTranslateRemake-$VERSION-linux-$VARIANT.tar.gz" "QTranslateRemake-$VERSION-linux-$VARIANT"

echo "Binary: $DIST/$VARIANT/QTranslateRemake"
echo "Archive: $DIST/QTranslateRemake-$VERSION-linux-$VARIANT.tar.gz"
