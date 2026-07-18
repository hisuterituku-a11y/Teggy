from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QApplication
from pathlib import Path
from gui.header import Header
from gui.sidebar import Sidebar
from gui.inspector import Inspector
from gui.bottom_log import BottomLog
from gui.pages.metadata_page import MetadataPage
from gui.pages.templates_page import TemplatesPage
from gui.dragdrop import DragDropManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teggy")
        self.setGeometry(100, 100, 1280, 820)
        self.setProperty("class", "MainWindow")
        self.setAcceptDrops(True)

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
        self.sidebar.page_changed.connect(self._switch_page)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.metadata_page = MetadataPage()
        self.metadata_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.metadata_page)
        # Drag & Drop менеджер
        self.dragdrop = DragDropManager()
        self.dragdrop.folder_dropped.connect(self._on_folder_dropped)
        self.dragdrop.files_dropped.connect(self._on_files_dropped)

        app = QApplication.instance()
        app.installEventFilter(self.dragdrop)
        body_layout.addWidget(self.stack, stretch=1)

    # Страница шаблонов
        self.templates_page = TemplatesPage()
        self.templates_page.log_message.connect(self.log_message)
        self.stack.addWidget(self.templates_page)

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
            
    def _switch_page(self, page: str):
        if page == 'metadata':
            self.stack.setCurrentWidget(self.metadata_page)
        elif page == 'templates':
            self.stack.setCurrentWidget(self.templates_page)

    def _on_folder_dropped(self, path: str):
        """Обрабатывает перетаскивание папки."""
        self.metadata_page.folder_field.setText(path)
        self.metadata_page._load_files(path)
        self.metadata_page._refresh_templates()
        self.log_message(f"📁 Папка открыта через Drag&Drop: {path}")

    def _on_files_dropped(self, paths: list):
        """Обрабатывает перетаскивание файлов."""
        if not paths:
            return
        
        # Проверяем, что все файлы — изображения
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
        image_paths = [p for p in paths if Path(p).suffix.lower() in image_extensions]
        
        if not image_paths:
            self.log_message("⚠️ Перетащены не изображения")
            return
        
        # Загружаем только перетащенные файлы
        self.metadata_page.load_files_from_paths(image_paths)
        self.metadata_page._refresh_templates()
        
        parent_dir = Path(image_paths[0]).parent
        self.log_message(f"📁 Загружено из папки: {parent_dir}")
        self.log_message(f"📄 Загружено файлов: {len(image_paths)}")

    def dragEnterEvent(self, event):
        """Проверяет, можно ли принять перетаскиваемые данные."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                path = urls[0].toLocalFile()
                if Path(path).is_dir():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Обрабатывает перетаскивание папки или файлов."""
        urls = event.mimeData().urls()
        print(f"DEBUG: urls = {urls}")
        if not urls:
            event.ignore()
            return

        # Проверяем, что перетаскиваются локальные файлы
        local_paths = []
        for url in urls:
            if url.isLocalFile():
                local_paths.append(url.toLocalFile())
        print(f"DEBUG: local_paths = {local_paths}")

        if not local_paths:
            event.ignore()
            return

        # Проверяем, все ли пути — файлы из одной папки
        first_path = Path(local_paths[0])
        
        # Если перетащили папку
        if len(local_paths) == 1 and first_path.is_dir():
            path = str(first_path)
            self.metadata_page.folder_field.setText(path)
            self.metadata_page._load_files(path)
            self.metadata_page._refresh_templates()
            self.log_message(f"📁 Папка открыта через Drag&Drop: {path}")
            event.acceptProposedAction()
            return
        
        # Если перетащили файлы
        # Проверяем, что все файлы лежат в одной папке
        parent_dir = first_path.parent
        all_same_folder = all(Path(p).parent == parent_dir for p in local_paths)
        
        if all_same_folder:
            # Открываем папку
            self.metadata_page.folder_field.setText(str(parent_dir))
            self.metadata_page._load_files(str(parent_dir))
            self.metadata_page._refresh_templates()
            
            # Выделяем перетащенные файлы
            self.metadata_page._select_files_by_names([Path(p).name for p in local_paths])
            
            self.log_message(f"📁 Открыта папка: {parent_dir}")
            self.log_message(f"📄 Выделено файлов: {len(local_paths)}")
            event.acceptProposedAction()
        else:
            self.log_message("⚠️ Перетаскивайте файлы только из одной папки")
            event.ignore()