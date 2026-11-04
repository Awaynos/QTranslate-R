"""Проверка платформенных хоткеев по умолчанию."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.hotkeys import ACTIONS, binding, defaults  # noqa: E402
from qtranslate_r.platform.hotkey_defaults import defaults as platform_defaults  # noqa: E402


class FakeSettings:
    hotkeys: dict = {}


def main() -> int:
    values = defaults()
    assert set(values) == {action.id for action in ACTIONS}
    assert values == {
        **{action.id: action.default for action in ACTIONS},
        **platform_defaults(),
    }

    if sys.platform.startswith("linux"):
        assert values["quick_translate"] == "Ctrl+Alt+Q"
        assert values["replace_selection"] == "Ctrl+Alt+1"
        assert values["ocr"] == "Ctrl+Alt+I"

    settings = FakeSettings()
    settings.hotkeys = {"quick_translate": "Ctrl+Shift+F9"}
    assert binding(settings, "quick_translate") == "Ctrl+Shift+F9"
    assert binding(FakeSettings(), "replace_selection") == values["replace_selection"]

    global_keys = [values[action.id] for action in ACTIONS if action.scope == "global"]
    assert len(set(global_keys)) == len(global_keys)

    print("platform:", sys.platform)
    for action_id in ("quick_translate", "replace_selection", "ocr"):
        print(f"  {action_id}: {values[action_id]}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
