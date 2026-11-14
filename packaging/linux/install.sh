#!/bin/sh
set -eu

PREFIX="${PREFIX:-$HOME/.local}"
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
BINDIR="$PREFIX/bin"
APPDIR="$PREFIX/share/applications"
ICONDIR="$PREFIX/share/icons/hicolor/256x256/apps"

PYTHON="$ROOT/_local/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON=python3
fi

mkdir -p "$BINDIR" "$APPDIR" "$ICONDIR"

cat > "$BINDIR/qtranslate-remake" <<EOF
#!/bin/sh
exec "$PYTHON" "$ROOT/run.py" "\$@"
EOF
chmod 755 "$BINDIR/qtranslate-remake"

cp "$ROOT/packaging/linux/qtranslate-remake.png" "$ICONDIR/qtranslate-remake.png"
sed "s|^Exec=.*|Exec=$BINDIR/qtranslate-remake|" \
    "$ROOT/packaging/linux/qtranslate-remake.desktop" \
    > "$APPDIR/qtranslate-remake.desktop"
chmod 644 "$APPDIR/qtranslate-remake.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPDIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed QTranslate Remake:"
echo "  launcher: $BINDIR/qtranslate-remake"
echo "  desktop:  $APPDIR/qtranslate-remake.desktop"
echo "  icon:     $ICONDIR/qtranslate-remake.png"
echo "Run 'qtranslate-remake' or start it from the application menu."
