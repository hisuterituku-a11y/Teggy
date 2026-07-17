from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from gui.header import Header
from gui.sidebar import Sidebar
from gui.inspector import Inspector
from gui.bottom_log import BottomLog
from gui.pages.metadata_page import MetadataPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teggy")
        self.setGeometry(100, 100, 1280, 820)
        self.setProperty("class", "MainWindow")

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = Header()
        main_layout.addWidget(self.header)

        # Body: Sidebar + Pages + Inspector
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.metadata_page = MetadataPage()
        self.metadata_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.metadata_page)
        body_layout.addWidget(self.stack, stretch=1)

        self.inspector = Inspector()
        body_layout.addWidget(self.inspector)

        main_layout.addWidget(body, stretch=1)

        # Bottom Log
        self.bottom_log = BottomLog()
        main_layout.addWidget(self.bottom_log)

        # Подключаем сигнал выбора файла из MetadataPage
        self.metadata_page.file_selected.connect(self.inspector.update_file_info)
    def log_message(self, message: str):
        """Отправляет сообщение в BottomLog."""
        if hasattr(self, 'bottom_log') and hasattr(self.bottom_log, 'log'):
            self.bottom_log.log.info(message)