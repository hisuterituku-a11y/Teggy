from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
)

from gui.components.sidebar import Sidebar
from gui.components.topbar import TopBar
from gui.pages.dashboard import Dashboard
from gui.pages.tegging import PhotoPage
from PySide6.QtWidgets import QPushButton

class MainWindow(QMainWindow):
    def __init__(self, theme_manager=None):
        super().__init__()

        self.theme_manager = theme_manager

        self.setWindowTitle("Teggy")
        self.resize(1440, 900)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.findChildren(QPushButton)[0].clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )


        self.sidebar.findChildren(QPushButton)[1].clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )
        self.topbar = TopBar()

        self.pages = QStackedWidget()

        self.dashboard_page = Dashboard()
        self.photo_page = PhotoPage()


        self.pages.addWidget(
            self.dashboard_page
        )

        self.pages.addWidget(
            self.photo_page
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