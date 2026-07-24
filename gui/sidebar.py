from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.widgets.buttons import IconButton


class Sidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Sidebar")
        self.setFixedWidth(64)

        self._buttons: dict[str, IconButton] = {}

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        self.home_btn = self._add_button(
            layout, "home", "assets/icons/home.svg", "Главная"
        )
        self.photos_btn = self._add_button(
            layout, "photos", "assets/icons/images.svg", "Фото"
        )
        self.metadata_btn = self._add_button(
            layout, "metadata", "assets/icons/file-pen.svg", "Метаданные"
        )
        self.templates_btn = self._add_button(
            layout, "templates", "assets/icons/files.svg", "Шаблоны"
        )
        self.yandex_btn = self._add_button(
            layout, "yandex", "assets/icons/download.svg", "Импорт"
        )
        self.batch_btn = self._add_button(
            layout, "batch", "assets/icons/layers.svg", "Пакетная обработка"
        )

        layout.addStretch()

        self.settings_btn = self._add_button(
            layout, "settings", "assets/icons/settings.svg", "Настройки"
        )

        self.set_active_page("home")

    def _add_button(
        self,
        layout: QVBoxLayout,
        page: str,
        icon_path: str,
        tooltip: str,
    ) -> IconButton:
        button = IconButton(icon_path, tooltip, self)
        button.setProperty("class", "SidebarButton")
        button.setProperty("active", False)
        button.setFixedSize(48, 48)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda checked=False, name=page: self.page_changed.emit(name))
        layout.addWidget(button)
        self._buttons[page] = button
        return button

    def set_active_page(self, page: str) -> None:
        for name, button in self._buttons.items():
            button.setProperty("active", name == page)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
