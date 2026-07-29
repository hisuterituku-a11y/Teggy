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
    THEME_ORDER = ("default",)

    SCROLLBAR_PALETTES = {
        "default": ("#0B1022", "#4A2A82", "#915CFF"),
        "light": ("#E9EDF5", "#AEB8CA", "#8B5CF6"),
        "corporate": ("#191D23", "#555D69", "#F33C00"),
        "frogs": ("#083D33", "#679887", "#A9D9BC"),
        "sakura": ("#F1D9DC", "#CF939F", "#D9798D"),
    }

    COMPONENT_PALETTES = {
        "default": {
            "topbar_border": "#27335A", "chrome_bg": "#11182D", "chrome_text": "#DCE2FF",
            "chrome_hover": "#202B4E", "secondary_bg": "#151D35", "secondary_hover": "#202B4E",
            "secondary_text": "#F3F5FF", "secondary_border": "#3B4A7A",
            "premium_title": "#FFFFFF", "premium_text": "#C6CCEA",
            "tip_bg": "#171F39", "tip_text": "#D5DAF2", "tip_border": "#364574",
            "theme_bg": "#11182D", "theme_text": "#F4F6FF", "theme_selected": "#39206B",
            "theme_hover": "#1A2340", "theme_border": "#303B68", "accent": "#915CFF",
            "dialog_bg": "#0B1022", "dialog_card": "#11182D", "dialog_text": "#F4F6FF",
            "step_bg": "#2C1B52", "step_text": "#FFFFFF", "step_border": "#915CFF",
            "check_bg": "#11182D", "check_border": "#5D6A98", "check_hover": "#2A355E",
            "check_checked": "#915CFF", "check_checked_hover": "#A778FF",
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
            theme_name, self.SCROLLBAR_PALETTES["default"]
        )
        return f"""
QScrollBar:vertical, #PageScroll QScrollBar:vertical, QAbstractScrollArea QScrollBar:vertical {{ background: {track}; width: 10px; margin: 0; border: none; }}
QScrollBar::handle:vertical, #PageScroll QScrollBar::handle:vertical, QAbstractScrollArea QScrollBar::handle:vertical {{ background: {handle}; min-height: 28px; border-radius: 5px; border: none; }}
QScrollBar::handle:vertical:hover, #PageScroll QScrollBar::handle:vertical:hover {{ background: {hover}; }}
QScrollBar:horizontal, #PageScroll QScrollBar:horizontal, QAbstractScrollArea QScrollBar:horizontal {{ background: {track}; height: 10px; margin: 0; border: none; }}
QScrollBar::handle:horizontal, #PageScroll QScrollBar::handle:horizontal, QAbstractScrollArea QScrollBar::handle:horizontal {{ background: {handle}; min-width: 28px; border-radius: 5px; border: none; }}
QScrollBar::handle:horizontal:hover, #PageScroll QScrollBar::handle:horizontal:hover {{ background: {hover}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; background: transparent; border: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""

    def _component_postlude(self, theme_name: str) -> str:
        p = self.COMPONENT_PALETTES.get(theme_name, self.COMPONENT_PALETTES["default"])
        return f"""
/* Final component layer. These selectors intentionally win over legacy QSS. */
#TopBar {{ border-bottom: 1px solid {p['topbar_border']}; }}
#WindowTitleBar {{ background: {p['chrome_bg']}; border: none; border-bottom: 1px solid {p['topbar_border']}; border-radius: 0; }}
#WindowTitle {{ color: {p['chrome_text']}; background: transparent; font-weight: 600; }}
#WindowHelpButton, #WindowControlButton, #WindowCloseButton {{ background: transparent; color: {p['chrome_text']}; border: none; border-radius: 0; }}
#WindowHelpButton:hover, #WindowControlButton:hover {{ background: {p['chrome_hover']}; color: {p['accent']}; }}
#WindowCloseButton:hover {{ background: #D94B64; color: #FFFFFF; }}
QPushButton#ThemeButton, QPushButton#NotifyButton {{ background: {p['chrome_bg']}; color: {p['accent']}; border: 1px solid {p['topbar_border']}; border-radius: 18px; }}
QPushButton#ThemeButton:hover, QPushButton#NotifyButton:hover {{ background: {p['chrome_hover']}; color: {p['accent']}; border-color: {p['accent']}; }}
QPushButton#SettingsButton {{ background: {p['chrome_bg']}; border: 1px solid {p['topbar_border']}; border-radius: 18px; color: {p['accent']}; }}
QPushButton#SettingsButton:hover {{ background: {p['chrome_hover']}; border-color: {p['accent']}; color: {p['accent']}; }}
QPushButton#YandexActionButton, QPushButton#DashboardSecondaryButton, QPushButton#AboutSecondaryButton, QPushButton#TemplateManagerButton {{ background: {p['secondary_bg']}; color: {p['secondary_text']}; border: 1px solid {p['secondary_border']}; border-radius: 10px; }}
QPushButton#YandexActionButton:hover, QPushButton#DashboardSecondaryButton:hover, QPushButton#AboutSecondaryButton:hover, QPushButton#TemplateManagerButton:hover {{ background: {p['secondary_hover']}; color: {p['secondary_text']}; border-color: {p['accent']}; }}
#PremiumTitle {{ color: {p['premium_title']}; background: transparent; }}
#PremiumText {{ color: {p['premium_text']}; background: transparent; }}
QLabel#DashboardTip {{ background: {p['tip_bg']}; color: {p['tip_text']}; border: 1px solid {p['tip_border']}; border-radius: 10px; padding: 14px; min-height: 70px; }}
QLabel#DashboardStepBadge {{ background: {p['step_bg']}; color: {p['step_text']}; border: 1px solid {p['step_border']}; border-radius: 15px; font-weight: 700; }}
QPushButton#ThemeChoiceButton {{ background: {p['theme_bg']}; color: {p['theme_text']}; border: 1px solid {p['theme_border']}; border-radius: 10px; text-align: left; padding: 12px 16px; }}
QPushButton#ThemeChoiceButton:hover {{ background: {p['theme_hover']}; color: {p['theme_text']}; border-color: {p['accent']}; }}
QPushButton#ThemeChoiceButton:checked {{ background: {p['theme_selected']}; color: {p['theme_text']}; border: 2px solid {p['accent']}; }}

/* Checkbox indicators are fully theme-owned, including hover states. */
QCheckBox, QRadioButton {{ background: transparent; spacing: 9px; }}
QCheckBox::indicator, QRadioButton::indicator,
QCheckBox#DownloadOptionCheck::indicator, QRadioButton#DownloadOptionCheck::indicator,
QCheckBox#SettingsCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 5px;
    background: {p['check_bg']}; border: 1px solid {p['check_border']};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover,
QCheckBox#DownloadOptionCheck::indicator:hover, QRadioButton#DownloadOptionCheck::indicator:hover,
QCheckBox#SettingsCheckBox::indicator:hover {{
    background: {p['check_hover']}; border-color: {p['accent']};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked,
QCheckBox#DownloadOptionCheck::indicator:checked, QRadioButton#DownloadOptionCheck::indicator:checked,
QCheckBox#SettingsCheckBox::indicator:checked {{
    background: {p['check_checked']}; border-color: {p['check_checked']};
    image: url(assets/icons/teggy/check.svg);
}}
QCheckBox::indicator:checked:hover, QRadioButton::indicator:checked:hover,
QCheckBox#DownloadOptionCheck::indicator:checked:hover, QRadioButton#DownloadOptionCheck::indicator:checked:hover,
QCheckBox#SettingsCheckBox::indicator:checked:hover {{
    background: {p['check_checked_hover']}; border-color: {p['check_checked_hover']};
    image: url(assets/icons/teggy/check.svg);
}}
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{
    background: {p['secondary_bg']}; border-color: {p['secondary_border']};
}}

