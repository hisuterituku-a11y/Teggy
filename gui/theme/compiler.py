import re
from typing import Dict
from pathlib import Path


class QSSCompiler:
    """Компилирует QSS, заменяя @переменные."""

    @classmethod
    def compile(cls, theme_path: Path, theme_data: Dict) -> str:
        qss_path = theme_path / "style.qss"
        if not qss_path.exists():
            return ""

        with open(qss_path, "r", encoding="utf-8") as f:
            qss_raw = f.read()

        # Собираем все переменные в один словарь
        variables = cls._flatten_variables(theme_data)

        # Заменяем @variable на значение (рекурсивно, до 10 проходов)
        qss = qss_raw
        for _ in range(10):
            qss, changed = cls._replace_variables(qss, variables)
            if not changed:
                break

        return qss

    @classmethod
    def _flatten_variables(cls, data: Dict, prefix: str = "") -> Dict:
        result = {}
        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                result.update(cls._flatten_variables(value, f"{full_key}_"))
            else:
                result[full_key] = value
        return result

    @classmethod
    def _replace_variables(cls, qss: str, variables: Dict) -> tuple:
        changed = False

        def replacer(match):
            nonlocal changed
            var_name = match.group(1)
            if var_name in variables:
                changed = True
                return str(variables[var_name])
            return match.group(0)

        new_qss = re.sub(r'@([a-zA-Z0-9_]+)', replacer, qss)
        return new_qss, changed