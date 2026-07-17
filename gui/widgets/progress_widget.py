from PySide6.QtWidgets import QProgressBar


class ProgressWidget(QProgressBar):
    """Прогресс-бар с кастомным стилем."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "ProgressWidget")
        self.setRange(0, 100)
        self.setValue(0)