"""Сервисы: интерфейсы, реестр и реализации."""

from .base import Service, ServiceRole, Translator
from .registry import ServiceRegistry

__all__ = ["Service", "ServiceRole", "Translator", "ServiceRegistry"]
