from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from gui.widgets.buttons import IconButton


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Sidebar")
        self.setFixedWidth(56)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        self.home_btn = IconButton("", "Главная")
        self.home_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.home_btn)

        self.photos_btn = IconButton("", "Фото")
        self.photos_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.photos_btn)

        self.metadata_btn = IconButton("", "Метаданные")
        self.metadata_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.metadata_btn)

        self.batch_btn = IconButton("", "Пакетная обработка")
        self.batch_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.batch_btn)

        layout.addStretch()

        self.settings_btn = IconButton("", "Настройки")
        self.settings_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.settings_btn)

        # Сигналы НЕ ПОДКЛЮЧЕНЫ — будут подключены позже