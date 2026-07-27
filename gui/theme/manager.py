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
    )

    def __init__(self, themes_path=None):
        self.themes_path = Path(themes_path) if themes_path else Path(__file__).parent

    def load(self, theme_name: str) -> ThemeData:
        theme_folder = self.themes_path / theme_name
        if not theme_folder.is_dir():
            return ThemeData("")

        qss_parts = []
        for file_name in self.QSS_FILES:
            qss_file = theme_folder / file_name
            if qss_file.is_file():
                qss_parts.append(qss_file.read_text(encoding="utf-8"))

        return ThemeData("\n\n".join(qss_parts))

    def list_themes(self) -> list[str]:
        if not self.themes_path.is_dir():
            return []

        return sorted(
            folder.name
            for folder in self.themes_path.iterdir()
            if folder.is_dir()
            and any((folder / file_name).is_file() for file_name in self.QSS_FILES)
        )
