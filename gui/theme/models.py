from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class Theme:
    """Неизменяемый объект темы."""
    name: str
    path: Path
    colors: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, int] = field(default_factory=dict)
    radius: Dict[str, int] = field(default_factory=dict)
    typography: Dict[str, str | int] = field(default_factory=dict)
    animation: Dict[str, int] = field(default_factory=dict)
    icons: Dict[str, str] = field(default_factory=dict)
    patterns: Dict[str, str] = field(default_factory=dict)
    qss: str = ""

    def color(self, key: str, default: str = "#FFFFFF") -> str:
        return self.colors.get(key, default)

    def spacing(self, key: str, default: int = 8) -> int:
        return self.spacing.get(key, default)

    def radius(self, key: str, default: int = 8) -> int:
        return self.radius.get(key, default)

    def typography_value(self, key: str, default: str | int = "Inter") -> str | int:
        return self.typography.get(key, default)