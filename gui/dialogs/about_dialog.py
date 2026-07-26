from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.version import display_version


REPOSITORY_URL = "https://github.com/hisuterituku-a11y/Teggy"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("AboutDialog")
        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setFixedSize(460, 310)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 24)
        layout.setSpacing(14)

        mark = QLabel("T")
        mark.setObjectName("AboutMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(64, 64)
        layout.addWidget(mark, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(display_version())
        title.setObjectName("AboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "Приложение для тегирования фотографий и работы с контентом Яндекс Карт."
        )
        description.setObjectName("AboutDescription")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        repository_button = QPushButton("Открыть репозиторий GitHub")
        repository_button.setObjectName("AboutRepositoryButton")
        repository_button.clicked.connect(self._open_repository)
        layout.addWidget(repository_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.setObjectName("AboutButtonBox")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _open_repository(self) -> None:
        QDesktopServices.openUrl(QUrl(REPOSITORY_URL))
