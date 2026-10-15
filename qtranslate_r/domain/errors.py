"""Ошибки сервисов."""

from __future__ import annotations


class ServiceError(Exception):
    """Ошибка одного сервиса. kind: network / auth / config / limit / unsupported / error."""

    def __init__(self, message: str, *, kind: str = "error") -> None:
        super().__init__(message)
        self.kind = kind
