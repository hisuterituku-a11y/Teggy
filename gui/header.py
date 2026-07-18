from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu
from PySide6.QtCore import Qt, Signal
from gui.widgets.buttons import IconButton


class Header(QWidget):
    theme_requested = Signal(str)  # Сигнал для смены темы

    def __init__(self, theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setProperty("class", "Header")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self.logo = QLabel("Teggy")
        self.logo.setProperty("class", "HeaderLogo")
        layout.addWidget(self.logo)

        layout.addStretch()

        # Кнопка темы с меню
        self.theme_btn = IconButton("assets/icons/palette.svg", "Сменить тему")
        self.theme_btn.setProperty("class", "HeaderButton")
        self.theme_menu = QMenu(self)
        self._build_theme_menu()
        self.theme_btn.setMenu(self.theme_menu)
        layout.addWidget(self.theme_btn)

        self.settings_btn = IconButton("assets/icons/settings.svg", "Настройки")
        self.settings_btn.setProperty("class", "HeaderButton")
        layout.addWidget(self.settings_btn)

        self.help_btn = IconButton("assets/icons/help.svg", "Помощь")
        self.help_btn.setProperty("class", "HeaderButton")
        layout.addWidget(self.help_btn)

    def _build_theme_menu(self):
        """Строит меню из доступных тем."""
        self.theme_menu.clear()
        
        if not self.theme_manager:
            self.theme_menu.addAction("Нет тем")
            return
        
        themes = self.theme_manager.list_themes()
        if not themes:
            self.theme_menu.addAction("Нет тем")
            return
        
        for theme_name in sorted(themes):
            action = self.theme_menu.addAction(theme_name.capitalize())
            
            action.triggered.connect(
                lambda checked, name=theme_name: self._emit_theme(name)
            )

    def _emit_theme(self, theme_name: str):
        """Отправляет сигнал с именем темы."""
        self.theme_requested.emit(theme_name)