#ThumbnailCard {{ background: {p['dialog_card']}; border: 1px solid {p['theme_border']}; border-radius: 10px; }}
#ThumbnailCard:hover {{ background: {p['theme_hover']}; border-color: {p['accent']}; }}
#ThumbnailCard[selected="true"] {{ background: {p['theme_selected']}; border: 2px solid {p['accent']}; }}
#DownloadOptionCard[selected="true"] {{ background: {p['theme_selected']}; border: 2px solid {p['accent']}; }}
#DownloadOptionCard[selected="true"] #DownloadOptionTitle {{ color: {p['theme_text']}; }}
#DownloadOptionCard[selected="true"] #DownloadOptionDescription {{ color: {p['dialog_text']}; }}
#ThumbnailImage, #ThumbnailName {{ background: transparent; color: {p['dialog_text']}; }}
#FolderItem:hover, #DownloadOptionCard:hover, #DashboardActionCard:hover, #DashboardWorkflowRow:hover {{ background: {p['theme_hover']}; border-color: {p['accent']}; }}
QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {{ background: {p['theme_hover']}; color: {p['theme_text']}; }}
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{ background: {p['theme_selected']}; color: {p['theme_text']}; }}
QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {{ background: {p['theme_hover']}; color: {p['theme_text']}; }}

#TemplateDialog, #TemplateContent {{ background: {p['dialog_bg']}; color: {p['dialog_text']}; }}
#TemplateSidebar, #TemplateEditor {{ background: {p['dialog_card']}; color: {p['dialog_text']}; border: 1px solid {p['theme_border']}; border-radius: 12px; }}
#TemplateDialog QLabel {{ background: transparent; color: {p['dialog_text']}; border: none; border-radius: 0; padding: 0; }}
#TemplateDialog QLineEdit, #TemplateDialog QTextEdit, #TemplateDialog QListWidget {{ background: {p['secondary_bg']}; color: {p['secondary_text']}; border: 1px solid {p['secondary_border']}; border-radius: 9px; }}
#TemplateDialog QPushButton {{ min-height: 36px; padding: 0 14px; border-radius: 9px; }}
#TemplateDialog #TemplateManagerButton, #TemplateDialog #AboutSecondaryButton {{ background: {p['secondary_bg']}; color: {p['secondary_text']}; border: 1px solid {p['secondary_border']}; }}
#TemplateDialog #TemplateManagerButton:hover, #TemplateDialog #AboutSecondaryButton:hover {{ background: {p['secondary_hover']}; color: {p['secondary_text']}; border-color: {p['accent']}; }}
#TemplateDialog #TemplatePrimaryButton {{ background: {p['accent']}; color: #FFFFFF; border: 1px solid {p['accent']}; }}
#TemplateDialog #TemplateDangerButton {{ background: transparent; color: #D94B64; border: 1px solid #D94B64; }}
#TemplateDialog QSplitter::handle {{ background: {p['topbar_border']}; width: 1px; }}
#ThemedMessageBox, #ThemedMessageContent {{ background: {p['dialog_bg']}; color: {p['dialog_text']}; }}
#ThemedMessageCard {{ background: {p['dialog_card']}; border: 1px solid {p['theme_border']}; border-radius: 12px; }}
#ThemedMessageText {{ color: {p['dialog_text']}; background: transparent; }}
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
