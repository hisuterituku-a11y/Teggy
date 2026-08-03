from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "icons" / "teggy"


def tinted_pixmap(path: Path, size: QSize, color: str) -> QPixmap:
    source = QIcon(str(path)).pixmap(size)
    result = QPixmap(source.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.drawPixmap(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color))
    painter.end()
    return result


def tinted_icon(name: str, color: str, filled: bool = False) -> QIcon:
    suffix = "-filled" if filled else ""
    path = ICON_PATH / f"{name}{suffix}.svg"
    if not path.exists():
        path = ICON_PATH / f"{name}.svg"
    return QIcon(tinted_pixmap(path, QSize(22, 22), color))


class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(252)
        self._icon_color = "#A778FF"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(6)
        brand.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.brand_icon = QLabel()
        self.brand_icon.setObjectName("LogoIcon")
        brand.addWidget(self.brand_icon)

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
            ("Главная", "home", True, True),
            ("Тегирование", "photo", False, True),
            ("Яндекс Карты", "map", False, True),
            ("Wordstat", "search", False, True),
            ("Настройки", "settings", False, False),
        ]

        self.menu_buttons = {}
        self._menu_icon_names = {}
        for text, icon_name, active, visible in menu:
            button = QPushButton(text)
            button.setIconSize(QSize(22, 22))
            button.setObjectName("SideButton")
            button.setCheckable(True)
            button.page_name = text
            button.setChecked(active)
            button.setVisible(visible)
            self.menu_buttons[text] = button
            self._menu_icon_names[text] = icon_name
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

        self.set_icon_color(self._icon_color)

    def set_icon_color(self, color: str) -> None:
        self._icon_color = color
        logo_path = ICON_PATH / "logo.png"
        self.brand_icon.setPixmap(tinted_pixmap(logo_path, QSize(50, 50), color))
        for name, button in self.menu_buttons.items():
            icon_name = self._menu_icon_names[name]
            button.setIcon(tinted_icon(icon_name, color, button.isChecked()))

    def set_active(self, page_name: str) -> None:
        for name, button in self.menu_buttons.items():
            is_active = name == page_name
            button.setChecked(is_active)
            icon_name = self._menu_icon_names[name]
            button.setIcon(tinted_icon(icon_name, self._icon_color, is_active))
