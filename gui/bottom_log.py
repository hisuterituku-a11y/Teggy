from PySide6.QtWidgets import QWidget, QVBoxLayout
from gui.widgets.log_widget import LogWidget


class BottomLog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "BottomLog")
        self.setFixedHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.log = LogWidget()
        layout.addWidget(self.log)

        # Стартовые сообщения
        self.log.info("Teggy started")
        self.log.success("Theme loaded")
        self.log.info("UI initialized")