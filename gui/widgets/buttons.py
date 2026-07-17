from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon


class PrimaryButton(QPushButton):
    """Главная кнопка действия."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "PrimaryButton")


class SecondaryButton(QPushButton):
    """Второстепенная кнопка."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "SecondaryButton")


class IconButton(QPushButton):
    """Кнопка с SVG-иконкой."""
    def __init__(self, icon_path: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(24, 24))
        self.setToolTip(tooltip)
        self.setProperty("class", "IconButton")