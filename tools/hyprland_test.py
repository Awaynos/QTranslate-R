"""Проверка установки биндов и правил Hyprland."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.platform.linux.hyprland import (  # noqa: E402
    BINDS_MARKER,
    RULES_MARKER,
    _trigger,
    config_targets,
    install,
    install_rules,
)

ENTRIES = (
    ("CTRL + ALT + Q", "--quick", "Quick translate"),
    ("CTRL + ALT + 1", "--replace", "Replace selection"),
    ("CTRL + ALT + I", "--ocr", "OCR"),
)


def check_conf(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "hyprland.conf"
    path.write_text("monitor=,preferred,auto,1\n", encoding="utf-8")

    target, changed = install(path, "/usr/bin/qtranslate-remake", entries=ENTRIES)
    assert changed and target == path
    text = path.read_text(encoding="utf-8")
    assert text.count(BINDS_MARKER) == 1
    for trigger, argument, _ in ENTRIES:
        assert f"bind = {trigger}, exec, /usr/bin/qtranslate-remake {argument}" in text

    rules, changed = install_rules(path)
    assert changed and rules == path
    text = path.read_text(encoding="utf-8")
    assert text.count(RULES_MARKER) == 1
    assert "windowrulev2 = float,title:^QTranslate Popup$" in text

    assert len(list(directory.glob("hyprland.conf.bak-*"))) == 2
    _, changed = install(path, "/usr/bin/qtranslate-remake", entries=ENTRIES)
    assert not changed
    _, changed = install_rules(path)
    assert not changed


def check_lua(directory: Path) -> None:
    binds = directory / "keybinds.lua"
    rules = directory / "rules.lua"
    binds.parent.mkdir(parents=True)
    binds.write_text('hl.bind("SUPER + X", hl.dsp.exec_cmd("test"))\n', encoding="utf-8")
    rules.write_text("", encoding="utf-8")

    target, changed = install(binds, "/usr/bin/qtranslate-remake", kind="lua", entries=ENTRIES)
    assert changed and target == binds
    text = binds.read_text(encoding="utf-8")
    assert text.count(BINDS_MARKER) == 1
    for trigger, argument, _ in ENTRIES:
        assert f'hl.bind("{trigger}"' in text
        assert f"/usr/bin/qtranslate-remake {argument}" in text

    target, changed = install_rules(rules, kind="lua")
    assert changed and target == rules
    text = rules.read_text(encoding="utf-8")
    assert text.count(RULES_MARKER) == 1
    assert 'move = {"cursor_x", "cursor_y"}' in text

    assert len(list(directory.glob("keybinds.lua.bak-*"))) == 1
    assert len(list(directory.glob("rules.lua.bak-*"))) == 1
    _, changed = install(binds, "/usr/bin/qtranslate-remake", kind="lua", entries=ENTRIES)
    assert not changed
    _, changed = install_rules(rules, kind="lua")
    assert not changed


def check_replacement(directory: Path) -> None:
    directory.mkdir(parents=True)
    path = directory / "keybinds.lua"
    path.write_text("", encoding="utf-8")
    install(path, "/usr/bin/qtranslate-remake", kind="lua", entries=ENTRIES)
    changed_entries = (("SUPER + F9", "--quick", "Quick translate"),)
    _, changed = install(path, "/usr/bin/qtranslate-remake", kind="lua", entries=changed_entries)
    assert changed
    text = path.read_text(encoding="utf-8")
    assert 'hl.bind("SUPER + F9"' in text
    assert 'hl.bind("CTRL + ALT + Q"' not in text
    assert text.count(BINDS_MARKER) == 1


def check_detection(directory: Path) -> None:
    base = directory / "config" / "hypr"
    base.mkdir(parents=True)
    (base / "hyprland.lua").write_text("", encoding="utf-8")
    (base / "custom").mkdir()
    old = os.environ.get("XDG_CONFIG_HOME")
    os.environ["XDG_CONFIG_HOME"] = str(directory / "config")
    try:
        binds, rules, kind = config_targets()
        assert kind == "lua"
        assert binds == base / "custom" / "keybinds.lua"
        assert rules == base / "custom" / "rules.lua"

        (base / "custom").rmdir()
        (base / "user.lua").write_text("", encoding="utf-8")
        binds, rules, kind = config_targets()
        assert kind == "lua"
        assert binds == base / "user.lua"
        assert rules == base / "user.lua"
    finally:
        if old is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = old


def check_existing_binds(directory: Path) -> None:
    directory.mkdir(parents=True)
    path = directory / "user.lua"
    path.write_text(
        'hl.bind("CTRL + ALT + Q", hl.dsp.exec_cmd("qtr --quick"))\n'
        'hl.bind("CTRL + ALT + 1", hl.dsp.exec_cmd("qtr --replace"))\n'
        'hl.bind("CTRL + ALT + I", hl.dsp.exec_cmd("qtr --ocr"))\n',
        encoding="utf-8",
    )
    _, changed = install(path, "/usr/bin/qtranslate-remake", kind="lua", entries=ENTRIES)
    assert not changed
    _, changed = install_rules(path, kind="lua")
    assert changed
    text = path.read_text(encoding="utf-8")
    assert text.count(RULES_MARKER) == 1
    assert text.count(BINDS_MARKER) == 0


def main() -> int:
    assert _trigger("Ctrl+Shift+F1") == "CTRL + SHIFT + F1"
    assert _trigger("Ctrl+,") == "CTRL + comma"
    assert _trigger("bad") is None

    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        check_conf(directory / "conf")
        check_lua(directory / "lua")
        check_replacement(directory / "replace")
        check_detection(directory / "detect")
        check_existing_binds(directory / "existing")

    print("hyprland rules and binds: OK")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
