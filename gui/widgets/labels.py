from PySide6.QtWidgets import QLabel


class IconLabel(QLabel):
    """Лейбл с иконкой и текстом."""
    def __init__(self, icon_path: str, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "IconLabel")
        # иконка будет добавлена позже через QSS + :before
        