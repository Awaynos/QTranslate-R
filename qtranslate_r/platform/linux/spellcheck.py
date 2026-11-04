"""Проверка орфографии через enchant."""

from __future__ import annotations

import atexit
import threading

try:
    import enchant
except Exception:
    enchant = None

_TAGS = {
    "ar": "ar_SA",
    "be": "be_BY",
    "bg": "bg_BG",
    "cs": "cs_CZ",
    "da": "da_DK",
    "de": "de_DE",
    "el": "el_GR",
    "en": "en_US",
    "es": "es_ES",
    "fi": "fi_FI",
    "fr": "fr_FR",
    "he": "he_IL",
    "hi": "hi_IN",
    "hr": "hr_HR",
    "hu": "hu_HU",
    "id": "id_ID",
    "it": "it_IT",
    "ja": "ja_JP",
    "ka": "ka_GE",
    "kk": "kk_KZ",
    "ko": "ko_KR",
    "ms": "ms_MY",
    "nb": "nb_NO",
    "nl": "nl_NL",
    "no": "nb_NO",
    "pl": "pl_PL",
    "pt": "pt_BR",
    "pt-BR": "pt_BR",
    "ro": "ro_RO",
    "ru": "ru_RU",
    "sk": "sk_SK",
    "sl": "sl_SI",
    "sr": "sr_RS",
    "sv": "sv_SE",
    "th": "th_TH",
    "tr": "tr_TR",
    "uk": "uk_UA",
    "vi": "vi_VN",
    "zh": "zh_CN",
    "zh-TW": "zh_TW",
}


def language_tag(code: str) -> str:
    return _TAGS.get(code, _TAGS.get(code.lower(), code))


def available() -> bool:
    return enchant is not None


class SpellChecker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._dicts: dict[str, object | None] = {}
        self._cache: dict[tuple[str, str], bool] = {}

    def _dictionary(self, code: str):
        if enchant is None:
            return None
        tag = language_tag(code)
        with self._lock:
            if tag in self._dicts:
                return self._dicts[tag]

            candidates = [tag, tag.split("_")[0]]
            if code == "en":
                candidates.append("en_GB")

            dictionary = None
            for candidate in candidates:
                try:
                    dictionary = enchant.Dict(candidate)
                except Exception:
                    continue
                break
            self._dicts[tag] = dictionary
            return dictionary

    def supported(self, code: str) -> bool:
        return self._dictionary(code) is not None

    def is_misspelled(self, word: str, code: str) -> bool:
        if not word:
            return False
        dictionary = self._dictionary(code)
        if dictionary is None:
            return False

        key = (language_tag(code), word)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            try:
                result = not dictionary.check(word)
            except Exception:
                result = False
            if len(self._cache) > 20000:
                self._cache.clear()
            self._cache[key] = result
            return result

    def suggestions(self, word: str, code: str, limit: int = 5) -> list[str]:
        dictionary = self._dictionary(code)
        if dictionary is None:
            return []
        try:
            return list(dictionary.suggest(word))[:limit]
        except Exception:
            return []

    def close(self) -> None:
        with self._lock:
            self._dicts.clear()
            self._cache.clear()


checker = SpellChecker()
atexit.register(checker.close)
