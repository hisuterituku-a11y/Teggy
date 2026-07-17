from pathlib import Path
from typing import Dict, Optional
from gui.theme.models import Theme
from gui.theme.loader import ThemeLoader
from gui.theme.validator import ThemeValidator, ThemeValidationError
from gui.theme.compiler import QSSCompiler


class ThemeManager:
    """Управляет темами. Загружает, валидирует, компилирует и кэширует."""

    def __init__(self, themes_dir: Path):
        self.themes_dir = themes_dir
        self._cache: Dict[str, Theme] = {}

    def load(self, name: str) -> Theme:
        """Загружает тему (с кэшированием)."""
        if name in self._cache:
            return self._cache[name]

        theme_path = self.themes_dir / name

        # 1. Загружаем JSON
        data = ThemeLoader.load(theme_path)

        # 2. Валидируем
        ThemeValidator.validate(data)

        # 3. Компилируем QSS
        qss = QSSCompiler.compile(theme_path, data)

        # 4. Создаём Theme
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
            qss=qss
        )

        self._cache[name] = theme
        return theme