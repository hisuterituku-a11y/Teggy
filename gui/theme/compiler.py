import re
from pathlib import Path
from typing import Dict


class QSSCompiler:
    """Компилирует все QSS-файлы темы, заменяя @переменные."""

    @classmethod
    def compile(cls, theme_path: Path, theme_data: Dict) -> str:
        qss_files = sorted(theme_path.glob("*.qss"), key=lambda path: (path.name != "style.qss", path.name))
        if not qss_files:
            return ""

        chunks = []
        for qss_path in qss_files:
            with open(qss_path, "r", encoding="utf-8") as file:
                chunks.append(file.read())

        variables = cls._flatten_variables(theme_data)
        qss = "\n\n".join(chunks)
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
    def _replace_variables(cls, qss: str, variables: Dict) -> tuple[str, bool]:
        changed = False

        def replacer(match):
            nonlocal changed
            var_name = match.group(1)
            if var_name in variables:
                changed = True
                return str(variables[var_name])
            return match.group(0)

        new_qss = re.sub(r"@([a-zA-Z0-9_]+)", replacer, qss)
        return new_qss, changed
