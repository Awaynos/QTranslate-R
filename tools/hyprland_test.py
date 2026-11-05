"""Проверка установки биндов и правил Hyprland."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.platform.linux.hyprland import (  # noqa: E402
    BINDS,
    BINDS_MARKER,
    RULES_MARKER,
    config_targets,
    install,
    install_rules,
)


def check_conf(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "hyprland.conf"
    path.write_text("monitor=,preferred,auto,1\n", encoding="utf-8")

    target, changed = install(path, "/usr/bin/qtranslate-remake")
    assert changed and target == path
    text = path.read_text(encoding="utf-8")
    assert text.count(BINDS_MARKER) == 1
    for key, argument, _ in BINDS:
        assert f"bind = CTRL ALT, {key}, exec, /usr/bin/qtranslate-remake {argument}" in text

    rules, changed = install_rules(path)
    assert changed and rules == path
    text = path.read_text(encoding="utf-8")
    assert text.count(RULES_MARKER) == 1
    assert "windowrulev2 = float,title:^QTranslate Popup$" in text

    assert len(list(directory.glob("hyprland.conf.bak-*"))) == 2
    _, changed = install(path, "/usr/bin/qtranslate-remake")
    assert not changed
    _, changed = install_rules(path)
    assert not changed


def check_lua(directory: Path) -> None:
    binds = directory / "keybinds.lua"
    rules = directory / "rules.lua"
    binds.parent.mkdir(parents=True)
    binds.write_text('hl.bind("SUPER + X", hl.dsp.exec_cmd("test"))\n', encoding="utf-8")
    rules.write_text("", encoding="utf-8")

    target, changed = install(binds, "/usr/bin/qtranslate-remake", kind="lua")
    assert changed and target == binds
    text = binds.read_text(encoding="utf-8")
    assert text.count(BINDS_MARKER) == 1
    for key, argument, _ in BINDS:
        assert f'hl.bind("CTRL + ALT + {key}"' in text
        assert f"/usr/bin/qtranslate-remake {argument}" in text

    target, changed = install_rules(rules, kind="lua")
    assert changed and target == rules
    text = rules.read_text(encoding="utf-8")
    assert text.count(RULES_MARKER) == 1
    assert 'move = {"cursor_x", "cursor_y"}' in text

    assert len(list(directory.glob("keybinds.lua.bak-*"))) == 1
    assert len(list(directory.glob("rules.lua.bak-*"))) == 1
    _, changed = install(binds, "/usr/bin/qtranslate-remake", kind="lua")
    assert not changed
    _, changed = install_rules(rules, kind="lua")
    assert not changed


def check_detection(directory: Path) -> None:
    base = directory / "config" / "hypr"
    base.mkdir(parents=True)
    (base / "hyprland.lua").write_text("", encoding="utf-8")
    old = os.environ.get("XDG_CONFIG_HOME")
    os.environ["XDG_CONFIG_HOME"] = str(directory / "config")
    try:
        binds, rules, kind = config_targets()
        assert kind == "lua"
        assert binds == base / "custom" / "keybinds.lua"
        assert rules == base / "custom" / "rules.lua"
    finally:
        if old is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = old


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        check_conf(directory / "conf")
        check_lua(directory / "lua")
        check_detection(directory / "detect")

    print("hyprland rules and binds: OK")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
