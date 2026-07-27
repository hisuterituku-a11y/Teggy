from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QGuiApplication,
    QPainterPath,
    QPalette,
    QRegion,
)
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QScrollArea, QWidget

from core.update_checker import ReleaseInfo
from core.version import __version__, display_version
from gui.components.application_shell import ApplicationShell
from gui.dialogs.about_dialog import AboutDialog
from gui.pages.dashboard import Dashboard
from gui.pages.settings_page import SettingsPage
from gui.pages.tagging_fixed import TaggingPage
from gui.pages.yandex_maps import YandexMapsPage
from gui.services.update_service import UpdateService


class ResizeHandle(QWidget):
    """Невидимая зона изменения размера frameless-окна."""

    def __init__(self, window: QMainWindow, edges: Qt.Edge, cursor: Qt.CursorShape):
        super().__init__(window)
        self._window = window
        self._edges = edges
        self.setCursor(cursor)
        self.setMouseTracking(True)
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemResize(self._edges)
            event.accept()


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 7
    SAFE_MINIMUM_WIDTH = 1024
    SAFE_MINIMUM_HEIGHT = 680

    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self._manual_update_check = False
        self._update_dialog_open = False

        self.setWindowTitle(f"Teggy {display_version()}")
        self.setMinimumSize(self.SAFE_MINIMUM_WIDTH, self.SAFE_MINIMUM_HEIGHT)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.update_service = UpdateService(self)
        self.update_service.update_available.connect(self._handle_update_available)
        self.update_service.no_update.connect(self._handle_no_update)
        self.update_service.error.connect(self._handle_update_error)

        self.shell = ApplicationShell()
        self.setCentralWidget(self.shell)
        self.sidebar = self.shell.sidebar
        self.topbar = self.shell.topbar
        self.window_title_bar = self.shell.window_title_bar
        self.pages = self.shell.pages

        self.window_title_bar.help_button.clicked.connect(self._show_about_dialog)

        version_label = self.sidebar.findChild(QLabel, "VersionLabel")
        if version_label is not None:
            version_label.setText(f"v{__version__}")

        self.dashboard_page = Dashboard()
        self.photo_page = TaggingPage()
        self.yandex_maps_page = YandexMapsPage()
        self.settings_page = SettingsPage()
        self.settings_page.reset_interface_requested.connect(self.reset_interface_geometry)

        self.pages.addWidget(self._scroll_page(self.dashboard_page))
        self.pages.addWidget(self._scroll_page(self.photo_page))
        self.pages.addWidget(self._scroll_page(self.yandex_maps_page))
        self.pages.addWidget(self._scroll_page(self.settings_page))

        self._page_map = {
            "Главная": 0,
            "Тегирование": 1,
            "Яндекс Карты": 2,
            "Настройки": 3,
        }
        for name, index in self._page_map.items():
            self.sidebar.menu_buttons[name].clicked.connect(
                lambda checked=False, page_index=index, page_name=name: self._switch_page(
                    page_index,
                    page_name,
                )
            )

        self.dashboard_page.navigate_requested.connect(self._open_page_by_name)
        self.dashboard_page.check_updates_requested.connect(self._start_manual_update_check)

        self._resize_handles = self._create_resize_handles()
        self._switch_page(0, "Главная")
        QTimer.singleShot(1500, self.update_service.check)

    def _scroll_page(self, page):
        scroll = QScrollArea()
        scroll.setObjectName("PageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(page)
        return scroll

    def _open_page_by_name(self, page_name: str) -> None:
        index = self._page_map.get(page_name)
        if index is not None:
            self._switch_page(index, page_name)

    def _switch_page(self, index: int, page_name: str) -> None:
        self.pages.setCurrentIndex(index)
        self.sidebar.set_active(page_name)

    def _start_manual_update_check(self) -> None:
        self._manual_update_check = True
        self.dashboard_page.set_update_checking()

        if not self.update_service.check():
            self._manual_update_check = False
            self.dashboard_page.set_update_result("Проверка уже выполняется.")

    def _handle_no_update(self) -> None:
        if self._manual_update_check:
            self.dashboard_page.set_update_result("Установлена актуальная версия Teggy.")
        self._manual_update_check = False

    def _handle_update_error(self, message: str) -> None:
        if self._manual_update_check:
            self.dashboard_page.set_update_result(f"Не удалось проверить обновления: {message}")
        self._manual_update_check = False

    def _handle_update_available(self, release: ReleaseInfo) -> None:
        self.dashboard_page.set_update_result(f"Доступна версия {release.version}")
        self._manual_update_check = False

        if self._update_dialog_open:
            return
        self._update_dialog_open = True

        box = QMessageBox(self)
        box.setWindowTitle("Доступно обновление")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(f"Доступна новая версия Teggy {release.version}.")
        if release.notes:
            box.setInformativeText(release.notes[:500])
        download_button = box.addButton("Открыть страницу релиза", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Позже", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        self._update_dialog_open = False

        if box.clickedButton() is download_button:
            QDesktopServices.openUrl(QUrl(release.url))

    def _show_about_dialog(self) -> None:
        AboutDialog(self).exec()

    def reset_interface_geometry(self) -> None:
        self.resize(1280, 820)
        screen = QGuiApplication.screenAt(self.frameGeometry().center()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def _create_resize_handles(self):
        specs = (
            (Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor),
            (Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor),
            (Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor),
            (Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor),
            (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.CursorShape.SizeFDiagCursor),
            (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.CursorShape.SizeBDiagCursor),
            (Qt.Edge.LeftEdge | Qt.Edge.BottomEdge, Qt.CursorShape.SizeBDiagCursor),
            (Qt.Edge.RightEdge | Qt.Edge.BottomEdge, Qt.CursorShape.SizeFDiagCursor),
        )
        return [ResizeHandle(self, edges, cursor) for edges, cursor in specs]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = self.RESIZE_MARGIN
        width = self.width()
        height = self.height()
        left, right, top, bottom, top_left, top_right, bottom_left, bottom_right = self._resize_handles

        left.setGeometry(0, margin, margin, max(0, height - 2 * margin))
        right.setGeometry(width - margin, margin, margin, max(0, height - 2 * margin))
        top.setGeometry(margin, 0, max(0, width - 2 * margin), margin)
        bottom.setGeometry(margin, height - margin, max(0, width - 2 * margin), margin)
        top_left.setGeometry(0, 0, margin, margin)
        top_right.setGeometry(width - margin, 0, margin, margin)
        bottom_left.setGeometry(0, height - margin, margin, margin)
        bottom_right.setGeometry(width - margin, height - margin, margin, margin)

        self._update_window_mask()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_window_mask()

    def _update_window_mask(self) -> None:
        radius = 18
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        polygon = path.toFillPolygon().toPolygon()
        self.setMask(QRegion(polygon))
