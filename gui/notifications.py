from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt


class Notification(QFrame):
    """Всплывающее уведомление."""
    def __init__(self, text: str, duration: int = 3000, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Notification")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(QLabel(text))

        QTimer.singleShot(duration, self.close)