from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from gui.widgets.buttons import IconButton
from core.paths import resource_path


class Sidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Sidebar")
        self.setFixedWidth(56)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        self.home_btn = IconButton("assets/icons/home.svg", "Главная")
        self.home_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.home_btn)

        self.photos_btn = IconButton("assets/icons/images.svg", "Фото")
        self.photos_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.photos_btn)

        self.metadata_btn = IconButton("assets/icons/file-pen.svg", "Метаданные")
        self.metadata_btn.setProperty("class", "SidebarButton")
        self.metadata_btn.clicked.connect(lambda: self.page_changed.emit('metadata'))
        layout.addWidget(self.metadata_btn)

        self.templates_btn = IconButton("assets/icons/files.svg", "Шаблоны")
        self.templates_btn.setProperty("class", "SidebarButton")
        self.templates_btn.clicked.connect(lambda: self.page_changed.emit('templates'))
        layout.addWidget(self.templates_btn)

        self.yandex_btn = IconButton(str(resource_path("assets/icons/download.svg")), "Импорт")
        self.yandex_btn.setProperty("class", "SidebarButton")
        self.yandex_btn.clicked.connect(lambda: self.page_changed.emit('yandex'))
        layout.addWidget(self.yandex_btn)

        self.batch_btn = IconButton("assets/icons/layers.svg", "Пакетная обработка")
        self.batch_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.batch_btn)

        layout.addStretch()

        self.settings_btn = IconButton("assets/icons/settings.svg", "Настройки")
        self.settings_btn.setProperty("class", "SidebarButton")
        layout.addWidget(self.settings_btn)