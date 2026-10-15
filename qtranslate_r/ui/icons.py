"""Иконки из SVG-набора в папке ``icons/``."""

from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ..config.paths import app_icon_file, data_dir

_directory: Path | None = None
_color = "#dfe3e7"
_size = QSize(18, 18)


def set_directory(path) -> None:
    global _directory
    _directory = Path(path) if path else None


def set_color(color: str) -> None:
    global _color
    if color:
        _color = color


def available() -> bool:
    return _directory is not None and _directory.is_dir()


def icon(names: str | tuple[str, ...], color: str | None = None) -> QIcon | None:
    """Первая найденная иконка из списка имён (удобно для разных наборов)."""
    if isinstance(names, str):
        names = (names,)
    path = _find_any(names)
    if path is None:
        return None
    try:
        data = path.read_text(encoding="utf-8")
    except OSError:
        return None

    data = data.replace("currentColor", color or _color)
    renderer = QSvgRenderer(QByteArray(data.encode("utf-8")))
    if not renderer.isValid():
        return None

    pixmap = QPixmap(_size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def icon_size() -> QSize:
    return _size


def ensure_ico() -> Path | None:
    """Собрать .ico из app.png — нужен Windows для значка окна и панели задач."""
    png = app_icon_file()
    if not png.is_file():
        return None
    target = data_dir() / "app.ico"
    try:
        if target.is_file() and target.stat().st_mtime >= png.stat().st_mtime:
            return target

        image = QImage(str(png)).convertToFormat(QImage.Format.Format_ARGB32)
        if image.isNull():
            return None
        image = image.scaled(
            256,
            256,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        data = bytes(buffer.data())
        if not data:
            return None

        # ICO с PNG внутри: заголовок + одна запись + сами данные.
        header = struct.pack("<HHH", 0, 1, 1)
        entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(data), 22)
        target.write_bytes(header + entry + data)
        return target
    except (OSError, ValueError):
        return None


def _find_any(names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = _find(name)
        if path is not None:
            return path
    return None


def _find(name: str) -> Path | None:
    if _directory is None or not _directory.is_dir():
        return None
    for path in _directory.glob(f"*/{name}.svg"):
        return path
    direct = _directory / f"{name}.svg"
    return direct if direct.is_file() else None
