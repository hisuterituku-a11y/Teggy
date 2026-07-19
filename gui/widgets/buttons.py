from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from core.paths import resource_path
from core.svg_loader import load_svg_icon


class PrimaryButton(QPushButton):
    """Главная кнопка действия."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "PrimaryButton")
        self._icon_size = QSize(20, 20)

    def set_icon(self, icon: QIcon):
        self.setIcon(icon)
        self.setIconSize(self._icon_size)

    def set_icon_size(self, size: QSize):
        self._icon_size = size
        self.setIconSize(size)


class SecondaryButton(QPushButton):
    """Второстепенная кнопка."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "SecondaryButton")
        self._icon_size = QSize(20, 20)

    def set_icon(self, icon: QIcon):
        self.setIcon(icon)
        self.setIconSize(self._icon_size)

    def set_icon_size(self, size: QSize):
        self._icon_size = size
        self.setIconSize(size)


class IconButton(QPushButton):

    def __init__(self, icon_path: str, tooltip="", parent=None):
        super().__init__(parent)

        self._icon_path = icon_path
        self._color = "#FFFFFF"

        self.reload_icon()

    def set_color(self, color: str):
        if self._color != color:
            self._color = color
            self.reload_icon()

    def reload_icon(self):
        self.setIcon(
            load_svg_icon(
                resource_path(self._icon_path),
                self._color
            )
        )