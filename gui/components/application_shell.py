from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from gui.components.sidebar import Sidebar
from gui.components.topbar import TopBar
from gui.components.window_title_bar import WindowTitleBar


class ApplicationShell(QWidget):
    """Единая оболочка окна: title bar, sidebar, topbar и страницы."""

    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("WindowShell")

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.title_bar = WindowTitleBar(window)
        root.addWidget(self.title_bar)

        body = QWidget()
        body.setObjectName("WindowBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.topbar = TopBar()
        self.pages = QStackedWidget()
        self.pages.setObjectName("PageStack")

        content = QWidget()
        content.setObjectName("ContentShell")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.topbar)
        content_layout.addWidget(self.pages, 1)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(content, 1)
        root.addWidget(body, 1)
