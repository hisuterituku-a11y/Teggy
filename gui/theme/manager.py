from pathlib import Path
from typing import Dict, List

from gui.theme.compiler import QSSCompiler
from gui.theme.loader import ThemeLoader
from gui.theme.models import Theme
from gui.theme.validator import ThemeValidator


class ThemeManager:
    """Управляет темами. Загружает, валидирует, компилирует и кэширует."""

    def __init__(self, themes_dir: Path):
        self.themes_dir = themes_dir
        self._cache: Dict[str, Theme] = {}

    def load(self, name: str) -> Theme:
        """Загружает тему с кэшированием."""
        if name in self._cache:
            return self._cache[name]

        theme_path = self.themes_dir / name
        data = ThemeLoader.load(theme_path)
        ThemeValidator.validate(data)
        qss = QSSCompiler.compile(theme_path, data)

        theme = Theme(
            name=name,
            path=theme_path,
            colors=data.get("colors", {}),
            spacing=data.get("spacing", {}),
            radius=data.get("radius", {}),
            typography=data.get("typography", {}),
            animation=data.get("animation", {}),
            icons=data.get("icons", {}),
            patterns=data.get("patterns", {}),
            qss=qss,
        )
        self._cache[name] = theme
        return theme

    def clear_cache(self) -> None:
        self._cache.clear()

    def list_themes(self) -> List[str]:
        """Возвращает список доступных тем."""
        if not self.themes_dir.exists():
            return []
        return [
            directory.name
            for directory in self.themes_dir.iterdir()
            if directory.is_dir() and (directory / "theme.json").exists()
        ]
