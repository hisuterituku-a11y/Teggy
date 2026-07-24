from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class Theme:
    """Неизменяемый объект темы."""
    name: str
    path: Path
    colors: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, int] = field(default_factory=dict)
    radius: Dict[str, int] = field(default_factory=dict)
    typography: Dict[str, "str | int"] = field(default_factory=dict)
    animation: Dict[str, int] = field(default_factory=dict)
    icons: Dict[str, str] = field(default_factory=dict)
    patterns: Dict[str, str] = field(default_factory=dict)
    qss: str = ""

    # ИСПРАВЛЕНО: методы-аксессоры раньше назывались так же, как поля
    # (spacing, radius). Класс выполняется сверху вниз: сначала
    # объявляются поля через field(default_factory=dict), а методы с
    # такими же именами ниже по коду перезаписывают их в пространстве
    # имён класса. @dataclass обрабатывает класс уже после выполнения
    # всего тела класса, поэтому видит вместо field(...) саму функцию
    # метода — она становится "значением по умолчанию" для поля.
    # Итог: без явной передачи spacing/radius в конструктор их значением
    # оказывается сама функция, а не {}; если передать словарь явно —
    # ломается вызов метода, потому что self.spacing — это уже не метод,
    # а переданный словарь. Переименование убирает коллизию полностью.
    def color(self, key: str, default: str = "#FFFFFF") -> str:
        return self.colors.get(key, default)

    def spacing_value(self, key: str, default: int = 8) -> int:
        return self.spacing.get(key, default)

    def radius_value(self, key: str, default: int = 8) -> int:
        return self.radius.get(key, default)

    def typography_value(self, key: str, default: "str | int" = "Inter") -> "str | int":
        return self.typography.get(key, default)