from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.update_checker import ReleaseInfo
from core.version import __version__, display_version
from gui.components.sidebar import Sidebar
from gui.components.topbar import TopBar
from gui.dialogs.about_dialog import AboutDialog
from gui.pages.dashboard import Dashboard
from gui.pages.tagging import TaggingPage
from gui.pages.yandex_maps import YandexMapsPage
from gui.services.update_service import UpdateService


class MainWindow(QMainWindow):
    def __init__(self, theme_manager=None):
        super().__init__()

        self.theme_manager = theme_manager
        self.update_service = UpdateService(self)
        self.update_service.update_available.connect(self._show_update_available)

        self.setWindowTitle(display_version())
        self.resize(1440, 900)
        self._create_menu()

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        version_label = self.sidebar.findChild(QLabel, "VersionLabel")
        if version_label is not None:
            version_label.setText(f"v{__version__}")

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

        # Не задерживаем запуск окна сетевым запросом.
        QTimer.singleShot(1500, self.update_service.check)

    def _create_menu(self) -> None:
        help_menu = self.menuBar().addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_about_dialog(self) -> None:
        AboutDialog(self).exec()

    def _show_update_available(self, release: ReleaseInfo) -> None:
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle("Доступно обновление")
        message.setText(f"Доступна версия Teggy {release.version}")
        message.setInformativeText(
            "Открыть страницу релиза для загрузки новой версии?"
        )
        message.setStandardButtons(
            QMessageBox.StandardButton.Open
            | QMessageBox.StandardButton.Cancel
        )
        message.setDefaultButton(QMessageBox.StandardButton.Open)

        if message.exec() == QMessageBox.StandardButton.Open:
            QDesktopServices.openUrl(QUrl(release.page_url))
