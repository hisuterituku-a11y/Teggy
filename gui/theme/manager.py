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

    COMPONENT_PALETTES = {
        "default": {
            "topbar_border": "#27335A",
            "secondary_bg": "#151D35",
            "secondary_hover": "#202B4E",
            "secondary_text": "#F3F5FF",
            "secondary_border": "#3B4A7A",
            "premium_title": "#FFFFFF",
            "premium_text": "#C6CCEA",
            "tip_bg": "#171F39",
            "tip_text": "#D5DAF2",
            "tip_border": "#364574",
            "theme_bg": "#11182D",
            "theme_text": "#F4F6FF",
            "theme_selected": "#39206B",
            "theme_border": "#303B68",
            "accent": "#915CFF",
        },
        "light": {
            "topbar_border": "#D8DEEA",
            "secondary_bg": "#F7F8FC",
            "secondary_hover": "#EEE9FF",
            "secondary_text": "#263147",
            "secondary_border": "#CCD4E2",
            "premium_title": "#39206B",
            "premium_text": "#667085",
            "tip_bg": "#F0EAFF",
            "tip_text": "#4C347E",
            "tip_border": "#C4B1F4",
            "theme_bg": "#FFFFFF",
            "theme_text": "#172033",
            "theme_selected": "#E9E1FF",
            "theme_border": "#D9DFEA",
            "accent": "#8B5CF6",
        },
        "corporate": {
            "topbar_border": "#353A44",
            "secondary_bg": "#292E37",
            "secondary_hover": "#332A1B",
            "secondary_text": "#F0F2F5",
            "secondary_border": "#454C58",
            "premium_title": "#FFD38A",
            "premium_text": "#D2D7DF",
            "tip_bg": "#2C251A",
            "tip_text": "#E7C88E",
            "tip_border": "#71511F",
            "theme_bg": "#22262E",
            "theme_text": "#F0F2F5",
            "theme_selected": "#332A1B",
            "theme_border": "#3A404B",
            "accent": "#F59E0B",
        },
        "frogs": {
            "topbar_border": "#28695A",
            "secondary_bg": "#185E4F",
            "secondary_hover": "#206C5A",
            "secondary_text": "#F2FAF4",
            "secondary_border": "#4D8B78",
            "premium_title": "#F3FBF5",
            "premium_text": "#CBE3D6",
            "tip_bg": "#D9E9CF",
            "tip_text": "#244C3D",
            "tip_border": "#A9D9BC",
            "theme_bg": "#105447",
            "theme_text": "#F3FBF5",
            "theme_selected": "#D9E9CF",
            "theme_border": "#347565",
            "accent": "#A9D9BC",
        },
        "sakura": {
            "topbar_border": "#E6BFC4",
            "secondary_bg": "#F8E7E8",
            "secondary_hover": "#F4D9DD",
            "secondary_text": "#64434C",
            "secondary_border": "#DDB9BF",
            "premium_title": "#563640",
            "premium_text": "#8C6971",
            "tip_bg": "#FBE1E4",
            "tip_text": "#724650",
            "tip_border": "#E2AEB8",
            "theme_bg": "#FFF8F5",
            "theme_text": "#563640",
            "theme_selected": "#F2C9CF",
            "theme_border": "#E9C9CC",
            "accent": "#D9798D",
        },
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

    def _component_postlude(self, theme_name: str) -> str:
        palette = self.COMPONENT_PALETTES.get(
            theme_name,
            self.COMPONENT_PALETTES["default"],
        )
        return f"""
/* Final component layer. These selectors intentionally win over legacy QSS. */
#TopBar {{
    border-bottom: 1px solid {palette['topbar_border']};
}}
QPushButton#YandexActionButton,
QPushButton#DashboardSecondaryButton,
QPushButton#AboutSecondaryButton,
QPushButton#TemplateManagerButton {{
    background: {palette['secondary_bg']};
    color: {palette['secondary_text']};
    border: 1px solid {palette['secondary_border']};
    border-radius: 10px;
}}
QPushButton#YandexActionButton:hover,
QPushButton#DashboardSecondaryButton:hover,
QPushButton#AboutSecondaryButton:hover,
QPushButton#TemplateManagerButton:hover {{
    background: {palette['secondary_hover']};
    border-color: {palette['accent']};
}}
#PremiumTitle {{ color: {palette['premium_title']}; background: transparent; }}
#PremiumText {{ color: {palette['premium_text']}; background: transparent; }}
#DashboardTip {{
    background: {palette['tip_bg']};
    color: {palette['tip_text']};
    border: 1px solid {palette['tip_border']};
    border-radius: 10px;
    padding: 14px;
}}
QPushButton#ThemeChoiceButton {{
    background: {palette['theme_bg']};
    color: {palette['theme_text']};
    border: 1px solid {palette['theme_border']};
    border-radius: 10px;
    text-align: left;
    padding: 12px 16px;
}}
QPushButton#ThemeChoiceButton:hover {{ border-color: {palette['accent']}; }}
QPushButton#ThemeChoiceButton:checked {{
    background: {palette['theme_selected']};
    border: 2px solid {palette['accent']};
}}
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
        qss_parts.append(self._component_postlude(theme_name))
        return ThemeData("\n\n".join(qss_parts))

    def list_themes(self) -> list[str]:
        return [
            name
            for name in self.THEME_ORDER
            if name == "default" or (self.themes_path / name / "theme.qss").is_file()
        ]
