"""Единый источник версии приложения Teggy."""

from __future__ import annotations

APP_NAME = "Teggy"
__version__ = "0.1.0"
VERSION = tuple(int(part) for part in __version__.split("."))


def display_version() -> str:
    """Версия для интерфейса и диагностических сообщений."""
    return f"{APP_NAME} {__version__}"


def is_newer_version(candidate: str, current: str = __version__) -> bool:
    """Проверяет, новее ли версия candidate текущей версии приложения.

    Поддерживает стабильные версии в формате MAJOR.MINOR.PATCH. Префикс ``v``
    допускается, чтобы напрямую сравнивать теги GitHub Releases.
    """
    return _parse_version(candidate) > _parse_version(current)


def _parse_version(value: str) -> tuple[int, int, int]:
    normalized = value.strip().removeprefix("v")
    parts = normalized.split(".")

    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(
            f"Некорректная версия {value!r}: ожидается формат MAJOR.MINOR.PATCH"
        )

    return tuple(int(part) for part in parts)
