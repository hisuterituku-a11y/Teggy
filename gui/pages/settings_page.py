from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    reset_interface_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(18)

        title = QLabel("Настройки")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("PhotoPanel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        card_title = QLabel("Интерфейс")
        card_title.setObjectName("CardTitle")
        card_layout.addWidget(card_title)

        description = QLabel(
            "Вернуть окно к безопасному размеру и расположить его по центру доступной области экрана."
        )
        description.setObjectName("CardSubtitle")
        description.setWordWrap(True)
        card_layout.addWidget(description)

        reset_button = QPushButton("Сбросить размер и положение окна")
        reset_button.setObjectName("PrimaryButton")
        reset_button.clicked.connect(self.reset_interface_requested)
        card_layout.addWidget(reset_button)

        root.addWidget(card)
        root.addStretch(1)
