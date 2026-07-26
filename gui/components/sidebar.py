from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "icons" / "teggy"


def load_icon(name: str) -> QIcon:
    return QIcon(str(ICON_PATH / f"{name}.svg"))


class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(252)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(6)
        brand.setAlignment(Qt.AlignmentFlag.AlignLeft)

        brand_icon = QLabel()
        brand_icon.setObjectName("LogoIcon")
        pixmap = QPixmap(str(ICON_PATH / "logo.png"))
        brand_icon.setPixmap(
            pixmap.scaled(
                50,
                50,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        brand.addWidget(brand_icon)

        logo = QLabel("Teggy")
        logo.setObjectName("Logo")
        brand.addWidget(logo)
        brand.addStretch()
        layout.addLayout(brand)

        sub = QLabel("AI PHOTO TAGGER")
        sub.setObjectName("LogoSub")
        layout.addWidget(sub)

        version = QLabel()
        version.setObjectName("VersionLabel")
        layout.addWidget(version)
        layout.addSpacing(28)

        menu = [
            ("Главная", "home", True),
            ("Тегирование", "photo", False),
            ("Яндекс Карты", "map", False),
            ("Теги", "tag", False),
            ("Шаблоны", "templates", False),
            ("Настройки", "settings", False),
        ]

        self.menu_buttons = {}
        for text, icon, active in menu:
            button = QPushButton(text)
            button.setIcon(load_icon(icon))
            button.setIconSize(QSize(22, 22))
            button.setObjectName("SideButton")
            button.setCheckable(True)
            button.page_name = text
            button.setChecked(active)
            self.menu_buttons[text] = button
            layout.addWidget(button)

        layout.addStretch(1)

        premium_card = QFrame()
        premium_card.setObjectName("PremiumCard")
        premium_layout = QVBoxLayout(premium_card)
        premium_layout.setContentsMargins(14, 10, 14, 10)
        premium_layout.setSpacing(6)

        premium_title = QLabel("✦ Teggy PRO")
        premium_title.setObjectName("PremiumTitle")
        premium_layout.addWidget(premium_title)

        premium_text = QLabel("Все функции открыты\nAI + Яндекс + шаблоны")
        premium_text.setObjectName("PremiumText")
        premium_layout.addWidget(premium_text)

        layout.addWidget(premium_card)
