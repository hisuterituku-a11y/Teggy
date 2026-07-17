from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class Thumbnail(QFrame):
    """Миниатюра изображения."""
    def __init__(self, filename: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "Thumbnail")
        self.setFixedSize(120, 120)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("📄")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(QLabel(filename))