"""Распознавание текста средствами Windows (Windows.Media.Ocr)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..config.paths import resource
from ..localization import tr

_SCRIPT = "qtranslate_r/platform/ocr.ps1"
_TIMEOUT = 60
_CREATE_NO_WINDOW = 0x08000000

_TAGS = {
    "ar": "ar-SA", "bg": "bg-BG", "cs": "cs-CZ", "da": "da-DK", "de": "de-DE",
    "el": "el-GR", "en": "en-US", "es": "es-ES", "et": "et-EE", "fi": "fi-FI",
    "fr": "fr-FR", "he": "he-IL", "hi": "hi-IN", "hr": "hr-HR", "hu": "hu-HU",
    "id": "id-ID", "it": "it-IT", "ja": "ja-JP", "ka": "ka-GE", "kk": "kk-KZ",
    "ko": "ko-KR", "lt": "lt-LT", "lv": "lv-LV", "ms": "ms-MY", "nb": "nb-NO",
    "nl": "nl-NL", "no": "nb-NO", "pl": "pl-PL", "pt": "pt-BR", "ro": "ro-RO",
    "ru": "ru-RU", "sk": "sk-SK", "sl": "sl-SI", "sr": "sr-Latn-RS", "sv": "sv-SE",
    "th": "th-TH", "tr": "tr-TR", "uk": "uk-UA", "vi": "vi-VN", "zh": "zh-Hans-CN",
    "zh-TW": "zh-Hant-TW",
}

_available: list[str] | None = None


class OcrError(Exception):
    def __init__(self, message: str, *, kind: str = "error") -> None:
        super().__init__(message)
        self.kind = kind


def language_tag(code: str) -> str:
    return _TAGS.get(code, code)


def available_languages() -> list[str]:
    global _available
    if _available is None:
        data = _run(["-ListLanguages"])
        languages = data.get("languages")
        _available = [str(item) for item in languages] if isinstance(languages, list) else []
    return _available


def pick_language(preferred: str = "") -> str:
    languages = available_languages()
    if not languages:
        raise OcrError(tr("ocr.no_language"), kind="language")

    candidates = []
    if preferred:
        candidates.append(language_tag(preferred))
    candidates.append("en-US")

    lowered = {item.lower(): item for item in languages}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
        base = candidate.split("-")[0].lower()
        if base in lowered:
            return lowered[base]
    return languages[0]


def recognize(image_path: Path | str, preferred: str = "") -> tuple[str, str]:
    tag = pick_language(preferred)
    data = _run(["-ImagePath", str(image_path), "-Language", tag])
    if not data.get("ok"):
        error = str(data.get("error", ""))
        if error == "unsupported_language":
            raise OcrError(tr("ocr.no_language"), kind="language")
        raise OcrError(tr("ocr.failed", message=error or tr("errors.internal", message="")), kind="error")

    text = data.get("text")
    if not isinstance(text, str):
        raise OcrError(tr("errors.bad_response"), kind="error")
    language = data.get("language")
    return text, language if isinstance(language, str) else tag


def _run(extra: list[str]) -> dict:
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if not executable:
        raise OcrError(tr("ocr.unavailable"), kind="unavailable")

    script = resource(_SCRIPT)
    if not script.is_file():
        raise OcrError(tr("ocr.unavailable"), kind="unavailable")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
        output = Path(handle.name)

    try:
        command = [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script),
            *extra,
            "-OutputPath", str(output),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=_TIMEOUT,
                creationflags=_CREATE_NO_WINDOW,
            )
        except subprocess.TimeoutExpired as exc:
            raise OcrError(tr("errors.timeout"), kind="network") from exc
        except OSError as exc:
            raise OcrError(tr("ocr.unavailable"), kind="unavailable") from exc

        if result.returncode != 0 or not output.is_file():
            message = result.stderr.decode("utf-8", "replace").strip()
            raise OcrError(tr("ocr.failed", message=message or tr("ocr.unavailable")), kind="error")

        try:
            data = json.loads(output.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise OcrError(tr("errors.bad_response"), kind="error") from exc
        if not isinstance(data, dict):
            raise OcrError(tr("errors.bad_response"), kind="error")
        return data
    finally:
        try:
            output.unlink()
        except OSError:
            pass
