from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import TemplateError
from core.files.file_service import FileInfo, FileService
from core.paths import resource_path
from core.settings import Settings
from core.tag_generator import TagGenerator
from core.template_manager import TemplateManager
from core.worker_thread import ProcessingThread
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from gui.widgets.cards import PremiumCard
from gui.widgets.inputs import SearchField, TagEditor, TextField
from gui.widgets.section import Section
from gui.widgets.toolbar import Toolbar


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class MetadataPage(QWidget):
    file_selected = Signal(FileInfo)
    log_message = Signal(str)
    templates_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "MetadataPage")
        self.current_files: list[FileInfo] = []
        self.thread: ProcessingThread | None = None
        self._preview_source: QPixmap | None = None
        self._last_template = Settings.get_last_template()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addLayout(self._build_toolbar())

        self.workspace = QSplitter(Qt.Horizontal)
        self.workspace.setChildrenCollapsible(False)
        self.workspace.addWidget(self._build_file_browser())
        self.workspace.addWidget(self._build_preview_panel())
        self.workspace.addWidget(self._build_editor_panel())
        self.workspace.setStretchFactor(0, 0)
        self.workspace.setStretchFactor(1, 1)
        self.workspace.setStretchFactor(2, 0)
        self.workspace.setSizes([300, 620, 380])
        root.addWidget(self.workspace, stretch=1)

        root.addLayout(self._build_status_bar())

        self.delete_original_cb.setChecked(Settings.get_delete_original())
        self._refresh_templates()
        self._update_selection_label()
        self._update_action_state()

    def _build_toolbar(self) -> QVBoxLayout:
        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(10)

        toolbar = Toolbar(
            title="Метаданные",
            subtitle="Выбор файлов, предпросмотр и запись EXIF/IPTC-данных",
            compact=True,
        )

        self.browse_btn = SecondaryButton("Открыть папку")
        self.browse_btn.setIcon(QIcon(str(resource_path("assets/icons/folder-open.svg"))))
        self.browse_btn.clicked.connect(self._browse_folder)
        toolbar.add_action(self.browse_btn)

        self.select_all_btn = SecondaryButton("Выделить всё")
        self.select_all_btn.clicked.connect(self._select_all)
        toolbar.add_action(self.select_all_btn)

        self.deselect_all_btn = SecondaryButton("Снять")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        toolbar.add_action(self.deselect_all_btn)

        container.addWidget(toolbar)

        self.folder_field = TextField("Выберите папку с изображениями...")
        self.folder_field.setReadOnly(True)
        container.addWidget(self.folder_field)
        return container

    def _build_file_browser(self) -> QWidget:
        section = Section(
            "Файлы",
            "Выберите изображения для обработки",
            show_divider=False,
            spacing=8,
            content_spacing=8,
            variant="browser",
        )
        section.setProperty("class", "Section MetadataBrowser")
        section.setMinimumWidth(260)
        section.setMaximumWidth(380)

        self.browser_count = QLabel("0")
        self.browser_count.setProperty("class", "MutedLabel")
        section.add_action(self.browser_count)

        self.search_field = SearchField(placeholder="Поиск по имени...")
        self.search_field.textChanged.connect(self._apply_file_filter)
        section.add_widget(self.search_field)

        self.format_filter = QComboBox()
        self.format_filter.addItem("Все форматы", "")
        self.format_filter.currentIndexChanged.connect(self._apply_file_filter)
        section.add_widget(self.format_filter)

        self.file_list = QListWidget()
        self.file_list.setProperty("class", "FileList")
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setIconSize(QSize(56, 56))
        self.file_list.setSpacing(4)
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        section.add_widget(self.file_list, stretch=1)

        self.empty_list_label = QLabel("Откройте папку или перетащите изображения")
        self.empty_list_label.setProperty("class", "InspectorPlaceholder")
        self.empty_list_label.setAlignment(Qt.AlignCenter)
        self.empty_list_label.setWordWrap(True)
        section.add_widget(self.empty_list_label)
        return section

    def _build_preview_panel(self) -> QWidget:
        section = Section(
            "Предпросмотр",
            "Проверка выбранного изображения",
            show_divider=False,
            spacing=8,
            content_spacing=8,
            variant="preview",
        )
        section.setProperty("class", "Section MetadataPreview")
        section.content_layout().setContentsMargins(12, 0, 12, 0)

        # Сохраняем прежний публичный атрибут: остальная логика меняет его текст.
        self.preview_title = section.title_label()

        self.preview_position = QLabel("")
        self.preview_position.setProperty("class", "MutedLabel")
        section.add_action(self.preview_position)

        self.preview_label = QLabel("Выберите изображение")
        self.preview_label.setProperty("class", "ImagePreview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(360, 260)
        self.preview_label.setWordWrap(True)
        section.add_widget(self.preview_label, stretch=1)

        self.preview_info = QLabel("Файл не выбран")
        self.preview_info.setProperty("class", "MutedLabel")
        self.preview_info.setAlignment(Qt.AlignCenter)
        section.add_widget(self.preview_info)
        return section

    def _build_editor_panel(self) -> QWidget:
        section = Section(
            "Редактор",
            "Шаблоны и значения метаданных",
            show_divider=False,
            spacing=8,
            content_spacing=10,
            variant="editor",
        )
        section.setProperty("class", "Section MetadataEditor")
        section.setMinimumWidth(340)
        section.setMaximumWidth(430)

        template_row = QHBoxLayout()
        template_row.setContentsMargins(0, 0, 0, 0)
        template_row.setSpacing(8)

        self.template_combo = QComboBox()
        self.template_combo.setPlaceholderText("Выберите шаблон...")
        self.template_combo.currentTextChanged.connect(self._apply_template)
        template_row.addWidget(self.template_combo, stretch=1)

        self.save_template_btn = SecondaryButton("Сохранить")
        self.save_template_btn.clicked.connect(self._save_as_template)
        template_row.addWidget(self.save_template_btn)
        section.add_layout(template_row)

        meta_card = PremiumCard(
            title="Метаданные",
            subtitle="Заполняются для всех выбранных файлов",
            variant="metadata",
            compact=True,
        )

        self.title_field = TextField("Название")
        self.subject_field = TextField("Тема")
        self.author_field = TextField("Автор")
        self.comment_field = TextField("Комментарий")
        self.copyright_field = TextField("Авторские права")
        for field in (
            self.title_field,
            self.subject_field,
            self.author_field,
            self.comment_field,
            self.copyright_field,
        ):
            meta_card.add_widget(field)

        self.keywords_field = TagEditor()
        self.keywords_field.setPlaceholderText("Теги — по одному на строке")
        self.keywords_field.textChanged.connect(self._update_generate_button)
        meta_card.add_widget(self.keywords_field)

        self.generate_tags_btn = SecondaryButton("Сгенерировать SEO-теги")
        self.generate_tags_btn.setEnabled(False)
        self.generate_tags_btn.clicked.connect(self._generate_tags)
        meta_card.add_widget(self.generate_tags_btn)
        section.add_widget(meta_card, stretch=1)

        self.delete_original_cb = QCheckBox("Удалить исходные файлы после конвертации")
        section.add_widget(self.delete_original_cb)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        section.add_widget(self.progress_bar)

        self.action_btn = PrimaryButton("Записать метаданные")
        self.action_btn.setIcon(QIcon(str(resource_path("assets/icons/save.svg"))))
        self.action_btn.clicked.connect(self._start_processing)
        section.add_widget(self.action_btn)

        self.cancel_btn = SecondaryButton("Отменить обработку")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_processing)
        section.add_widget(self.cancel_btn)
        return section

    def _build_status_bar(self) -> QHBoxLayout:
        status = QHBoxLayout()
        self.selection_label = QLabel("Файлов: 0 · Выбрано: 0")
        self.selection_label.setProperty("class", "StatusLabel")
        status.addWidget(self.selection_label)
        status.addStretch()
        self.workspace_status = QLabel("Готов к работе")
        self.workspace_status.setProperty("class", "MutedLabel")
        status.addWidget(self.workspace_status)
        return status

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_preview()

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с фотографиями",
            Settings.get_last_folder() or "",
        )
        if folder:
            self.folder_field.setText(folder)
            Settings.save_last_folder(folder)
            self._load_files(folder)

    def _load_files(self, folder_path: str):
        files = FileService.get_files(Path(folder_path))
        self.current_files = files
        self.folder_field.setText(folder_path)
        self._populate_file_list(files)
        self._refresh_templates()
        self.log(f"Папка выбрана: {folder_path}")
        self.log(f"Найдено файлов: {len(files)}")

    def _populate_file_list(self, files: list[FileInfo]):
        self.file_list.clear()
        formats = set()
        for file_info in files:
            suffix = file_info.path.suffix.lower()
            formats.add(suffix)
            item = QListWidgetItem(file_info.name)
            item.setData(Qt.UserRole, file_info)
            item.setToolTip(str(file_info.path))
            pixmap = QPixmap(str(file_info.path))
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            self.file_list.addItem(item)

        current_filter = self.format_filter.currentData()
        self.format_filter.blockSignals(True)
        self.format_filter.clear()
        self.format_filter.addItem("Все форматы", "")
        for suffix in sorted(formats):
            self.format_filter.addItem(suffix.lstrip(".").upper(), suffix)
        index = self.format_filter.findData(current_filter)
        self.format_filter.setCurrentIndex(max(index, 0))
        self.format_filter.blockSignals(False)

        self.empty_list_label.setVisible(not files)
        self._apply_file_filter()
        self._update_selection_label()
        self._clear_preview()

    def _apply_file_filter(self):
        query = self.search_field.text().strip().lower()
        suffix = self.format_filter.currentData() or ""
        visible = 0
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            file_info = item.data(Qt.UserRole)
            matches_name = not query or query in item.text().lower()
            matches_format = not suffix or file_info.path.suffix.lower() == suffix
            hidden = not (matches_name and matches_format)
            item.setHidden(hidden)
            if not hidden:
                visible += 1
        self.browser_count.setText(str(visible))
        self.empty_list_label.setVisible(self.file_list.count() == 0)
        self._update_selection_label()

    def _on_selection_changed(self):
        selected = self.file_list.selectedItems()
        self._update_selection_label()
        self._update_action_state()
        if not selected:
            self._clear_preview()
            return

        item = selected[0]
        file_info = item.data(Qt.UserRole)
        if file_info:
            self.file_selected.emit(file_info)
            self._show_preview(file_info)

    def _show_preview(self, file_info: FileInfo):
        self._preview_source = QPixmap(str(file_info.path))
        self.preview_title.setText(file_info.name)
        try:
            index = self.current_files.index(file_info) + 1
            self.preview_position.setText(f"{index} / {len(self.current_files)}")
        except ValueError:
            self.preview_position.setText("")

        if self._preview_source.isNull():
            self.preview_label.setText("Предпросмотр этого формата недоступен")
            self.preview_label.setPixmap(QPixmap())
        else:
            self._render_preview()

        dimensions = ""
        if not self._preview_source.isNull():
            dimensions = f" · {self._preview_source.width()}×{self._preview_source.height()} px"
        self.preview_info.setText(
            f"{file_info.path.suffix.lstrip('.').upper()} · {self._human_size(file_info.size)}{dimensions}"
        )

    def _render_preview(self):
        if self._preview_source is None or self._preview_source.isNull():
            return
        target = self.preview_label.size() - QSize(24, 24)
        if target.width() <= 0 or target.height() <= 0:
            return
        self.preview_label.setText("")
        self.preview_label.setPixmap(
            self._preview_source.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _clear_preview(self):
        self._preview_source = None
        self.preview_title.setText("Предпросмотр")
        self.preview_position.setText("")
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Выберите изображение")
        self.preview_info.setText("Файл не выбран")

    @staticmethod
    def _human_size(size: int) -> str:
        if size < 1024:
            return f"{size} Б"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} КБ"
        return f"{size / (1024 * 1024):.1f} МБ"

    def log(self, message: str):
        self.log_message.emit(message)
        self.workspace_status.setText(message)

    def _refresh_templates(self):
        templates = TemplateManager.list_templates()
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        if templates:
            self.template_combo.addItems(sorted(templates))
        else:
            self.template_combo.addItem("Нет шаблонов")
        if self._last_template:
            index = self.template_combo.findText(self._last_template)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)
        self.template_combo.blockSignals(False)

    def _apply_template(self):
        template_name = self.template_combo.currentText()
        if not template_name or template_name == "Нет шаблонов":
            return
        try:
            data = TemplateManager.load(template_name)
            self.title_field.setText(data.get("title", ""))
            self.subject_field.setText(data.get("subject", ""))
            self.author_field.setText(data.get("artist", ""))
            keywords = data.get("keywords", [])
            self.keywords_field.setPlainText(
                "\n".join(keywords) if isinstance(keywords, list) else str(keywords or "")
            )
            self.comment_field.setText(data.get("comment", ""))
            self.copyright_field.setText(data.get("copyright", ""))
            Settings.save_last_template(template_name)
            self._last_template = template_name
            self.log(f"Шаблон '{template_name}' применён")
        except TemplateError as error:
            self.log(f"Ошибка загрузки шаблона: {error}")

    def _save_as_template(self):
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Сохранить шаблон", "Введите имя шаблона:")
        if not ok or not name.strip():
            return
        name = name.strip()
        keywords = [line.strip() for line in self.keywords_field.toPlainText().splitlines() if line.strip()]
        data = {
            "name": name,
            "title": self.title_field.text(),
            "subject": self.subject_field.text(),
            "artist": self.author_field.text(),
            "keywords": keywords,
            "comment": self.comment_field.text(),
            "copyright": self.copyright_field.text(),
        }
        try:
            TemplateManager.save(name, data)
            self._last_template = name
            self._refresh_templates()
            self.template_combo.setCurrentText(name)
            self.templates_updated.emit()
            self.log(f"Шаблон '{name}' сохранён")
        except TemplateError as error:
            self.log(f"Ошибка сохранения шаблона: {error}")

    def _start_processing(self):
        selected_files = [
            item.data(Qt.UserRole).path
            for item in self.file_list.selectedItems()
            if item.data(Qt.UserRole)
        ]
        if not selected_files:
            self.log("Нет выбранных файлов")
            return

        keywords = [line.strip() for line in self.keywords_field.toPlainText().splitlines() if line.strip()]
        metadata = {
            "title": self.title_field.text(),
            "subject": self.subject_field.text(),
            "artist": self.author_field.text(),
            "keywords": keywords,
            "comment": self.comment_field.text(),
            "copyright": self.copyright_field.text(),
        }
        if not any(metadata.values()):
            self.log("Заполните хотя бы одно поле метаданных")
            return

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
            quality=95,
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.log.connect(self.log)
        self.thread.finished.connect(self._on_finished)
        self.thread.error.connect(self._on_error)
        self.thread.start()
        self.log(f"Начинаем обработку {len(selected_files)} файлов...")

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(max(total, 1))
        self.progress_bar.setValue(current)
        self.workspace_status.setText(f"Обработка: {current} из {total}")

    def _on_finished(self, stats: dict):
        if stats.get("cancelled"):
            self.log("Обработка отменена")
        else:
            self.log(
                f"Готово. Обработано {stats.get('processed', 0)} из {stats.get('total', 0)} файлов"
            )
        self._reset_ui()

    def _on_error(self, message: str):
        self.log(f"Ошибка: {message}")
        self._reset_ui()

    def _cancel_processing(self):
        if self.thread and self.thread.isRunning():
            self.thread.cancel()
            self.log("Отмена обработки...")

    def _reset_ui(self):
        self.action_btn.setEnabled(bool(self.file_list.selectedItems()))
        self.browse_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.thread = None

    def _update_selection_label(self):
        total = self.file_list.count()
        visible = sum(not self.file_list.item(i).isHidden() for i in range(total))
        selected = len(self.file_list.selectedItems())
        self.selection_label.setText(f"Файлов: {total} · Показано: {visible} · Выбрано: {selected}")
        self.browser_count.setText(str(visible))

    def _update_action_state(self):
        running = bool(self.thread and self.thread.isRunning())
        self.action_btn.setEnabled(bool(self.file_list.selectedItems()) and not running)

    def _select_all(self):
        self.file_list.clearSelection()
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            if not item.isHidden():
                item.setSelected(True)
        self._update_selection_label()

    def _deselect_all(self):
        self.file_list.clearSelection()
        self._update_selection_label()

    def _select_files_by_names(self, names: list):
        wanted = set(names)
        self.file_list.clearSelection()
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            if item.text() in wanted:
                item.setSelected(True)
        self._update_selection_label()

    def load_files_from_paths(self, paths: list):
        files: list[FileInfo] = []
        for path_str in paths:
            path = Path(path_str)
            if not path.exists() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            stat = path.stat()
            files.append(
                FileInfo(
                    name=path.name,
                    path=path,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                )
            )
        self.current_files = files
        self._populate_file_list(files)
        if files:
            self.folder_field.setText(str(files[0].path.parent))
            for index in range(self.file_list.count()):
                self.file_list.item(index).setSelected(True)
        self.log(f"Загружено файлов: {len(files)}")

    def _update_generate_button(self):
        self.generate_tags_btn.setEnabled(bool(self.keywords_field.toPlainText().strip()))

    def _generate_tags(self):
        lines = [line.strip() for line in self.keywords_field.toPlainText().splitlines() if line.strip()]
        if not lines:
            self.log("Нет текста для генерации тегов")
            return
        tags = TagGenerator.generate_seo_tags(lines)
        self.keywords_field.setPlainText("\n".join(tags))
        self.log(f"Сгенерировано тегов: {len(tags)}")
