from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QApplication
from pathlib import Path
from gui.header import Header
from gui.sidebar import Sidebar
from gui.inspector import Inspector
from gui.bottom_log import BottomLog
from gui.pages.metadata_page import MetadataPage
from gui.pages.templates_page import TemplatesPage
from gui.dragdrop import DragDropManager
from core.settings import Settings
from PySide6.QtGui import QColor


class MainWindow(QMainWindow):
    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("Teggy")
        self.setGeometry(100, 100, 1280, 820)
        self.setProperty("class", "MainWindow")
        self.setAcceptDrops(True)

        # Загружаем геометрию окна
        geometry = Settings.get_window_geometry()
        self.setGeometry(
            geometry.get("x", 100),
            geometry.get("y", 100),
            geometry.get("width", 1280),
            geometry.get("height", 820)
        )

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = Header(theme_manager=self.theme_manager)
        self.header.theme_requested.connect(self._apply_theme)
        main_layout.addWidget(self.header)

        # Body: Sidebar + Pages + Inspector
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()

        # MetadataPage
        self.metadata_page = MetadataPage()
        self.metadata_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.metadata_page)

        # TemplatesPage
        self.templates_page = TemplatesPage()
        self.templates_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.templates_page)

        body_layout.addWidget(self.stack, stretch=1)

        from gui.pages.yandex_downloader_page import YandexDownloaderPage

        self.yandex_page = YandexDownloaderPage()
        self.yandex_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.yandex_page)

        # Drag & Drop менеджер
        self.dragdrop = DragDropManager()
        self.dragdrop.folder_dropped.connect(self._on_folder_dropped)
        self.dragdrop.files_dropped.connect(self._on_files_dropped)

        app = QApplication.instance()
        app.installEventFilter(self.dragdrop)

        self.inspector = Inspector()
        body_layout.addWidget(self.inspector)

        main_layout.addWidget(body, stretch=1)

        # Bottom Log
        self.bottom_log = BottomLog()
        main_layout.addWidget(self.bottom_log)

        # Подключаем сигнал выбора файла из MetadataPage
        self.metadata_page.file_selected.connect(self.inspector.update_file_info)

        # Подключаем сигнал обновления шаблонов
        self.metadata_page.templates_updated.connect(self.templates_page._refresh_list)

    def _apply_theme(self, theme_name: str):
        if not self.theme_manager:
            return

        theme = self.theme_manager.load(theme_name)
        app = QApplication.instance()
        app.setStyleSheet("")
        app.processEvents()
        app.setStyleSheet(theme.qss)

        Settings.save_theme(theme_name)

    def log_message(self, message: str):
        """Отправляет сообщение в BottomLog."""
        if hasattr(self, 'bottom_log') and hasattr(self.bottom_log, 'log'):
            self.bottom_log.log.info(message)

    def _switch_page(self, page: str):
        print(f"Switch to: {page}")  # временно для проверки
        if page == 'metadata':
            self.stack.setCurrentWidget(self.metadata_page)
        elif page == 'templates':
            self.templates_page._refresh_list()
            self.stack.setCurrentWidget(self.templates_page)
        elif page == 'yandex':
            self.stack.setCurrentWidget(self.yandex_page)

    def _on_folder_dropped(self, path: str):
        self.metadata_page.folder_field.setText(path)
        self.metadata_page._load_files(path)
        self.metadata_page._refresh_templates()
        self.log_message(f"Папка открыта через Drag&Drop: {path}")

    def _on_files_dropped(self, paths: list):
        if not paths:
            return

        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
        image_paths = [p for p in paths if Path(p).suffix.lower() in image_extensions]

        if not image_paths:
            self.log_message("Перетащены не изображения")
            return

        self.metadata_page.load_files_from_paths(image_paths)
        self.metadata_page._refresh_templates()

        parent_dir = Path(image_paths[0]).parent
        self.log_message(f"Загружено из папки: {parent_dir}")
        self.log_message(f"Загружено файлов: {len(image_paths)}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                path = urls[0].toLocalFile()
                if Path(path).is_dir():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return

        local_paths = []
        for url in urls:
            if url.isLocalFile():
                local_paths.append(url.toLocalFile())

        if not local_paths:
            event.ignore()
            return

        first_path = Path(local_paths[0])

        if len(local_paths) == 1 and first_path.is_dir():
            path = str(first_path)
            self.metadata_page.folder_field.setText(path)
            self.metadata_page._load_files(path)
            self.metadata_page._refresh_templates()
            self.log_message(f"Папка открыта через Drag&Drop: {path}")
            event.acceptProposedAction()
            return

        parent_dir = first_path.parent
        all_same_folder = all(Path(p).parent == parent_dir for p in local_paths)

        if all_same_folder:
            self.metadata_page.folder_field.setText(str(parent_dir))
            self.metadata_page._load_files(str(parent_dir))
            self.metadata_page._refresh_templates()
            self.metadata_page._select_files_by_names([Path(p).name for p in local_paths])
            self.log_message(f"Открыта папка: {parent_dir}")
            self.log_message(f"Выделено файлов: {len(local_paths)}")
            event.acceptProposedAction()
        else:
            self.log_message("Перетаскивайте файлы только из одной папки")
            event.ignore()

    def closeEvent(self, event):
        """Сохраняет настройки при закрытии окна."""
        geo = self.geometry()
        Settings.save_window_geometry(geo.x(), geo.y(), geo.width(), geo.height())

        if hasattr(self.metadata_page, 'delete_original_cb'):
            Settings.save_delete_original(
                self.metadata_page.delete_original_cb.isChecked()
            )

        if hasattr(self.metadata_page, 'template_combo'):
            current_template = self.metadata_page.template_combo.currentText()
            if current_template and current_template != "Нет шаблонов":
                Settings.save_last_template(current_template)

        event.accept()