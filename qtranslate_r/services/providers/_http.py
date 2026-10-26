"""HTTP-обёртки с общей обработкой ошибок."""

from __future__ import annotations

import requests

from ...domain.errors import ServiceError
from ...localization import tr

DEFAULT_TIMEOUT = 15
USER_AGENT = "QTranslateR/0.0.1"


def http_get(url: str, params: dict, *, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
    except requests.Timeout as exc:
        raise ServiceError(tr("errors.timeout"), kind="network") from exc
    except requests.RequestException as exc:
        raise ServiceError(tr("errors.network"), kind="network") from exc
    _raise_for_status(response)
    return response


def http_post(url: str, json_body: dict, *, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    try:
        response = requests.post(
            url,
            json=json_body,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
    except requests.Timeout as exc:
        raise ServiceError(tr("errors.timeout"), kind="network") from exc
    except requests.RequestException as exc:
        raise ServiceError(tr("errors.network"), kind="network") from exc
    _raise_for_status(response)
    return response


def http_post_form(
    url: str,
    data: dict,
    *,
    params: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response:
    """POST с телом формы (application/x-www-form-urlencoded)."""
    try:
        response = requests.post(
            url,
            params=params,
            data=data,
            timeout=timeout,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    except requests.Timeout as exc:
        raise ServiceError(tr("errors.timeout"), kind="network") from exc
    except requests.RequestException as exc:
        raise ServiceError(tr("errors.network"), kind="network") from exc
    _raise_for_status(response)
    return response


def http_get_bytes(
    url: str,
    params: dict,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    headers: dict | None = None,
) -> bytes:
    """GET, возвращающий тело ответа как байты (для аудио и подобного)."""
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers=request_headers,
        )
    except requests.Timeout as exc:
        raise ServiceError(tr("errors.timeout"), kind="network") from exc
    except requests.RequestException as exc:
        raise ServiceError(tr("errors.network"), kind="network") from exc
    _raise_for_status(response)
    return response.content


def _raise_for_status(response: requests.Response) -> None:
    status = response.status_code
    if status == 429:
        raise ServiceError(tr("errors.rate_limit"), kind="limit")
    if status in (401, 403):
        raise ServiceError(tr("errors.auth"), kind="auth")
    if status >= 500:
        raise ServiceError(tr("errors.unavailable", status=status), kind="network")
    if status >= 400:
        raise ServiceError(tr("errors.rejected", status=status), kind="error")
