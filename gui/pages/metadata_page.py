from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from core.files.file_service import FileService, FileInfo
from gui.widgets.cards import Card, CardHeader, CardBody
from gui.widgets.inputs import TextField, TagEditor
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from pathlib import Path


class MetadataPage(QWidget):
    file_selected = Signal(FileInfo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "MetadataPage")
        self.current_files: list[FileInfo] = []

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Левая колонка
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Карточка выбора папки
        folder_card = Card()
        folder_row = QHBoxLayout()
        self.folder_field = TextField("Выберите папку...")
        self.folder_field.setReadOnly(True)
        folder_row.addWidget(self.folder_field)

        self.browse_btn = SecondaryButton("Обзор")
        self.browse_btn.setIcon(QIcon("assets/icons/folder-open.svg"))
        folder_row.addWidget(self.browse_btn)

        folder_card.add_layout(folder_row)
        left_layout.addWidget(folder_card)

        # Список файлов
        self.file_list = QListWidget()
        self.file_list.setProperty("class", "FileList")
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.file_list)

        main_layout.addWidget(left_panel, stretch=1)

        # Правая колонка
        right_panel = QWidget()
        right_panel.setFixedWidth(380)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        meta_card = Card()
        header = CardHeader()
        header.set_title("Метаданные")
        meta_card.add_widget(header)

        body = CardBody()
        self.title_field = TextField("Название")
        body.add_widget(self.title_field)

        self.subject_field = TextField("Тема")
        body.add_widget(self.subject_field)

        self.author_field = TextField("Автор")
        body.add_widget(self.author_field)

        self.keywords_field = TagEditor()
        body.add_widget(self.keywords_field)

        self.comment_field = TextField("Комментарий")
        body.add_widget(self.comment_field)

        meta_card.add_widget(body)
        right_layout.addWidget(meta_card)

        self.action_btn = PrimaryButton("Записать метаданные")
        self.action_btn.setIcon(QIcon("assets/icons/save.svg"))
        right_layout.addWidget(self.action_btn)

        right_layout.addStretch()

        main_layout.addWidget(right_panel)

        # Подключаем сигналы
        self.browse_btn.clicked.connect(self._browse_folder)

    def _browse_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с фотографиями")
        if folder:
            self.folder_field.setText(folder)
            self._load_files(folder)

    def _load_files(self, folder_path: str):
        path = Path(folder_path)
        files = FileService.get_files(path)
        self.current_files = files

        self.file_list.clear()
        for file_info in files:
            item = QListWidgetItem(file_info.name)
            item.setData(Qt.UserRole, file_info)
            self.file_list.addItem(item)

        self.log(f"Папка выбрана: {folder_path}")
        self.log(f"Найдено файлов: {len(files)}")

    def _on_selection_changed(self):
        selected = self.file_list.selectedItems()
        if not selected:
            return

        item = selected[0]
        file_info = item.data(Qt.UserRole)
        if file_info:
            self.file_selected.emit(file_info)

    def log(self, message: str):
        if hasattr(self, 'parent') and hasattr(self.parent(), 'parent'):
            bottom_log = self.parent().parent().bottom_log
            if hasattr(bottom_log, 'log'):
                bottom_log.log.info(message)