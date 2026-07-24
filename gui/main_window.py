from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.settings import Settings
from gui.bottom_log import BottomLog
from gui.dragdrop import DragDropManager
from gui.header import Header
from gui.inspector import Inspector
from gui.pages.home_page import HomePage
from gui.pages.metadata_page import MetadataPage
from gui.pages.templates_page import TemplatesPage
from gui.pages.yandex_downloader_page import YandexDownloaderPage
from gui.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("Teggy")
        self.setProperty("class", "MainWindow")
        self.setAcceptDrops(True)

        geometry = Settings.get_window_geometry()
        self.setGeometry(
            geometry.get("x", 100),
            geometry.get("y", 100),
            geometry.get("width", 1280),
            geometry.get("height", 820),
        )

        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = Header(theme_manager=self.theme_manager)
        self.header.theme_requested.connect(self._apply_theme)
        main_layout.addWidget(self.header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, stretch=1)

        self.home_page = HomePage()
        self.home_page.page_requested.connect(self._switch_page)
        self.home_page.open_folder_requested.connect(self._choose_folder)
        self.home_page.create_template_requested.connect(self._create_template)
        self.stack.addWidget(self.home_page)

        self.metadata_page = MetadataPage()
        self.metadata_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.metadata_page)

        self.templates_page = TemplatesPage()
        self.templates_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.templates_page)

        self.yandex_page = YandexDownloaderPage()
        self.yandex_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.yandex_page)

        self._pages = {
            "home": self.home_page,
            "metadata": self.metadata_page,
            "templates": self.templates_page,
            "yandex": self.yandex_page,
        }
        self._page_aliases = {"photos": "metadata", "batch": "metadata"}

        self.inspector = Inspector()
        body_layout.addWidget(self.inspector)
        main_layout.addWidget(body, stretch=1)

        self.bottom_log = BottomLog()
        main_layout.addWidget(self.bottom_log)

        self.metadata_page.file_selected.connect(self.inspector.update_file_info)
        self.metadata_page.templates_updated.connect(self.templates_page._refresh_list)

        self.dragdrop = DragDropManager()
        self.dragdrop.folder_dropped.connect(self._on_folder_dropped)
        self.dragdrop.files_dropped.connect(self._on_files_dropped)

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self.dragdrop)

        self._switch_page("home")

    def _apply_theme(self, theme_name: str) -> None:
        if not self.theme_manager:
            return
        theme = self.theme_manager.load(theme_name)
        app = QApplication.instance()
        if app is None:
            return
        app.setStyleSheet("")
        app.processEvents()
        app.setStyleSheet(theme.qss)
        Settings.save_theme(theme_name)

        from gui.widgets.buttons import IconButton

        icon_color = theme.colors.get("icon", theme.colors.get("text", "#FFFFFF"))
        for button in self.findChildren(IconButton):
            button.set_color(icon_color)

    def log_message(self, message: str) -> None:
        if hasattr(self, "bottom_log") and hasattr(self.bottom_log, "log"):
            self.bottom_log.log.info(message)

        match = re.search(r"Обработано\s+(\d+)\s+из\s+\d+\s+файлов", message)
        if match:
            Settings.increment_processed_files(int(match.group(1)))
            Settings.update_dashboard_stats(last_run=datetime.now().isoformat(timespec="minutes"))
            self.home_page.refresh()

    def _switch_page(self, page: str) -> None:
        requested_page = page
        page = self._page_aliases.get(page, page)
        if page == "settings":
            self.log_message("Раздел настроек будет подключён следующим этапом")
            return

        widget = self._pages.get(page)
        if widget is None:
            self.log_message(f"Неизвестный раздел: {requested_page}")
            return

        if page == "home":
            self.home_page.refresh()
        elif page == "templates":
            self.templates_page._refresh_list()
        elif page == "metadata" and not self.metadata_page.current_files:
            last_folder = Settings.get_last_folder()
            folder_path = Path(last_folder) if last_folder else None
            if folder_path and folder_path.exists() and folder_path.is_dir():
                self.metadata_page.folder_field.setText(str(folder_path))
                self.metadata_page._load_files(str(folder_path))
                self.metadata_page._refresh_templates()

        self.stack.setCurrentWidget(widget)
        active_page = requested_page if requested_page in self.sidebar._buttons else page
        self.sidebar.set_active_page(active_page)
        self.inspector.setVisible(page == "metadata")

    def _choose_folder(self) -> None:
        start_dir = Settings.get_last_folder() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self,
            "Открыть папку с фотографиями",
            start_dir,
        )
        if folder:
            self._on_folder_dropped(folder)

    def _create_template(self) -> None:
        self._switch_page("templates")
        for method_name in ("_create_template", "create_template", "_add_template"):
            method = getattr(self.templates_page, method_name, None)
            if callable(method):
                method()
                return
        self.log_message("Открыт раздел шаблонов")

    def _open_metadata_workspace(self) -> None:
        self._switch_page("metadata")

    def _on_folder_dropped(self, path: str) -> None:
        Settings.save_last_folder(path)
        self._open_metadata_workspace()
        self.metadata_page.folder_field.setText(path)
        self.metadata_page._load_files(path)
        self.metadata_page._refresh_templates()
        self.home_page.refresh()
        self.log_message(f"Папка открыта: {path}")

    def _on_files_dropped(self, paths: list[str]) -> None:
        if not paths:
            return
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
        image_paths = [path for path in paths if Path(path).suffix.lower() in image_extensions]
        if not image_paths:
            self.log_message("Перетащены не изображения")
            return

        parent_dir = Path(image_paths[0]).parent
        Settings.save_last_folder(str(parent_dir))
        self._open_metadata_workspace()
        self.metadata_page.load_files_from_paths(image_paths)
        self.metadata_page._refresh_templates()
        self.home_page.refresh()
        self.log_message(f"Загружено из папки: {parent_dir}")
        self.log_message(f"Загружено файлов: {len(image_paths)}")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        local_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if not local_paths:
            event.ignore()
            return

        first_path = Path(local_paths[0])
        if len(local_paths) == 1 and first_path.is_dir():
            self._on_folder_dropped(str(first_path))
            event.acceptProposedAction()
            return

        parent_dir = first_path.parent
        if not all(Path(path).parent == parent_dir for path in local_paths):
            self.log_message("Перетаскивайте файлы только из одной папки")
            event.ignore()
            return

        Settings.save_last_folder(str(parent_dir))
        self._open_metadata_workspace()
        self.metadata_page.folder_field.setText(str(parent_dir))
        self.metadata_page._load_files(str(parent_dir))
        self.metadata_page._refresh_templates()
        self.metadata_page._select_files_by_names([Path(path).name for path in local_paths])
        self.home_page.refresh()
        self.log_message(f"Открыта папка: {parent_dir}")
        self.log_message(f"Выделено файлов: {len(local_paths)}")
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:
        geo = self.geometry()
        Settings.save_window_geometry(geo.x(), geo.y(), geo.width(), geo.height())
        if hasattr(self.metadata_page, "delete_original_cb"):
            Settings.save_delete_original(self.metadata_page.delete_original_cb.isChecked())
        if hasattr(self.metadata_page, "template_combo"):
            current_template = self.metadata_page.template_combo.currentText()
            if current_template and current_template != "Нет шаблонов":
                Settings.save_last_template(current_template)
        event.accept()
