import json
from pathlib import Path
from typing import Dict


class ThemeLoader:
    """Загружает тему из JSON."""

    @staticmethod
    def load(theme_path: Path) -> Dict:
        json_path = theme_path / "theme.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Theme file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)