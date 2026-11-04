"""Проверка Linux-выделения и буфера обмена."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qtranslate_r.platform.linux import selection  # noqa: E402


def read(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.decode("utf-8", "replace")


def write(args: list[str], text: str) -> None:
    subprocess.run(
        args,
        input=text.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        check=False,
    )


def check_primary() -> None:
    old_clipboard = read(["wl-paste", "--no-newline"])
    old_primary = read(["wl-paste", "--primary", "--no-newline"])
    try:
        write(["wl-copy", "--primary"], "selection-test")
        assert selection.capture_selection() == "selection-test"  # noqa: SLF001
        assert selection.set_clipboard("selection-test")
        assert read(["wl-paste", "--no-newline"]) == "selection-test"
    finally:
        write(["wl-copy"], old_clipboard)
        write(["wl-copy", "--primary"], old_primary)
    print("primary selection: OK")


def check_fallback() -> None:
    original = (selection._primary_text, selection._clipboard_text, selection._send_shortcut)
    calls = {"count": 0}
    keys: list[str] = []

    def clipboard() -> str:
        calls["count"] += 1
        return "before" if calls["count"] == 1 else "after"

    def shortcut(key: str) -> bool:
        keys.append(key)
        return True

    selection._primary_text = lambda: None  # noqa: SLF001
    selection._clipboard_text = clipboard  # noqa: SLF001
    selection._send_shortcut = shortcut  # noqa: SLF001
    try:
        assert selection.capture_selection() == "after"
        assert keys == ["c"]
    finally:
        selection._primary_text, selection._clipboard_text, selection._send_shortcut = original
    print("ctrl+c fallback: OK")


def check_paste() -> None:
    original = selection._send_shortcut
    keys: list[str] = []
    selection._send_shortcut = lambda key: keys.append(key) or True  # noqa: SLF001
    try:
        selection.paste_clipboard()
        assert keys == ["v"]
    finally:
        selection._send_shortcut = original  # noqa: SLF001
    print("ctrl+v: OK")


def main() -> int:
    if not sys.platform.startswith("linux"):
        print("SKIP: not Linux")
        return 0
    if (
        selection.session_type() == "x11"
        or not shutil.which("wl-paste")
        or not shutil.which("wl-copy")
    ):
        print("SKIP: wl-clipboard is not available")
        return 0

    check_primary()
    check_fallback()
    check_paste()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
