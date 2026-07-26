from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
)

from core.version import display_version
from gui.components.sidebar import Sidebar
from gui.components.topbar import TopBar
from gui.pages.dashboard import Dashboard
from gui.pages.tagging import TaggingPage
from gui.pages.yandex_maps import YandexMapsPage


class MainWindow(QMainWindow):
    def __init__(self, theme_manager=None):
        super().__init__()

        self.theme_manager = theme_manager

        self.setWindowTitle(display_version())
        self.resize(1440, 900)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.menu_buttons["Главная"].clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )

        self.sidebar.menu_buttons["Тегирование"].clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )

        self.sidebar.menu_buttons["Яндекс Карты"].clicked.connect(
            lambda: self.pages.setCurrentIndex(2)
        )
        self.topbar = TopBar()

        self.pages = QStackedWidget()

        self.dashboard_page = Dashboard()
        self.photo_page = TaggingPage()
        self.yandex_maps_page = YandexMapsPage()

        self.pages.addWidget(
            self.dashboard_page
        )

        self.pages.addWidget(
            self.photo_page
        )

        self.pages.addWidget(
            self.yandex_maps_page
        )

        # правая часть: topbar + страницы
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        content.addWidget(self.topbar)
        content.addWidget(self.pages, 1)

        layout.addWidget(self.sidebar)
        layout.addLayout(content, 1)

        self.setCentralWidget(central)
