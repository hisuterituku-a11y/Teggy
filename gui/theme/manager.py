from pathlib import Path


class ThemeData:
    def __init__(self, qss: str):
        self.qss = qss


class ThemeManager:
    QSS_FILES = (
        "style.qss",
        "dashboard.qss",
        "inspector.qss",
        "window.qss",
        "templates.qss",
        "settings.qss",
        "theme.qss",
    )
    THEME_ORDER = ("default", "light", "corporate", "frogs", "sakura")

    def __init__(self, themes_path=None):
        self.themes_path = Path(themes_path) if themes_path else Path(__file__).parent

    def _read_theme_parts(self, theme_folder: Path) -> list[str]:
        parts: list[str] = []
        for file_name in self.QSS_FILES:
            qss_file = theme_folder / file_name
            if qss_file.is_file():
                parts.append(qss_file.read_text(encoding="utf-8"))
        return parts

    def load(self, theme_name: str) -> ThemeData:
        default_folder = self.themes_path / "default"
        theme_folder = self.themes_path / theme_name
        if not theme_folder.is_dir() or theme_name not in self.THEME_ORDER:
            theme_folder = default_folder
            theme_name = "default"

        qss_parts = self._read_theme_parts(default_folder)
        if theme_name != "default":
            overlay = theme_folder / "theme.qss"
            if overlay.is_file():
                qss_parts.append(overlay.read_text(encoding="utf-8"))
        return ThemeData("\n\n".join(qss_parts))

    def list_themes(self) -> list[str]:
        return [
            name
            for name in self.THEME_ORDER
            if name == "default" or (self.themes_path / name / "theme.qss").is_file()
        ]
