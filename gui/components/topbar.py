from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)


ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "icons" / "teggy"


def tinted_icon(name: str, color: str) -> QIcon:
    source = QIcon(str(ICON_PATH / f"{name}.svg")).pixmap(QSize(22, 22))
    result = QPixmap(source.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.drawPixmap(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color))
    painter.end()
    return QIcon(result)


class TopBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("TopBar")
        self._icon_color = "#A778FF"
        self._settings_icon_color = "#FFFFFF"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(10)

        self.title = QLabel("Главная")
        self.title.setObjectName("PageTitle")
        layout.addWidget(self.title)
        layout.addStretch(1)

        self.search = QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText("Поиск...")
        self.search.setMinimumWidth(260)
        self.search.setMaximumWidth(520)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.search, 1)

        self.theme_button = QPushButton()
        self.theme_button.setIconSize(QSize(22, 22))
        self.theme_button.setObjectName("ThemeButton")
        self.theme_button.setToolTip("Тема оформления")
        layout.addWidget(self.theme_button)

        self.notify_button = QPushButton()
        self.notify_button.setIconSize(QSize(22, 22))
        self.notify_button.setObjectName("NotifyButton")
        self.notify_button.setToolTip("Уведомления и обновления Teggy")
        layout.addWidget(self.notify_button)

        self.settings_button = QPushButton()
        self.settings_button.setIconSize(QSize(22, 22))
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setToolTip("Настройки")
        layout.addWidget(self.settings_button)

        self.set_icon_color(self._icon_color, self._settings_icon_color)

    def set_icon_color(self, color: str, settings_color: str | None = None) -> None:
        self._icon_color = color
        if settings_color is not None:
            self._settings_icon_color = settings_color
        self.theme_button.setIcon(tinted_icon("sun", color))
        self.notify_button.setIcon(tinted_icon("bell", color))
        self.settings_button.setIcon(tinted_icon("settings", self._settings_icon_color))
