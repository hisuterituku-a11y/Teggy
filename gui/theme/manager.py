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

    SCROLLBAR_PALETTES = {
        "default": ("#0B1022", "#4A2A82", "#915CFF"),
        "light": ("#E9EDF5", "#AEB8CA", "#8B5CF6"),
        "corporate": ("#191D23", "#555D69", "#F59E0B"),
        "frogs": ("#083D33", "#679887", "#A9D9BC"),
        "sakura": ("#F1D9DC", "#CF939F", "#D9798D"),
    }

    def __init__(self, themes_path=None):
        self.themes_path = Path(themes_path) if themes_path else Path(__file__).parent

    def _read_theme_parts(self, theme_folder: Path) -> list[str]:
        parts: list[str] = []
        for file_name in self.QSS_FILES:
            qss_file = theme_folder / file_name
            if qss_file.is_file():
                parts.append(qss_file.read_text(encoding="utf-8"))
        return parts

    def _scrollbar_postlude(self, theme_name: str) -> str:
        track, handle, hover = self.SCROLLBAR_PALETTES.get(
            theme_name,
            self.SCROLLBAR_PALETTES["default"],
        )
        return f"""
/* Applied last so a base-theme selector cannot leak purple into another theme. */
QScrollBar:vertical, #PageScroll QScrollBar:vertical,
QAbstractScrollArea QScrollBar:vertical {{
    background: {track}; width: 10px; margin: 0; border: none;
}}
QScrollBar::handle:vertical, #PageScroll QScrollBar::handle:vertical,
QAbstractScrollArea QScrollBar::handle:vertical {{
    background: {handle}; min-height: 28px; border-radius: 5px; border: none;
}}
QScrollBar::handle:vertical:hover,
#PageScroll QScrollBar::handle:vertical:hover {{ background: {hover}; }}
QScrollBar:horizontal, #PageScroll QScrollBar:horizontal,
QAbstractScrollArea QScrollBar:horizontal {{
    background: {track}; height: 10px; margin: 0; border: none;
}}
QScrollBar::handle:horizontal, #PageScroll QScrollBar::handle:horizontal,
QAbstractScrollArea QScrollBar::handle:horizontal {{
    background: {handle}; min-width: 28px; border-radius: 5px; border: none;
}}
QScrollBar::handle:horizontal:hover,
#PageScroll QScrollBar::handle:horizontal:hover {{ background: {hover}; }}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0; height: 0; background: transparent; border: none;
}}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""

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
        qss_parts.append(self._scrollbar_postlude(theme_name))
        return ThemeData("\n\n".join(qss_parts))

    def list_themes(self) -> list[str]:
        return [
            name
            for name in self.THEME_ORDER
            if name == "default" or (self.themes_path / name / "theme.qss").is_file()
        ]
