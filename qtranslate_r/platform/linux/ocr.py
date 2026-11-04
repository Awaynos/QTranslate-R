"""Распознавание текста через tesseract."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ...localization import tr
from ..base import OcrError

_TIMEOUT = 60

_TAGS = {
    "ar": "ara",
    "be": "bel",
    "bg": "bul",
    "cs": "ces",
    "da": "dan",
    "de": "deu",
    "el": "ell",
    "en": "eng",
    "es": "spa",
    "et": "est",
    "fi": "fin",
    "fr": "fra",
    "he": "heb",
    "hi": "hin",
    "hr": "hrv",
    "hu": "hun",
    "id": "ind",
    "it": "ita",
    "ja": "jpn",
    "ka": "kat",
    "kk": "kaz",
    "ko": "kor",
    "lt": "lit",
    "lv": "lav",
    "ms": "msa",
    "nl": "nld",
    "no": "nor",
    "pl": "pol",
    "pt": "por",
    "pt-BR": "por",
    "ro": "ron",
    "ru": "rus",
    "sk": "slk",
    "sl": "slv",
    "sr": "srp",
    "sv": "swe",
    "th": "tha",
    "tr": "tur",
    "uk": "ukr",
    "vi": "vie",
    "zh": "chi_sim",
    "zh-TW": "chi_tra",
}

_available: list[str] | None = None


def language_tag(code: str) -> str:
    return _TAGS.get(code, _TAGS.get(code.lower(), code))


def available_languages() -> list[str]:
    global _available
    if _available is None:
        executable = shutil.which("tesseract")
        if not executable:
            _available = []
        else:
            try:
                result = subprocess.run(
                    [executable, "--list-langs"],
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                _available = []
            else:
                lines = result.stdout.decode("utf-8", "replace").splitlines()
                _available = [
                    line.strip()
                    for line in lines
                    if line.strip() and " " not in line.strip() and line.strip() != "osd"
                ]
    return _available


def pick_language(preferred: str = "") -> str:
    languages = available_languages()
    if not languages:
        raise OcrError(tr("ocr.no_language"), kind="language")

    candidates = []
    if preferred:
        candidates.append(language_tag(preferred))
    candidates.append("eng")

    lowered = {item.lower(): item for item in languages}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return languages[0]


def recognize(image_path: Path | str, preferred: str = "") -> tuple[str, str]:
    executable = shutil.which("tesseract")
    if not executable:
        raise OcrError(tr("ocr.unavailable"), kind="unavailable")

    path = Path(image_path)
    if not path.is_file():
        raise OcrError(tr("errors.file_not_found"), kind="error")

    tag = pick_language(preferred)
    try:
        result = subprocess.run(
            [executable, str(path), "stdout", "-l", tag],
            capture_output=True,
            timeout=_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise OcrError(tr("errors.timeout"), kind="network") from exc
    except OSError as exc:
        raise OcrError(tr("ocr.unavailable"), kind="unavailable") from exc

    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise OcrError(tr("ocr.failed", message=message or tr("ocr.unavailable")), kind="error")

    return result.stdout.decode("utf-8", "replace"), tag
