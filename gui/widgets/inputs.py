from PySide6.QtWidgets import QLineEdit, QTextEdit
from PySide6.QtCore import Qt


class TextField(QLineEdit):
    """Однострочное поле ввода."""
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setProperty("class", "TextField")


class SearchField(QLineEdit):
    """Поле поиска с иконкой."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Поиск...")
        self.setProperty("class", "SearchField")


class TagEditor(QTextEdit):
    """Многострочное поле для тегов."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TagEditor")
        self.setPlaceholderText("Введите теги (по одному на строке)")