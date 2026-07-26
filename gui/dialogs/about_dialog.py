from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from core.version import display_version
from gui.components.window_title_bar import WindowTitleBar


REPOSITORY_URL = "https://github.com/hisuterituku-a11y/Teggy"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(460, 300)

        shell = QWidget(self)
        shell.setObjectName("AboutDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)

        title_bar = WindowTitleBar(
            self,
            title="О программе",
            show_help=False,
            show_minimize=False,
            show_maximize=False,
        )
        shell_layout.addWidget(title_bar)

        content = QWidget()
        content.setObjectName("AboutContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 26, 28, 24)
        content_layout.setSpacing(14)

        title = QLabel(display_version())
        title.setObjectName("AboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)

        description = QLabel(
            "Приложение для тегирования фотографий и работы с контентом Яндекс Карт."
        )
        description.setObjectName("AboutDescription")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(description)
        content_layout.addStretch(1)

        repository_button = QPushButton("Открыть репозиторий GitHub")
        repository_button.setObjectName("AboutPrimaryButton")
        repository_button.clicked.connect(self._open_repository)
        content_layout.addWidget(repository_button)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("AboutSecondaryButton")
        close_button.clicked.connect(self.reject)
        content_layout.addWidget(close_button)

        shell_layout.addWidget(content, 1)

    def _open_repository(self) -> None:
        QDesktopServices.openUrl(QUrl(REPOSITORY_URL))
