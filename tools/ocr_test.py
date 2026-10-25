"""Проверка распознавания текста с изображения."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter  # noqa: E402

from qtranslate_r.platform.ocr import OcrError, available_languages, recognize  # noqa: E402


def main() -> int:
    app = QGuiApplication(sys.argv)
    languages = available_languages()
    print("OCR languages:", ", ".join(languages) or "none")
    if not languages:
        print("SKIP: no OCR language is installed")
        return 0

    image = QImage(720, 160, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    painter.setPen(QColor("black"))
    painter.setFont(QFont("Arial", 30))
    painter.drawText(30, 95, "Hello world, this is OCR.")
    painter.end()

    handle, name = tempfile.mkstemp(suffix=".png")
    path = Path(name)
    try:
        image.save(str(path), "PNG")
        text, language = recognize(path, "en")
    except OcrError as exc:
        print("FAIL:", exc)
        return 1
    finally:
        try:
            path.unlink()
        except OSError:
            pass

    print("recognized:", language, "|", text)
    print("OK" if "hello" in text.lower() else "FAIL")
    return 0 if "hello" in text.lower() else 1


if __name__ == "__main__":
    raise SystemExit(main())
