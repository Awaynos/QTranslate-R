"""Проверка орфографии через Windows Spell Checking API."""

from __future__ import annotations

import atexit
import ctypes
import sys
import threading
from ctypes import POINTER, byref, c_int, c_uint, c_ulong, c_void_p, c_wchar_p

_HRESULT = ctypes.c_long
_CLSID = "{7ab36653-1796-484b-bdfa-e74f1db7c1dc}"
_IID = "{8e018a9d-2415-4677-bf08-794ea61f94bb}"
_RPC_E_CHANGED_MODE = -2147417850
_COINIT_MULTITHREADED = 0

_TAGS = {
    "en": "en-US", "ru": "ru-RU", "de": "de-DE", "fr": "fr-FR", "es": "es-ES",
    "it": "it-IT", "pt": "pt-BR", "pl": "pl-PL", "uk": "uk-UA", "tr": "tr-TR",
    "nl": "nl-NL", "sv": "sv-SE", "cs": "cs-CZ", "da": "da-DK", "fi": "fi-FI",
    "nb": "nb-NO", "no": "nb-NO", "ro": "ro-RO", "sk": "sk-SK", "sl": "sl-SI",
    "hr": "hr-HR", "hu": "hu-HU", "el": "el-GR", "bg": "bg-BG", "he": "he-IL",
    "ar": "ar-SA", "hi": "hi-IN", "id": "id-ID", "ms": "ms-MY", "vi": "vi-VN",
    "th": "th-TH", "ko": "ko-KR", "ja": "ja-JP", "zh": "zh-CN", "zh-TW": "zh-TW",
    "kk": "kk-KZ", "ka": "ka-GE",
}



class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(text: str) -> _GUID:
    value = _GUID()
    if _ole32.CLSIDFromString(c_wchar_p(text), byref(value)) < 0:
        raise OSError("bad GUID")
    return value


def _call(pointer, index: int, argtypes: list, args: list, restype=_HRESULT):
    vtable = ctypes.cast(pointer, POINTER(POINTER(c_void_p)))[0]
    function = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)(vtable[index])
    return function(pointer, *args)


def _release(pointer) -> None:
    if pointer:
        _call(pointer, 2, [], [], c_ulong)


def windows_tag(code: str) -> str:
    return _TAGS.get(code, code)


if sys.platform == "win32":
    _ole32 = ctypes.windll.ole32
    _ole32.CoCreateInstance.argtypes = [
        POINTER(_GUID), c_void_p, c_ulong, POINTER(_GUID), POINTER(c_void_p)
    ]
    _ole32.CoCreateInstance.restype = _HRESULT
else:
    _ole32 = None


class SpellChecker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._factory = c_void_p()
        self._checkers: dict[str, c_void_p] = {}
        self._cache: dict[tuple[str, str], bool] = {}
        self._owns_apartment = False
        self._started = False

    def _start(self) -> None:
        if self._started:
            return
        if _ole32 is None:
            return
        result = _ole32.CoInitializeEx(None, _COINIT_MULTITHREADED) & 0xFFFFFFFF
        self._owns_apartment = result in (0, 1)
        if not self._owns_apartment and result != (_RPC_E_CHANGED_MODE & 0xFFFFFFFF):
            return
        self._started = True

    def supported(self, code: str) -> bool:
        with self._lock:
            factory = self._factory_pointer()
            if not factory:
                return False
            tag = windows_tag(code)
            value = c_int()
            result = _call(factory, 4, [c_wchar_p, POINTER(c_int)], [tag, byref(value)])
            return result >= 0 and bool(value.value)

    def is_misspelled(self, word: str, code: str) -> bool:
        if not word:
            return False
        key = (windows_tag(code), word)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            result = bool(self._check(word, code))
            if len(self._cache) > 20000:
                self._cache.clear()
            self._cache[key] = result
            return result

    def suggestions(self, word: str, code: str, limit: int = 5) -> list[str]:
        with self._lock:
            checker = self._checker_pointer(code)
            if not checker:
                return []
            items = self._suggest(checker, word)
            return items[:limit]

    def _check(self, word: str, code: str) -> list[tuple[int, int, int, str]]:
        checker = self._checker_pointer(code)
        if not checker:
            return []
        errors = c_void_p()
        result = _call(checker, 4, [c_wchar_p, POINTER(c_void_p)], [word, byref(errors)])
        if result < 0 or not errors:
            return []

        found: list[tuple[int, int, int, str]] = []
        start = c_uint()
        length = c_uint()
        action = c_int()
        replacement = c_wchar_p()
        try:
            while True:
                error = c_void_p()
                status = _call(errors, 3, [POINTER(c_void_p)], [byref(error)])
                if status != 0 or not error:
                    break
                try:
                    _call(error, 3, [POINTER(c_uint)], [byref(start)])
                    _call(error, 4, [POINTER(c_uint)], [byref(length)])
                    _call(error, 5, [POINTER(c_int)], [byref(action)])
                    _call(error, 6, [POINTER(c_wchar_p)], [byref(replacement)])
                    text = replacement.value or ""
                    if text:
                        _ole32.CoTaskMemFree(replacement)
                    found.append((int(start.value), int(length.value), int(action.value), text))
                finally:
                    _release(error)
        finally:
            _release(errors)
        return found

    def _suggest(self, checker, word: str) -> list[str]:
        items = c_void_p()
        result = _call(checker, 5, [c_wchar_p, POINTER(c_void_p)], [word, byref(items)])
        if result < 0 or not items:
            return []

        values: list[str] = []
        try:
            while True:
                value = c_wchar_p()
                fetched = c_ulong()
                status = _call(
                    items,
                    3,
                    [c_ulong, POINTER(c_wchar_p), POINTER(c_ulong)],
                    [1, byref(value), byref(fetched)],
                )
                if value.value:
                    values.append(value.value)
                    _ole32.CoTaskMemFree(value)
                if status != 0 or fetched.value == 0:
                    break
        finally:
            _release(items)
        return values

    def _factory_pointer(self):
        if not self._started:
            self._start()
        if not self._started:
            return None
        if self._factory:
            return self._factory
        factory = c_void_p()
        result = _ole32.CoCreateInstance(
            byref(_guid(_CLSID)), None, 1, byref(_guid(_IID)), byref(factory)
        )
        if result < 0 or not factory:
            return None
        self._factory = factory
        return factory

    def _checker_pointer(self, code: str):
        tag = windows_tag(code)
        checker = self._checkers.get(tag)
        if checker:
            return checker
        factory = self._factory_pointer()
        if not factory:
            return None

        supported = c_int()
        if _call(factory, 4, [c_wchar_p, POINTER(c_int)], [tag, byref(supported)]) < 0:
            return None
        if not supported.value:
            return None

        created = c_void_p()
        if _call(factory, 5, [c_wchar_p, POINTER(c_void_p)], [tag, byref(created)]) < 0:
            return None
        if not created:
            return None
        self._checkers[tag] = created
        return created

    def close(self) -> None:
        with self._lock:
            for checker in self._checkers.values():
                _release(checker)
            self._checkers.clear()
            _release(self._factory)
            self._factory = c_void_p()
            self._cache.clear()
            if self._started and self._owns_apartment and _ole32 is not None:
                _ole32.CoUninitialize()
            self._started = False
            self._owns_apartment = False


checker = SpellChecker()
atexit.register(checker.close)
