"""Единый источник версии приложения Teggy."""

from __future__ import annotations

import re

APP_NAME = "Teggy"
__version__ = "2.1.0-dev"
VERSION = (2, 1, 0)

_VERSION_PATTERN = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?$"
)


def display_version() -> str:
    """Версия для интерфейса и диагностических сообщений."""
    return f"{APP_NAME} {__version__}"


def is_newer_version(candidate: str, current: str = __version__) -> bool:
    """Проверяет, новее ли версия candidate текущей версии приложения.

    Поддерживает версии ``MAJOR.MINOR.PATCH`` и предварительные версии вроде
    ``2.1.0-dev``. Префикс ``v`` допускается для тегов GitHub Releases.
    """
    return _parse_version(candidate) > _parse_version(current)


def _parse_version(value: str) -> tuple[int, int, int, int, str]:
    match = _VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            f"Некорректная версия {value!r}: ожидается формат MAJOR.MINOR.PATCH"
        )

    prerelease = match.group("prerelease") or ""
    is_stable = 1 if not prerelease else 0

    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        is_stable,
        prerelease,
    )
