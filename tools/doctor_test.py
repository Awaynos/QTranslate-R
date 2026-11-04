"""Проверка определения окружения, XDG-путей и диагностики."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qtranslate_r.config import paths  # noqa: E402
from qtranslate_r.platform.linux import env  # noqa: E402
from qtranslate_r.platform.linux.doctor import report  # noqa: E402

KEYS = (
    "XDG_SESSION_TYPE",
    "WAYLAND_DISPLAY",
    "DISPLAY",
    "XDG_CURRENT_DESKTOP",
    "XDG_DATA_HOME",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
)


def snapshot() -> dict[str, str | None]:
    return {key: os.environ.get(key) for key in KEYS}


def restore(values: dict[str, str | None]) -> None:
    for key, value in values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def check_session() -> None:
    for key in ("XDG_SESSION_TYPE", "WAYLAND_DISPLAY", "DISPLAY"):
        os.environ.pop(key, None)

    os.environ["XDG_SESSION_TYPE"] = "wayland"
    assert env.session_type() == "wayland"

    os.environ["XDG_SESSION_TYPE"] = "x11"
    assert env.session_type() == "x11"

    os.environ.pop("XDG_SESSION_TYPE")
    os.environ["WAYLAND_DISPLAY"] = "wayland-1"
    assert env.session_type() == "wayland"

    os.environ.pop("WAYLAND_DISPLAY")
    os.environ["DISPLAY"] = ":0"
    assert env.session_type() == "x11"

    os.environ.pop("DISPLAY")
    assert env.session_type() == "unknown"

    os.environ["XDG_CURRENT_DESKTOP"] = "Hyprland"
    assert env.desktop() == "Hyprland"
    assert env.detect().hyprland
    print("session/desktop: OK")


def check_xdg_paths() -> None:
    original = paths.is_frozen
    paths.is_frozen = lambda: True
    try:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            os.environ["XDG_DATA_HOME"] = str(base / "data")
            os.environ["XDG_CONFIG_HOME"] = str(base / "config")
            os.environ["XDG_CACHE_HOME"] = str(base / "cache")

            assert paths.user_data_dir() == base / "data" / paths.APP_DIR_NAME
            assert paths.user_config_dir() == base / "config" / paths.APP_DIR_NAME
            assert paths.user_cache_dir() == base / "cache" / paths.APP_DIR_NAME
            assert paths.settings_file() == base / "config" / paths.APP_DIR_NAME / "settings.json"
            assert paths.history_file() == base / "data" / paths.APP_DIR_NAME / "history.json"
            assert paths.cache_dir().is_dir()

            os.environ["XDG_DATA_HOME"] = "relative/path"
            assert paths.user_data_dir() == Path.home() / ".local/share" / paths.APP_DIR_NAME
    finally:
        paths.is_frozen = original
    print("xdg paths: OK")


def check_report() -> None:
    lines = report()
    assert lines[0] == "QTranslate Remake: platform diagnostics"
    assert any(line.startswith("session: ") for line in lines)
    assert "tools:" in lines
    print("doctor report: OK")


def main() -> int:
    saved = snapshot()
    try:
        check_session()
        check_xdg_paths()
        check_report()
    finally:
        restore(saved)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
