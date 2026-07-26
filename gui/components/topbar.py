# ============================================================
# Teggy TopBar
# Sprint 3.8
#
# Верхняя панель приложения.
# Здесь находятся название страницы, поиск и быстрые действия.
# ============================================================

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)


ICON_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "assets"
    / "icons"
    / "teggy"
)


def load_icon(name):
    return QIcon(str(ICON_PATH / f"{name}.svg"))


class TopBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("TopBar")

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
        self.theme_button.setIcon(load_icon("sun"))
        self.theme_button.setIconSize(QSize(22, 22))
        self.theme_button.setObjectName("ThemeButton")
        layout.addWidget(self.theme_button)

        self.notify_button = QPushButton()
        self.notify_button.setIcon(load_icon("bell"))
        self.notify_button.setIconSize(QSize(22, 22))
        self.notify_button.setObjectName("NotifyButton")
        layout.addWidget(self.notify_button)
