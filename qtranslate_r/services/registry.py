"""Реестр сервисов."""

from __future__ import annotations

from .base import Service, ServiceRole


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[str, Service] = {}

    def register(self, service: Service) -> None:
        if not service.id:
            raise ValueError("У сервиса не задан id")
        self._services[service.id] = service

    def get(self, service_id: str) -> Service | None:
        return self._services.get(service_id)

    def all(self) -> list[Service]:
        return list(self._services.values())

    def by_role(self, role: ServiceRole) -> list[Service]:
        return [s for s in self._services.values() if s.role == role]

    def translators(self) -> list[Service]:
        return self.by_role(ServiceRole.TRANSLATOR)
