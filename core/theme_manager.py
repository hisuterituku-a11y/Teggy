"""
Менеджер тем оформления Tegi.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.exceptions import ConfigError


class ThemeManager:
    """Управляет темами оформления."""

    THEMES_DIR = Path("themes")

    # Текущая тема (кэш)
    _current_theme: Dict[str, Any] = {}
    _current_name: str = "dark"

    @classmethod
    def _ensure_dir(cls) -> None:
        """Создаёт папку с темами, если её нет."""
        cls.THEMES_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def list_themes(cls) -> List[str]:
        """Возвращает список доступных тем."""
        cls._ensure_dir()
        return [f.stem for f in cls.THEMES_DIR.glob("*.json")]

    @classmethod
    def load(cls, name: str) -> Dict[str, Any]:
        """
        Загружает тему по имени.

        Args:
            name: имя темы (без расширения)

        Returns:
            словарь с данными темы

        Raises:
            ConfigError: если тема не найдена
        """
        cls._ensure_dir()
        file_path = cls.THEMES_DIR / f"{name}.json"

        if not file_path.exists():
            raise ConfigError(f"Тема '{name}' не найдена")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ConfigError(f"Ошибка загрузки темы '{name}': {e}")

    @classmethod
    def get_current(cls) -> Dict[str, Any]:
        """Возвращает текущую тему."""
        if not cls._current_theme:
            cls._current_theme = cls.load(cls._current_name)
        return cls._current_theme

    @classmethod
    def set_current(cls, name: str) -> None:
        """Устанавливает текущую тему."""
        cls._current_name = name
        cls._current_theme = cls.load(name)

    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        """Возвращает цвета текущей темы."""
        theme = cls.get_current()
        return theme.get("colors", {})

    @classmethod
    def get_mode(cls) -> str:
        """Возвращает режим темы (dark/light)."""
        theme = cls.get_current()
        return theme.get("mode", "dark")

    @classmethod
    def get_name(cls) -> str:
        """Возвращает имя текущей темы."""
        return cls._current_name