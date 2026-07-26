from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox

from core.update_checker import ReleaseInfo
from core.version import __version__, display_version
from gui.components.application_shell import ApplicationShell
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
        self._initial_geometry_applied = False

        self.setWindowTitle(display_version())
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(1080, 680)

        self._create_menu()

        self.shell = ApplicationShell(self)
        self.setCentralWidget(self.shell)

        self.window_title_bar = self.shell.title_bar
        self.sidebar = self.shell.sidebar
        self.topbar = self.shell.topbar
        self.pages = self.shell.pages

        self.window_title_bar.help_button.clicked.connect(self._show_about_dialog)

        version_label = self.sidebar.findChild(QLabel, "VersionLabel")
        if version_label is not None:
            version_label.setText(f"v{__version__}")

        self.dashboard_page = Dashboard()
        self.photo_page = TaggingPage()
        self.yandex_maps_page = YandexMapsPage()

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.photo_page)
        self.pages.addWidget(self.yandex_maps_page)

        self.sidebar.menu_buttons["Главная"].clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )
        self.sidebar.menu_buttons["Тегирование"].clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )
        self.sidebar.menu_buttons["Яндекс Карты"].clicked.connect(
            lambda: self.pages.setCurrentIndex(2)
        )

        QTimer.singleShot(1500, self.update_service.check)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._initial_geometry_applied:
            return

        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return

        available = screen.availableGeometry()
        width = min(1440, max(self.minimumWidth(), available.width() - 40))
        height = min(900, max(self.minimumHeight(), available.height() - 40))
        x = available.x() + max(20, (available.width() - width) // 2)
        y = available.y() + 20

        self.setGeometry(x, y, width, height)
        self._initial_geometry_applied = True

    def _create_menu(self) -> None:
        self.menuBar().setVisible(False)
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
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel
        )
        message.setDefaultButton(QMessageBox.StandardButton.Open)

        if message.exec() == QMessageBox.StandardButton.Open:
            QDesktopServices.openUrl(QUrl(release.page_url))
