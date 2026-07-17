from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from pathlib import Path
import shutil

from core.files.file_service import FileService, FileInfo
from core.metadata.metadata_service import MetadataService
from gui.widgets.cards import Card, CardHeader, CardBody
from gui.widgets.inputs import TextField, TagEditor
from gui.widgets.buttons import PrimaryButton, SecondaryButton


class MetadataPage(QWidget):
    file_selected = Signal(FileInfo)
    log_message = Signal(str)

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

        self.copyright_field = TextField("Авторские права")
        body.add_widget(self.copyright_field)

        meta_card.add_widget(body)
        right_layout.addWidget(meta_card)

        # Чекбокс удаления оригиналов
        self.delete_original_cb = QCheckBox("Удалить оригиналы")
        right_layout.addWidget(self.delete_original_cb)

        self.action_btn = PrimaryButton("Записать метаданные")
        self.action_btn.setIcon(QIcon("assets/icons/save.svg"))
        self.action_btn.clicked.connect(self._process_files)
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

    def _process_files(self):
        """Обрабатывает выбранные файлы: запись метаданных и конвертация."""
        if not self.current_files:
            self.log("Нет файлов для обработки")
            return

        # Собираем теги из поля TagEditor
        keywords_text = self.keywords_field.toPlainText().strip()
        keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]

        # Собираем метаданные из полей
        metadata = {
            'title': self.title_field.text(),
            'subject': self.subject_field.text(),
            'artist': self.author_field.text(),
            'keywords': keywords,
            'comment': self.comment_field.text(),
            'copyright': self.copyright_field.text(),
        }

        # Проверяем, что хотя бы что-то заполнено
        has_data = any(v for v in metadata.values() if v)
        if not has_data:
            self.log("Заполните хотя бы одно поле метаданных")
            return

        delete_original = self.delete_original_cb.isChecked()
        folder_path = Path(self.folder_field.text())

        # Создаём папку Teggy для результатов
        output_folder = folder_path / "Teggy"
        output_folder.mkdir(exist_ok=True)

        self.log(f"Начинаем обработку {len(self.current_files)} файлов...")
        self.log(f"Результаты сохраняются в: {output_folder}")

        success_count = 0
        for file_info in self.current_files:
            src_path = file_info.path
            dst_path = output_folder / src_path.name

            try:
                shutil.copy2(src_path, dst_path)
            except Exception as e:
                self.log(f"Ошибка копирования {src_path.name}: {e}")
                continue

            result = MetadataService.process_file(
                str(dst_path),
                metadata,
                delete_original=delete_original
            )

            if result['success']:
                success_count += 1
                self.log(f"Обработан: {dst_path.name}")
            else:
                self.log(f"Ошибка: {dst_path.name} - {result['message']}")

        self.log(f"Готово. Обработано {success_count} из {len(self.current_files)} файлов")

    def log(self, message: str):
        """Отправляет сообщение в лог через сигнал."""
        self.log_message.emit(message)