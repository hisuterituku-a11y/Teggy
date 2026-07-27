from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.tag_generator import TagGenerator
from core.tag_template_store import TagTemplateStore
from core.worker_thread import ProcessingThread
from gui.dialogs.tag_template_dialog import TagTemplateDialog
from gui.pages.yandex_maps import YandexMapsPage as BaseYandexMapsPage


class YandexMapsPage(BaseYandexMapsPage):
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

    def __init__(self, parent=None):
        self._template_store = TagTemplateStore()
        self._download_snapshot: set[str] = set()
        self._selected_template_values: dict[str, str] | None = None
        self._tagging_thread: ProcessingThread | None = None
        super().__init__(parent)

    def setup_ui(self):
        super().setup_ui()
        self._install_template_option()

    def _install_template_option(self) -> None:
        options_layout = None
        for label in self.findChildren(QLabel):
            if label.text() == "Дополнительно":
                options_layout = label.parentWidget().layout()
                break
        if options_layout is None:
            return

        card = QFrame()
        card.setObjectName("DownloadOptionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.apply_template_checkbox = self._make_checkbox()
        header.addWidget(self.apply_template_checkbox)

        text_box = QVBoxLayout()
        title = QLabel("Применить шаблон метаданных")
        title.setObjectName("DownloadOptionTitle")
        description = QLabel(
            "После загрузки Teggy автоматически добавит теги и метаданные к скачанным фотографиям."
        )
        description.setObjectName("DownloadOptionDescription")
        description.setWordWrap(True)
        text_box.addWidget(title)
        text_box.addWidget(description)
        header.addLayout(text_box, 1)
        layout.addLayout(header)

        controls = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(36)
        self.template_combo.setObjectName("TemplateCombo")
        controls.addWidget(self.template_combo, 1)

        manage_button = QPushButton("Управление шаблонами")
        manage_button.setObjectName("YandexActionButton")
        manage_button.setMinimumHeight(36)
        manage_button.clicked.connect(self.open_template_manager)
        controls.addWidget(manage_button)
        layout.addLayout(controls)

        self.apply_template_checkbox.stateChanged.connect(
            lambda state: self._update_template_card(card, state)
        )
        options_layout.addWidget(card)
        self._refresh_template_combo()

    @staticmethod
    def _make_checkbox():
        from PySide6.QtWidgets import QCheckBox

        checkbox = QCheckBox()
        checkbox.setObjectName("DownloadOptionCheck")
        return checkbox

    def _update_template_card(self, card: QFrame, state: int) -> None:
        card.setProperty("selected", state == Qt.CheckState.Checked.value)
        card.style().unpolish(card)
        card.style().polish(card)
        card.update()

    def _refresh_template_combo(self, preferred: str | None = None) -> None:
        current = preferred or self.template_combo.currentText()
        names = self._template_store.names()
        self.template_combo.clear()
        if not names:
            self.template_combo.addItem("Шаблоны ещё не созданы")
            self.template_combo.setEnabled(False)
            self.apply_template_checkbox.setChecked(False)
            self.apply_template_checkbox.setEnabled(False)
            return
        self.template_combo.setEnabled(True)
        self.apply_template_checkbox.setEnabled(True)
        self.template_combo.addItems(names)
        index = self.template_combo.findText(current)
        if index >= 0:
            self.template_combo.setCurrentIndex(index)

    def open_template_manager(self) -> None:
        dialog = TagTemplateDialog(parent=self)
        dialog.templates_changed.connect(self._refresh_template_combo)
        dialog.template_applied.connect(self._select_applied_template)
        dialog.exec()
        self._refresh_template_combo()

    def _select_applied_template(self, values: dict) -> None:
        names = self._template_store.load()
        for name, stored_values in names.items():
            if stored_values == values:
                self._refresh_template_combo(name)
                self.apply_template_checkbox.setChecked(True)
                return

    def _image_paths(self) -> list[Path]:
        if self.output_folder is None:
            return []
        result: list[Path] = []
        try:
            for path in Path(self.output_folder).rglob("*"):
                if path.is_file() and path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    result.append(path)
        except OSError:
            return []
        return result

    @staticmethod
    def _path_key(path: Path) -> str:
        try:
            return str(path.resolve()).casefold()
        except OSError:
            return str(path.absolute()).casefold()

    def start_download(self):
        self._download_snapshot = {self._path_key(path) for path in self._image_paths()}
        self._selected_template_values = None
        if getattr(self, "apply_template_checkbox", None) is not None:
            if self.apply_template_checkbox.isChecked() and self.template_combo.isEnabled():
                self._selected_template_values = self._template_store.get(self.template_combo.currentText())
        super().start_download()
        if getattr(self, "apply_template_checkbox", None) is not None:
            self.apply_template_checkbox.setEnabled(False)
            self.template_combo.setEnabled(False)

    def on_download_finished(self, success: bool):
        super().on_download_finished(success)
        if getattr(self, "apply_template_checkbox", None) is not None:
            self._refresh_template_combo()

        if not success or not self._selected_template_values:
            return

        all_files = self._image_paths()
        new_files = [
            path for path in all_files
            if self._path_key(path) not in self._download_snapshot
        ]
        files = new_files or all_files
        if not files:
            self.append_download_log("Шаблон не применён: фотографии не найдены")
            return

        tags = TagGenerator.parse_tags_input(
            self._selected_template_values.get("keywords", "")
        )
        if not tags:
            self.append_download_log("Шаблон не применён: в нём нет тегов")
            return

        self.download_status.setText("Добавляем метаданные по шаблону…")
        self.download_progress.setVisible(True)
        self.append_download_log(
            f"Применяем шаблон к {len(files)} фотографиям"
        )

        metadata = dict(self._selected_template_values)
        self._tagging_thread = ProcessingThread(self)
        self._tagging_thread.setup(
            folder_path=str(self.output_folder),
            file_list=files,
            metadata=metadata,
            tags=tags,
            delete_original=False,
            output_dir=str(self.output_folder),
        )
        self._tagging_thread.progress.connect(
            lambda current, total: self.download_status.setText(
                f"Метаданные: {current} / {total}"
            )
        )
        self._tagging_thread.log.connect(self.append_download_log)
        self._tagging_thread.finished.connect(self._template_tagging_finished)
        self._tagging_thread.error.connect(self._template_tagging_failed)
        self._tagging_thread.start()

    def _template_tagging_finished(self, stats: dict) -> None:
        self.download_progress.setVisible(False)
        processed = int(stats.get("processed", 0))
        failed = int(stats.get("failed", 0))
        self.download_status.setText(
            f"Загрузка завершена, метаданные добавлены: {processed}"
        )
        if failed:
            self.append_download_log(f"Ошибок при добавлении метаданных: {failed}")
        self._tagging_thread = None

    def _template_tagging_failed(self, message: str) -> None:
        self.download_progress.setVisible(False)
        self.download_status.setText("Загрузка завершена, но шаблон применить не удалось")
        self.append_download_log(str(message))
        self._tagging_thread = None
