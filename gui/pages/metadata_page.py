from core.paths import resource_path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QCheckBox, QLabel, QComboBox, QProgressBar, 
    QAbstractItemView, QStyledItemDelegate, QStyle
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from pathlib import Path
import shutil
from datetime import datetime

from core.files.file_service import FileService, FileInfo
from core.metadata.metadata_service import MetadataService
import piexif
from gui.widgets.cards import Card, CardHeader, CardBody
from gui.widgets.inputs import TextField, TagEditor
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from core.template_manager import TemplateManager
from core.exceptions import TemplateError
from core.worker_thread import ProcessingThread
from core.settings import Settings
from core.tag_generator import TagGenerator


class MetadataPage(QWidget):
    file_selected = Signal(FileInfo)
    log_message = Signal(str)
    templates_updated = Signal() 

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
        self.browse_btn.setIcon(QIcon(str(resource_path("assets/icons/folder-open.svg"))))
        folder_row.addWidget(self.browse_btn)

        folder_card.add_layout(folder_row)
        left_layout.addWidget(folder_card)

        # Список файлов
        self.file_list = QListWidget()
        from PySide6.QtGui import QPalette, QColor

       
        
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setProperty("class", "FileList")
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.file_list)
        
        

        # Строка состояния и кнопки выделения
        selection_layout = QHBoxLayout()
        
        self.selection_label = QLabel("Файлов: 0, Выбрано: 0")
        selection_layout.addWidget(self.selection_label)
        selection_layout.addStretch()
        
        self.select_all_btn = SecondaryButton("Выделить всё")
        self.select_all_btn.clicked.connect(self._select_all)
        selection_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = SecondaryButton("Снять выделение")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        selection_layout.addWidget(self.deselect_all_btn)
        
        left_layout.addLayout(selection_layout)

        main_layout.addWidget(left_panel, stretch=1)

        # Правая колонка
        right_panel = QWidget()
        right_panel.setFixedWidth(380)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Блок шаблонов (над карточкой)
        template_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.setPlaceholderText("Выберите шаблон...")
        self.template_combo.currentTextChanged.connect(self._apply_template)
        template_layout.addWidget(self.template_combo)

        self.save_template_btn = SecondaryButton("Сохранить как шаблон")
        self.save_template_btn.clicked.connect(self._save_as_template)
        template_layout.addWidget(self.save_template_btn)

        right_layout.addLayout(template_layout)

        # Карточка "Метаданные"
        meta_card = Card()
        header = CardHeader()
        header.set_title("Метаданные")
        meta_card.add_widget(header)

        body = CardBody()
        self.title_field = TextField("Название")
        body.add_widget(self.title_field)

        self.subject_field = TextField("Тема")
        body.add_widget(self.subject_field)

        self.comment_field = TextField("Комментарий")
        body.add_widget(self.comment_field)

        self.author_field = TextField("Автор")
        body.add_widget(self.author_field)

        self.copyright_field = TextField("Авторские права")
        body.add_widget(self.copyright_field)

        meta_card.add_widget(body)
        right_layout.addWidget(meta_card)

        # Блок тегов (внутри карточки, но вне body)
        self.keywords_field = TagEditor()
        self.keywords_field.setPlaceholderText("Введите теги (по одному на строке)")
        self.keywords_field.textChanged.connect(self._update_generate_button)
        meta_card.add_widget(self.keywords_field)

        self.generate_tags_btn = SecondaryButton("Сделать теги")
        self.generate_tags_btn.setEnabled(False)
        self.generate_tags_btn.clicked.connect(self._generate_tags)
        self.generate_tags_btn.setFixedHeight(40)
        meta_card.add_widget(self.generate_tags_btn)

        # Чекбокс удаления оригиналов
        self.delete_original_cb = QCheckBox("Удалить оригиналы")
        right_layout.addWidget(self.delete_original_cb)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        self.action_btn = PrimaryButton("Записать метаданные")
        self.action_btn.setIcon(QIcon(str(resource_path("assets/icons/save.svg"))))
        self.action_btn.clicked.connect(self._start_processing)
        right_layout.addWidget(self.action_btn)

        self.cancel_btn = SecondaryButton("Отмена")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_processing)
        right_layout.addWidget(self.cancel_btn)

        right_layout.addStretch()

        main_layout.addWidget(right_panel)

        # Подключаем сигналы
        self.browse_btn.clicked.connect(self._browse_folder)

        # ===== ВОССТАНОВЛЕНИЕ СОСТОЯНИЯ =====
        # Восстанавливаем состояние чекбокса "Удалить оригиналы"
        self.delete_original_cb.setChecked(Settings.get_delete_original())

        # Сохраняем последний шаблон для восстановления после загрузки списка
        self._last_template = Settings.get_last_template()

    def _browse_folder(self):
        from PySide6.QtWidgets import QFileDialog
        from core.settings import Settings

        # Начальная папка — последняя открытая
        initial_dir = Settings.get_last_folder() or ""

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с фотографиями",
            initial_dir
        )

        if folder:
            self.folder_field.setText(folder)
            Settings.save_last_folder(folder) 
            self._load_files(folder)
            self._refresh_templates()

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
        self._refresh_templates()
        self._update_selection_label()

    def _on_selection_changed(self):
        self._update_selection_label()
        selected = self.file_list.selectedItems()
       
        if not selected:
            return

        item = selected[0]
        file_info = item.data(Qt.UserRole)
        if file_info:
            self.file_selected.emit(file_info)

    def log(self, message: str):
        """Отправляет сообщение в лог через сигнал."""
        self.log_message.emit(message)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

    def _refresh_templates(self):
        """Обновляет список шаблонов в выпадающем списке."""
        templates = TemplateManager.list_templates()
        self.template_combo.clear()
        if templates:
            self.template_combo.addItems(sorted(templates))
        else:
            self.template_combo.addItem("Нет шаблонов")
        
        # Восстанавливаем последний выбранный шаблон
        if hasattr(self, '_last_template') and self._last_template:
            index = self.template_combo.findText(self._last_template)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

    def _apply_template(self):
        """Применяет выбранный шаблон к полям."""
        template_name = self.template_combo.currentText()
        if not template_name or template_name == "Нет шаблонов":
            self.log("Нет шаблонов для применения")
            return

        try:
            data = TemplateManager.load(template_name)
            self.title_field.setText(data.get('title', ''))
            self.subject_field.setText(data.get('subject', ''))
            self.author_field.setText(data.get('artist', ''))
            self.keywords_field.setPlainText('\n'.join(data.get('keywords', [])) if isinstance(data.get('keywords'), list) else data.get('keywords', ''))
            self.comment_field.setText(data.get('comment', ''))
            self.copyright_field.setText(data.get('copyright', ''))
            self.log(f"Шаблон '{template_name}' применён")
            
            # Сохраняем последний выбранный шаблон
            Settings.save_last_template(template_name)
        except TemplateError as e:
            self.log(f"Ошибка загрузки шаблона: {e}")

    def _save_as_template(self):
        self.templates_updated.emit()
        """Сохраняет текущие поля как шаблон."""
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Сохранить шаблон", "Введите имя шаблона:")
        if not ok or not name.strip():
            return

        name = name.strip()
        keywords_text = self.keywords_field.toPlainText().strip()
        keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]

        data = {
            'name': name,
            'title': self.title_field.text(),
            'subject': self.subject_field.text(),
            'artist': self.author_field.text(),
            'keywords': keywords,
            'comment': self.comment_field.text(),
            'copyright': self.copyright_field.text(),
        }

        try:
            TemplateManager.save(name, data)
            self.log(f"Шаблон '{name}' сохранён")
            self._refresh_templates()
            index = self.template_combo.findText(name)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)
        except TemplateError as e:
            self.log(f"Ошибка сохранения шаблона: {e}")

    def _start_processing(self):
        """Запускает обработку в отдельном потоке."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.log("Нет выбранных файлов")
            return

        selected_files = []
        for item in selected_items:
            file_info = item.data(Qt.UserRole)
            if file_info:
                selected_files.append(file_info.path)

        if not selected_files:
            self.log("Нет файлов для обработки")
            return

        keywords_text = self.keywords_field.toPlainText().strip()
        keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]

        metadata = {
            'title': self.title_field.text(),
            'subject': self.subject_field.text(),
            'artist': self.author_field.text(),
            'keywords': keywords,
            'comment': self.comment_field.text(),
            'copyright': self.copyright_field.text(),
        }

        has_data = any(v for v in metadata.values() if v)
        if not has_data:
            self.log("Заполните хотя бы одно поле метаданных")
            return

        self._selected_files = selected_files

        self.action_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = ProcessingThread()
        self.thread.setup(
            folder_path=self.folder_field.text(),
            file_list=selected_files,
            metadata=metadata,
            tags=keywords,
            delete_original=self.delete_original_cb.isChecked(),
            quality=95
        )

        self.thread.progress.connect(self._on_progress)
        self.thread.log.connect(self.log)
        self.thread.finished.connect(self._on_finished)
        self.thread.error.connect(self._on_error)
        print("=== METADATA DEBUG ===")
        print(f"Title: {self.title_field.text()}")
        print(f"Subject: {self.subject_field.text()}")
        self.thread.start()
        self.log(f"⏳ Начинаем обработку {len(selected_files)} выбранных файлов...")

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_finished(self, stats: dict):
        if stats.get('cancelled'):
            self.log("⏹️ Обработка отменена")
        else:
            self.log(f"✅ Готово. Обработано {stats.get('processed', 0)} из {stats.get('total', 0)} файлов")
        self._reset_ui()

    def _on_error(self, message: str):
        self.log(f"❌ Ошибка: {message}")
        self._reset_ui()

    def _cancel_processing(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.cancel()
            self.log("⏹️ Отмена обработки...")

    def _reset_ui(self):
        self.action_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.thread = None

    def _update_selection_label(self):
        total = self.file_list.count()
        selected = len(self.file_list.selectedItems())
        self.selection_label.setText(f"Файлов: {total}, Выбрано: {selected}")

    def _select_all(self):
        self.file_list.selectAll()
        self._update_selection_label()

    def _deselect_all(self):
        self.file_list.clearSelection()
        self._update_selection_label()

    def _select_files_by_names(self, names: list):
        """Выделяет файлы по списку имён."""
        self.file_list.clearSelection()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.text() in names:
                item.setSelected(True)
        self._update_selection_label()

    def load_files_from_paths(self, paths: list):
        """Загружает список файлов по путям."""
        self.current_files = []
        self.file_list.clear()
        
        for path_str in paths:
            path = Path(path_str)
            stat = path.stat()
            file_info = FileInfo(
                name=path.name,
                path=path,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime)
            )
            self.current_files.append(file_info)
            
            item = QListWidgetItem(file_info.name)
            item.setData(Qt.UserRole, file_info)
            self.file_list.addItem(item)
        
        for i in range(self.file_list.count()):
            self.file_list.item(i).setSelected(True)
        
        self._update_selection_label()
        self.folder_field.setText(str(Path(paths[0]).parent))
        self.log(f"Загружено файлов: {len(paths)}")
    def _update_generate_button(self):
        """Обновляет состояние кнопки 'Сделать теги'."""
        self.generate_tags_btn.setEnabled(
            bool(self.keywords_field.toPlainText().strip())
        )

    def _generate_tags(self):
        """Генерирует теги в формате 'русский;translit'."""
        text = self.keywords_field.toPlainText().strip()
        if not text:
            self.log_message.emit("Нет текста для генерации тегов")
            return
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            self.log_message.emit("Нет строк для генерации")
            return
        
        from core.tag_generator import TagGenerator
        tags = TagGenerator.generate_seo_tags(lines)
        
        # Сохраняем позицию курсора
        cursor = self.keywords_field.textCursor()
        self.keywords_field.setPlainText('\n'.join(tags))
        self.keywords_field.setTextCursor(cursor)
        
        self.log_message.emit(f"Сгенерировано тегов: {len(tags)}")

