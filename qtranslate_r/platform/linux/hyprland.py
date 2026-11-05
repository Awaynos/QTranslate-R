"""Установка биндов и правил Hyprland для приложения."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ...config.paths import is_frozen, project_root

BINDS_MARKER = "QTranslate Remake binds"
RULES_MARKER = "QTranslate Remake rules"
BINDS = (
    ("Q", "--quick", "Quick translate"),
    ("1", "--replace", "Replace selection"),
    ("I", "--ocr", "OCR"),
)


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
        return base / "custom" / "keybinds.lua", base / "custom" / "rules.lua", "lua"
    return conf, conf, "conf"


def default_command() -> str:
    if is_frozen():
        executable = os.environ.get("APPIMAGE") or sys.executable
        return shlex.quote(executable)
    python = shlex.quote(sys.executable)
    script = shlex.quote(str(project_root() / "run.py"))
    return f"{python} {script}"


def _lua_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _binds_block(command: str, kind: str) -> str:
    if kind == "lua":
        lines = [f"-- {BINDS_MARKER}"]
        for key, argument, description in BINDS:
            lines.append(
                f'hl.bind("CTRL + ALT + {key}", '
                f'hl.dsp.exec_cmd("{_lua_escape(command)} {argument}"), '
                f'{{ description = "QTranslate: {description}" }})'
            )
        return "\n".join(lines) + "\n"

    lines = [f"# {BINDS_MARKER}"]
    for key, argument, _ in BINDS:
        lines.append(f"bind = CTRL ALT, {key}, exec, {command} {argument}")
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


def _append(path: Path, kind: str, marker: str, block: str) -> bool:
    if not path.is_file():
        if kind != "lua":
            raise FileNotFoundError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    if marker in text:
        return False

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, backup)

    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + ("\n" if text else "") + block, encoding="utf-8", newline="\n")
    return True


def install(
    path: Path | None = None,
    command: str | None = None,
    kind: str | None = None,
) -> tuple[Path, bool]:
    if path is None:
        path, _, kind = config_targets()
    kind = kind or ("lua" if path.suffix == ".lua" else "conf")
    command = command or default_command()
    return path, _append(path, kind, BINDS_MARKER, _binds_block(command, kind))


def install_rules(path: Path | None = None, kind: str | None = None) -> tuple[Path, bool]:
    if path is None:
        _, path, kind = config_targets()
    kind = kind or ("lua" if path.suffix == ".lua" else "conf")
    return path, _append(path, kind, RULES_MARKER, _rules_block(kind))


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
