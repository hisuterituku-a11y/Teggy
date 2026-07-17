from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.widgets.buttons import IconButton


class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Header")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self.logo = QLabel("Teggy")
        self.logo.setProperty("class", "HeaderLogo")
        layout.addWidget(self.logo)

        layout.addStretch()

        self.theme_btn = IconButton("", "Сменить тему")
        self.theme_btn.setProperty("class", "HeaderButton")
        layout.addWidget(self.theme_btn)

        self.settings_btn = IconButton("", "Настройки")
        self.settings_btn.setProperty("class", "HeaderButton")
        layout.addWidget(self.settings_btn)

        self.help_btn = IconButton("", "Помощь")
        self.help_btn.setProperty("class", "HeaderButton")
        layout.addWidget(self.help_btn)

        # Сигналы НЕ ПОДКЛЮЧЕНЫ — будут подключены позже