"""Установка биндов и правил Hyprland для приложения."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt

from ...config.paths import is_frozen, project_root, settings_file
from ...config.settings import Settings
from ...hotkeys import binding, combination, scope

BINDS_MARKER = "QTranslate Remake binds"
RULES_MARKER = "QTranslate Remake rules"
BINDS = (
    ("CTRL + ALT + Q", "--quick", "Quick translate"),
    ("CTRL + ALT + 1", "--replace", "Replace selection"),
    ("CTRL + ALT + I", "--ocr", "OCR"),
)
_CLI_ACTIONS = {
    "quick_translate": ("--quick", "Quick translate"),
    "replace_selection": ("--replace", "Replace selection"),
    "ocr": ("--ocr", "OCR"),
}
_KEY_NAMES = {
    Qt.Key.Key_Return: "Return",
    Qt.Key.Key_Enter: "Return",
    Qt.Key.Key_Escape: "Escape",
    Qt.Key.Key_Tab: "Tab",
    Qt.Key.Key_Backspace: "BackSpace",
    Qt.Key.Key_Delete: "Delete",
    Qt.Key.Key_Insert: "Insert",
    Qt.Key.Key_Home: "Home",
    Qt.Key.Key_End: "End",
    Qt.Key.Key_PageUp: "Prior",
    Qt.Key.Key_PageDown: "Next",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_Space: "Space",
    Qt.Key.Key_Comma: "comma",
    Qt.Key.Key_Period: "period",
    Qt.Key.Key_Slash: "slash",
    Qt.Key.Key_Backslash: "backslash",
    Qt.Key.Key_Minus: "minus",
    Qt.Key.Key_Equal: "equal",
    Qt.Key.Key_Semicolon: "semicolon",
    Qt.Key.Key_Apostrophe: "apostrophe",
    Qt.Key.Key_BracketLeft: "bracketleft",
    Qt.Key.Key_BracketRight: "bracketright",
    Qt.Key.Key_QuoteLeft: "grave",
}
for _index in range(1, 13):
    _KEY_NAMES[getattr(Qt.Key, f"Key_F{_index}")] = f"F{_index}"


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base and Path(base).is_absolute():
        return Path(base) / "hypr"
    return Path.home() / ".config" / "hypr"


def config_targets() -> tuple[Path, Path, str]:
    base = config_dir()
    conf = base / "hyprland.conf"
    if conf.is_file():
        return conf, conf, "conf"
    lua = base / "hyprland.lua"
    if lua.is_file():
        custom = base / "custom"
        if custom.is_dir():
            return custom / "keybinds.lua", custom / "rules.lua", "lua"
        user = base / "user.lua"
        if user.is_file():
            return user, user, "lua"
        return custom / "keybinds.lua", custom / "rules.lua", "lua"
    return conf, conf, "conf"


def default_command() -> str:
    if is_frozen():
        executable = os.environ.get("APPIMAGE") or sys.executable
        return shlex.quote(executable)
    python = shlex.quote(sys.executable)
    script = shlex.quote(str(project_root() / "run.py"))
    return f"{python} {script}"


def _key_name(key: int) -> str | None:
    if 0x41 <= key <= 0x5A:
        return chr(key).upper()
    if 0x30 <= key <= 0x39:
        return chr(key)
    return _KEY_NAMES.get(key)


def _trigger(sequence: str) -> str | None:
    parsed = combination(sequence)
    if parsed is None:
        return None
    key, ctrl, shift, alt, win = parsed
    name = _key_name(int(key))
    if name is None:
        return None
    parts = []
    if ctrl:
        parts.append("CTRL")
    if shift:
        parts.append("SHIFT")
    if alt:
        parts.append("ALT")
    if win:
        parts.append("SUPER")
    parts.append(name)
    return " + ".join(parts)


def bindings_from_settings() -> list[tuple[str, str, str]]:
    settings = Settings.load(settings_file())
    entries = []
    for action_id, (argument, description) in _CLI_ACTIONS.items():
        if scope(settings, action_id) != "global":
            continue
        trigger = _trigger(binding(settings, action_id))
        if trigger:
            entries.append((trigger, argument, description))
    return entries


def _lua_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _binds_block(command: str, kind: str, entries) -> str:
    if kind == "lua":
        lines = [f"-- {BINDS_MARKER}"]
        for trigger, argument, description in entries:
            lines.append(
                f'hl.bind("{trigger}", '
                f'hl.dsp.exec_cmd("{_lua_escape(command)} {argument}"), '
                f'{{ description = "QTranslate: {description}" }})'
            )
        return "\n".join(lines) + "\n"

    lines = [f"# {BINDS_MARKER}"]
    for trigger, argument, _ in entries:
        lines.append(f"bind = {trigger}, exec, {command} {argument}")
    return "\n".join(lines) + "\n"


def _rules_block(kind: str) -> str:
    if kind == "lua":
        return (
            f"-- {RULES_MARKER}\n"
            'hl.window_rule({match = {title = "^QTranslate Popup$"}, '
            'float = true, move = {"cursor_x", "cursor_y"}})\n'
            'hl.window_rule({match = {title = "^QTranslate Loading$"}, '
            'float = true, move = {"cursor_x", "cursor_y"}})\n'
        )

    return (
        f"# {RULES_MARKER}\n"
        "windowrulev2 = float,title:^QTranslate Popup$\n"
        "windowrulev2 = move cursor_x cursor_y,title:^QTranslate Popup$\n"
        "windowrulev2 = float,title:^QTranslate Loading$\n"
        "windowrulev2 = move cursor_x cursor_y,title:^QTranslate Loading$\n"
    )


def _binds_present(text: str) -> bool:
    return "hl.bind" in text and any(argument in text for _, argument, _ in BINDS)


def _replace_block(path: Path, kind: str, marker: str, block: str, prefixes) -> bool:
    if not path.is_file():
        if kind != "lua":
            raise FileNotFoundError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    start = None
    for index, line in enumerate(lines):
        if marker in line:
            start = index
            break

    if start is None:
        if text and not text.endswith("\n"):
            text += "\n"
        new_text = text + ("\n" if text else "") + block
    else:
        end = start + 1
        while end < len(lines):
            stripped = lines[end].strip()
            if stripped and any(stripped.startswith(prefix) for prefix in prefixes):
                end += 1
                continue
            break
        new_text = "".join(lines[:start]) + block + "".join(lines[end:])

    if new_text == text:
        return False

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, backup)
    path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def install(
    path: Path | None = None,
    command: str | None = None,
    kind: str | None = None,
    entries=None,
) -> tuple[Path, bool]:
    if path is None:
        path, _, kind = config_targets()
    kind = kind or ("lua" if path.suffix == ".lua" else "conf")
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        if BINDS_MARKER not in text and _binds_present(text):
            return path, False
    if entries is None:
        entries = bindings_from_settings()
    command = command or default_command()
    prefixes = ("hl.bind(", "bind = ") if kind == "lua" else ("bind = ",)
    return path, _replace_block(
        path,
        kind,
        BINDS_MARKER,
        _binds_block(command, kind, entries),
        prefixes,
    )


def install_rules(path: Path | None = None, kind: str | None = None) -> tuple[Path, bool]:
    if path is None:
        _, path, kind = config_targets()
    kind = kind or ("lua" if path.suffix == ".lua" else "conf")
    prefixes = ("hl.window_rule(",) if kind == "lua" else ("windowrulev2",)
    return path, _replace_block(
        path,
        kind,
        RULES_MARKER,
        _rules_block(kind),
        prefixes,
    )


def reload_hyprland() -> bool:
    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return False
    executable = shutil.which("hyprctl")
    if not executable:
        return False
    try:
        result = subprocess.run(
            [executable, "reload"],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0
