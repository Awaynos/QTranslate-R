"""QTranslate Remake — настольный переводчик на PySide6.

Версия читается из файла VERSION рядом с программой — его можно править
обычным блокнотом, без пересборки.
"""

import sys
from pathlib import Path

_DEFAULT_VERSION = "0.1.0 Alpha"


def _version_roots() -> list[Path]:
    if getattr(sys, "frozen", False):
        roots = [Path(sys.executable).resolve().parent]
        bundled = getattr(sys, "_MEIPASS", None)
        if bundled:
            roots.append(Path(bundled))
        return roots
    return [Path(__file__).resolve().parents[1]]


def _read_version() -> str:
    for root in _version_roots():
        try:
            text = (root / "VERSION").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            return text
    return _DEFAULT_VERSION


__version__ = _read_version()
__app_name__ = "QTranslate Remake"
