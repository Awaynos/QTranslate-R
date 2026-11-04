"""Проверка единственного экземпляра и команд между процессами."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication  # noqa: E402

from qtranslate_r.single_instance import SingleInstance  # noqa: E402


def wait_for(app: QCoreApplication, values: list[str], expected: list[str]) -> bool:
    deadline = time.time() + 3
    while time.time() < deadline:
        app.processEvents()
        if values == expected:
            return True
        time.sleep(0.01)
    return False


def main() -> int:
    app = QCoreApplication(sys.argv)
    with tempfile.TemporaryDirectory() as tmp:
        name = str(Path(tmp) / "instance.sock")
        first = SingleInstance(name)
        assert first.start()

        received: list[str] = []
        first.commandReceived.connect(received.append)

        second = SingleInstance(name)
        assert not second.start("quick")
        assert wait_for(app, received, ["quick"])

        assert second.send("ocr")
        assert wait_for(app, received, ["quick", "ocr"])

        first.stop()
        third = SingleInstance(name)
        assert third.start()
        third.stop()

    print("single instance: OK")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
