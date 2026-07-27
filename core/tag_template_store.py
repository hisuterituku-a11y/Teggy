from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QSettings


class TagTemplateStore:
    """Единое хранилище шаблонов метаданных для всех разделов Teggy."""

    SETTINGS_KEY = "tagging/templates_v2"
    LEGACY_KEY = "tagging/templates"
    FIELD_KEYS = ("title", "subject", "comment", "artist", "copyright", "keywords")

    def __init__(self) -> None:
        self._settings = QSettings("Teggy", "Teggy")

    def load(self) -> dict[str, dict[str, str]]:
        raw = self._settings.value(self.SETTINGS_KEY)
        if raw is None:
            raw = self._settings.value(self.LEGACY_KEY, "{}")
        try:
            data: Any = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        result: dict[str, dict[str, str]] = {}
        for name, values in data.items():
            if not isinstance(values, dict):
                continue
            result[str(name)] = {
                key: str(values.get(key, ""))
                for key in self.FIELD_KEYS
            }
        return result

    def save_all(self, templates: dict[str, dict[str, str]]) -> None:
        normalized = {
            str(name): {key: str(values.get(key, "")) for key in self.FIELD_KEYS}
            for name, values in templates.items()
        }
        self._settings.setValue(
            self.SETTINGS_KEY,
            json.dumps(normalized, ensure_ascii=False),
        )

    def names(self) -> list[str]:
        return sorted(self.load(), key=str.casefold)

    def get(self, name: str) -> dict[str, str] | None:
        values = self.load().get(name)
        return dict(values) if values is not None else None
