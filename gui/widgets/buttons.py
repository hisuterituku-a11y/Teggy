from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from core.paths import resource_path

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
    """Кнопка с SVG-иконкой."""
    def __init__(self, icon_path: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(str(resource_path(icon_path))))
        self.setIconSize(QSize(24, 24))
        self.setToolTip(tooltip)
        self.setProperty("class", "IconButton")
        self.setFocusPolicy(Qt.NoFocus)