"""Проверка установки desktop-файлов и app id."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.platform.linux import app as linux_app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def check_install() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp)
        env = dict(os.environ)
        env["PREFIX"] = str(prefix)
        result = subprocess.run(
            ["sh", str(ROOT / "packaging/linux/install.sh")],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr

        launcher = prefix / "bin/qtranslate-remake"
        desktop = prefix / "share/applications/qtranslate-remake.desktop"
        icon = prefix / "share/icons/hicolor/256x256/apps/qtranslate-remake.png"
        assert launcher.is_file() and os.access(launcher, os.X_OK)
        assert desktop.is_file() and icon.is_file()
        assert f"Exec={launcher}" in desktop.read_text(encoding="utf-8")
        assert "run.py" in launcher.read_text(encoding="utf-8")
    print("install: OK")


def check_identity() -> None:
    class FakeGuiApplication:
        value = ""

        @staticmethod
        def setDesktopFileName(name: str) -> None:
            FakeGuiApplication.value = name

    old_data = os.environ.get("XDG_DATA_HOME")
    old_dirs = os.environ.get("XDG_DATA_DIRS")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "applications").mkdir()
        os.environ["XDG_DATA_HOME"] = str(base)
        os.environ["XDG_DATA_DIRS"] = ""
        original = linux_app.QGuiApplication
        linux_app.QGuiApplication = FakeGuiApplication
        try:
            linux_app.set_taskbar_identity()
            assert FakeGuiApplication.value == ""
            (base / "applications/qtranslate-remake.desktop").write_text("", encoding="utf-8")
            linux_app.set_taskbar_identity()
            assert FakeGuiApplication.value == linux_app.DESKTOP_ID
        finally:
            linux_app.QGuiApplication = original
            if old_data is None:
                os.environ.pop("XDG_DATA_HOME", None)
            else:
                os.environ["XDG_DATA_HOME"] = old_data
            if old_dirs is None:
                os.environ.pop("XDG_DATA_DIRS", None)
            else:
                os.environ["XDG_DATA_DIRS"] = old_dirs
    print("desktop identity: OK")


def main() -> int:
    check_install()
    check_identity()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
