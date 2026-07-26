"""Проверка доступных обновлений Teggy через GitHub Releases."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.version import __version__, is_newer_version

LATEST_RELEASE_URL = (
    "https://api.github.com/repos/hisuterituku-a11y/Teggy/releases/latest"
)
DEFAULT_TIMEOUT_SECONDS = 5.0


class UpdateCheckError(RuntimeError):
    """Ошибка получения или разбора информации о релизе."""


@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    version: str
    name: str
    page_url: str
    notes: str
    is_prerelease: bool

    @property
    def is_update_available(self) -> bool:
        return is_newer_version(self.version, __version__)


def check_for_updates(
    *,
    opener: Callable = urlopen,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> ReleaseInfo:
    """Возвращает данные последнего опубликованного GitHub-релиза.

    ``opener`` передаётся отдельно, чтобы сетевую часть можно было тестировать без
    реальных запросов и без жертвоприношений интернет-соединению.
    """
    request = Request(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"Teggy/{__version__}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise UpdateCheckError("Не удалось связаться с GitHub Releases") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpdateCheckError("GitHub вернул некорректный ответ") from error

    return _parse_release(payload)


def _parse_release(payload: object) -> ReleaseInfo:
    if not isinstance(payload, dict):
        raise UpdateCheckError("Некорректный формат ответа GitHub")

    tag_name = payload.get("tag_name")
    page_url = payload.get("html_url")

    if not isinstance(tag_name, str) or not tag_name.strip():
        raise UpdateCheckError("В релизе отсутствует tag_name")
    if not isinstance(page_url, str) or not page_url.startswith("https://"):
        raise UpdateCheckError("В релизе отсутствует безопасная ссылка")

    version = tag_name.strip().removeprefix("v")

    try:
        is_newer_version(version, __version__)
    except ValueError as error:
        raise UpdateCheckError("Тег релиза не соответствует формату версии") from error

    name = payload.get("name")
    notes = payload.get("body")

    return ReleaseInfo(
        version=version,
        name=name.strip() if isinstance(name, str) and name.strip() else tag_name,
        page_url=page_url,
        notes=notes.strip() if isinstance(notes, str) else "",
        is_prerelease=bool(payload.get("prerelease", False)),
    )
