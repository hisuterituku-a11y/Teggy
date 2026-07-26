from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QGuiApplication,
    QPainterPath,
    QRegion,
)
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QScrollArea, QWidget

from core.update_checker import ReleaseInfo
from core.version import __version__, display_version
from gui.components.application_shell import ApplicationShell
from gui.dialogs.about_dialog import AboutDialog
from gui.pages.dashboard import Dashboard
from gui.pages.tagging import TaggingPage
from gui.pages.yandex_maps import YandexMapsPage
from gui.services.update_service import UpdateService


class ResizeHandle(QWidget):
    """Невидимая зона изменения размера frameless-окна."""

    def __init__(self, window: QMainWindow, edges: Qt.Edge, cursor: Qt.CursorShape):
        super().__init__(window)
        self._window = window
        self._edges = edges
        self.setCursor(cursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._window.isMaximized():
            handle = self._window.windowHandle()
            if handle is not None:
                handle.startSystemResize(self._edges)
                event.accept()
                return
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    RESIZE_BORDER = 7
    RESIZE_CORNER = 14

    def __init__(self, theme_manager=None):
        super().__init__()

        self.theme_manager = theme_manager
        self.update_service = UpdateService(self)
        self.update_service.update_available.connect(self._show_update_available)
        self._initial_geometry_applied = False

        self.setWindowTitle(display_version())
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Ниже этого порога Dashboard начинает ломать композицию.
        # Остальные длинные страницы уже живут в scroll-контейнерах.
        self.setMinimumSize(1024, 640)

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
        self.pages.addWidget(self._scroll_page(self.photo_page))
        self.pages.addWidget(self._scroll_page(self.yandex_maps_page))

        page_map = {
            "Главная": 0,
            "Тегирование": 1,
            "Яндекс Карты": 2,
        }
        for name, index in page_map.items():
            self.sidebar.menu_buttons[name].clicked.connect(
                lambda checked=False, page_index=index, page_name=name: self._switch_page(
                    page_index,
                    page_name,
                )
            )

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

    def _switch_page(self, index: int, page_name: str) -> None:
        self.pages.setCurrentIndex(index)
        self.sidebar.set_active(page_name)

    def _create_resize_handles(self) -> dict[str, ResizeHandle]:
        return {
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

    def _layout_resize_handles(self) -> None:
        if not hasattr(self, "_resize_handles"):
            return

        maximized = self.isMaximized()
        for handle in self._resize_handles.values():
            handle.setVisible(not maximized)
        if maximized:
            return

        width = self.width()
        height = self.height()
        border = self.RESIZE_BORDER
        corner = self.RESIZE_CORNER

        self._resize_handles["left"].setGeometry(0, corner, border, height - 2 * corner)
        self._resize_handles["right"].setGeometry(
            width - border,
            corner,
            border,
            height - 2 * corner,
        )
        self._resize_handles["top"].setGeometry(corner, 0, width - 2 * corner, border)
        self._resize_handles["bottom"].setGeometry(
            corner,
            height - border,
            width - 2 * corner,
            border,
        )
        self._resize_handles["top_left"].setGeometry(0, 0, corner, corner)
        self._resize_handles["top_right"].setGeometry(width - corner, 0, corner, corner)
        self._resize_handles["bottom_left"].setGeometry(0, height - corner, corner, corner)
        self._resize_handles["bottom_right"].setGeometry(
            width - corner,
            height - corner,
            corner,
            corner,
        )

        for handle in self._resize_handles.values():
            handle.raise_()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._initial_geometry_applied:
            self._layout_resize_handles()
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
        self._apply_rounded_mask()
        self._layout_resize_handles()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_rounded_mask()
        self._layout_resize_handles()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            QTimer.singleShot(0, self._layout_resize_handles)
            QTimer.singleShot(0, self._apply_rounded_mask)

    def _apply_rounded_mask(self) -> None:
        if self.isMaximized():
            self.clearMask()
            return

        path = QPainterPath()
        path.addRoundedRect(self.rect(), 14, 14)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

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
