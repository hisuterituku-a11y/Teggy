"""
Менеджер шаблонов Tegi.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.exceptions import TemplateError


class TemplateManager:
    """Управляет шаблонами метаданных."""

    TEMPLATES_DIR = Path("templates")

    @classmethod
    def _ensure_dir(cls) -> None:
        """Создаёт папку для шаблонов, если её нет."""
        cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def list_templates(cls) -> List[str]:
        """Возвращает список доступных шаблонов."""
        cls._ensure_dir()
        return [f.stem for f in cls.TEMPLATES_DIR.glob("*.json")]

    @classmethod
    def load(cls, name: str) -> Dict[str, Any]:
        """
        Загружает шаблон по имени.

        Args:
            name: имя шаблона (без расширения)

        Returns:
            словарь с данными шаблона

        Raises:
            TemplateError: если шаблон не найден
        """
        cls._ensure_dir()
        file_path = cls.TEMPLATES_DIR / f"{name}.json"

        if not file_path.exists():
            raise TemplateError(f"Шаблон '{name}' не найден")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise TemplateError(f"Ошибка загрузки шаблона '{name}': {e}")

    @classmethod
    def save(cls, name: str, data: Dict[str, Any]) -> None:
        """
        Сохраняет шаблон.

        Args:
            name: имя шаблона
            data: словарь с данными

        Raises:
            TemplateError: если не удалось сохранить
        """
        cls._ensure_dir()
        file_path = cls.TEMPLATES_DIR / f"{name}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise TemplateError(f"Ошибка сохранения шаблона '{name}': {e}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Удаляет шаблон."""
        cls._ensure_dir()
        file_path = cls.TEMPLATES_DIR / f"{name}.json"

        if not file_path.exists():
            raise TemplateError(f"Шаблон '{name}' не найден")

        try:
            file_path.unlink()
        except Exception as e:
            raise TemplateError(f"Ошибка удаления шаблона '{name}': {e}")

    @classmethod
    def export(cls, name: str, file_path: Path) -> None:
        """Экспортирует шаблон в указанный файл."""
        data = cls.load(name)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise TemplateError(f"Ошибка экспорта шаблона '{name}': {e}")

    @classmethod
    def import_from_file(cls, file_path: Path) -> str:
        """Импортирует шаблон из файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            name = data.get("name") or file_path.stem
            cls.save(name, data)
            return name

        except Exception as e:
            raise TemplateError(f"Ошибка импорта шаблона: {e}")