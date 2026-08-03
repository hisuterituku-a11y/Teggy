from PySide6.QtCore import QThread, QTimer, Qt, QUrl
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
from core.wordstat.worker import WordstatWorker
from gui.components.application_shell import ApplicationShell
from gui.dialogs.help_dialog import HelpDialog
from gui.pages.dashboard import Dashboard
from gui.pages.settings_page import SettingsPage
from gui.pages.tagging_fixed import TaggingPage
from gui.pages.wordstat import WordstatPage
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
    DEFAULT_WIDTH = 1180
    DEFAULT_HEIGHT = 860

    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self._manual_update_check = False
        self._update_dialog_open = False
        self._wordstat_thread: QThread | None = None
        self._wordstat_worker: WordstatWorker | None = None

        self.setWindowTitle(f"Teggy {display_version()}")
        self.setMinimumSize(self.SAFE_MINIMUM_WIDTH, self.SAFE_MINIMUM_HEIGHT)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.update_service = UpdateService(self)
        self.update_service.update_available.connect(self._handle_update_available)
        self.update_service.no_update.connect(self._handle_no_update)
        self.update_service.failed.connect(self._handle_update_error)

        self.shell = ApplicationShell(self)
        self.setCentralWidget(self.shell)
        self.sidebar = self.shell.sidebar
        self.topbar = self.shell.topbar
        self.window_title_bar = self.shell.title_bar
        self.pages = self.shell.pages

        self.window_title_bar.help_button.clicked.connect(self._show_help_dialog)

        version_label = self.sidebar.findChild(QLabel, "VersionLabel")
        if version_label is not None:
            version_label.setText(f"v{__version__}")

        self.dashboard_page = Dashboard()
        self.photo_page = TaggingPage()
        self.yandex_maps_page = YandexMapsPage()
        self.wordstat_page = WordstatPage()
        self.settings_page = SettingsPage()
        self.settings_page.reset_interface_requested.connect(self.reset_interface_geometry)

        self.pages.addWidget(self._scroll_page(self.dashboard_page))
        self.pages.addWidget(self._scroll_page(self.photo_page))
        self.pages.addWidget(self._scroll_page(self.yandex_maps_page))
        self.pages.addWidget(self._scroll_page(self.wordstat_page))
        self.pages.addWidget(self._scroll_page(self.settings_page))

        self._page_map = {
            "Главная": 0,
            "Тегирование": 1,
            "Яндекс Карты": 2,
            "Wordstat": 3,
            "Настройки": 4,
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
        self.wordstat_page.generate_requested.connect(self._start_wordstat_generation)
        self.wordstat_page.cancel_requested.connect(self._cancel_wordstat_generation)

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
        self.topbar.title.setText(page_name)

    def _start_wordstat_generation(self, form_data) -> None:
        if self._wordstat_thread is not None:
            self.wordstat_page.append_log("Сбор Wordstat уже выполняется")
            return

        thread = QThread(self)
        worker = WordstatWorker(form_data)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self.wordstat_page.append_log)
        worker.finished.connect(self._handle_wordstat_finished)
        worker.error.connect(self._handle_wordstat_error)
        worker.cancelled.connect(self._handle_wordstat_cancelled)

        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_wordstat_worker)

        self._wordstat_thread = thread
        self._wordstat_worker = worker
        self.wordstat_page.append_log("Запускаем генерацию тегов Wordstat")
        thread.start()

    def _cancel_wordstat_generation(self) -> None:
        worker = self._wordstat_worker
        if worker is None:
            return

        self.wordstat_page.append_log("Запрошена отмена генерации")
        worker.cancel()

    def _handle_wordstat_finished(self, result: dict) -> None:
        self.wordstat_page.set_result(
            text=str(result.get("text", "")),
            collected_count=int(result.get("collected_count", 0)),
            merged_count=int(result.get("merged_count", 0)),
            filtered_count=int(result.get("filtered_count", 0)),
            tag_count=int(result.get("tag_count", 0)),
        )

    def _handle_wordstat_error(self, message: str) -> None:
        self.wordstat_page.show_error(message)

    def _handle_wordstat_cancelled(self) -> None:
        self.wordstat_page.show_cancelled()

    def _clear_wordstat_worker(self) -> None:
        self._wordstat_worker = None
        self._wordstat_thread = None

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
        self._manual_update_check = False
        self.dashboard_page.set_update_result(f"Не удалось проверить обновления: {message}")

    def _handle_update_available(self, release: ReleaseInfo) -> None:
        self._manual_update_check = False
        self.dashboard_page.set_update_result(
            f"Доступна версия {release.version}."
        )
        if self._update_dialog_open:
            return

        self._update_dialog_open = True
        try:
            answer = QMessageBox.question(
                self,
                "Обновление Teggy",
                f"Доступна новая версия {release.version}. Открыть страницу релиза?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl(release.html_url))
        finally:
            self._update_dialog_open = False

    def _show_help_dialog(self) -> None:
        dialog = HelpDialog(self)
        dialog.exec()

    def reset_interface_geometry(self) -> None:
        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        width = min(max(self.SAFE_MINIMUM_WIDTH, self.DEFAULT_WIDTH), available.width())
        height = min(max(self.SAFE_MINIMUM_HEIGHT, self.DEFAULT_HEIGHT), available.height())
        self.resize(width, height)
        self.move(available.center() - self.rect().center())

    def closeEvent(self, event) -> None:
        worker = self._wordstat_worker
        thread = self._wordstat_thread
        if worker is not None:
            worker.cancel()
        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait(3000)
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_window_mask()
        self._position_resize_handles()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_window_mask()
        self._position_resize_handles()

    def _update_window_mask(self) -> None:
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 14, 14)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def _create_resize_handles(self) -> dict[str, ResizeHandle]:
        handles = {
            "left": ResizeHandle(self, Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor),
            "right": ResizeHandle(self, Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor),
            "top": ResizeHandle(self, Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor),
            "bottom": ResizeHandle(self, Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor),
            "top_left": ResizeHandle(
                self,
                Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
                Qt.CursorShape.SizeFDiagCursor,
            ),
            "top_right": ResizeHandle(
                self,
                Qt.Edge.TopEdge | Qt.Edge.RightEdge,
                Qt.CursorShape.SizeBDiagCursor,
            ),
            "bottom_left": ResizeHandle(
                self,
                Qt.Edge.BottomEdge | Qt.Edge.LeftEdge,
                Qt.CursorShape.SizeBDiagCursor,
            ),
            "bottom_right": ResizeHandle(
                self,
                Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
                Qt.CursorShape.SizeFDiagCursor,
            ),
        }
        return handles

    def _position_resize_handles(self) -> None:
        margin = self.RESIZE_MARGIN
        width = self.width()
        height = self.height()

        self._resize_handles["left"].setGeometry(0, margin, margin, height - 2 * margin)
        self._resize_handles["right"].setGeometry(width - margin, margin, margin, height - 2 * margin)
        self._resize_handles["top"].setGeometry(margin, 0, width - 2 * margin, margin)
        self._resize_handles["bottom"].setGeometry(margin, height - margin, width - 2 * margin, margin)
        self._resize_handles["top_left"].setGeometry(0, 0, margin, margin)
        self._resize_handles["top_right"].setGeometry(width - margin, 0, margin, margin)
        self._resize_handles["bottom_left"].setGeometry(0, height - margin, margin, margin)
        self._resize_handles["bottom_right"].setGeometry(width - margin, height - margin, margin, margin)

        for handle in self._resize_handles.values():
            handle.raise_()
