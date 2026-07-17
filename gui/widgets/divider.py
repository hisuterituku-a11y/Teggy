from PySide6.QtWidgets import QFrame


class Divider(QFrame):
    """Разделитель."""
    def __init__(self, orientation: str = "horizontal", parent=None):
        super().__init__(parent)
        self.setProperty("class", "Divider")
        if orientation == "horizontal":
            self.setFixedHeight(1)
        else:
            self.setFixedWidth(1)
            