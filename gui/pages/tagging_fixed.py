from __future__ import annotations

from pathlib import Path
from shutil import copy2

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImageReader, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from core.files.file_service import FileService
from core.tag_generator import TagGenerator
from core.worker_thread import ProcessingThread
from gui.dialogs.processing_result_dialog import ProcessingResultDialog
from gui.pages.tagging import ClickableThumbnailCard, TaggingPage as BaseTaggingPage


class TaggingPage(BaseTaggingPage):
    GALLERY_BATCH_SIZE = 20

    def __init__(self, parent=None):
        self.selected_files: list[str] = []
        self._pending_source_deletion: list[Path] = []
        self._gallery_generation = 0
        super().__init__(parent)

        for label in self.findChildren(QLabel):
            if label.text() == "3. Куда сохранить результат":
                label.hide()

        old_checkbox = self.delete_originals_checkbox
        old_checkbox.setText("Удалять исходные фото после обработки")
        old_checkbox.setObjectName("")
        old_checkbox.setToolTip(
            "Без галочки исходники сохранятся, готовые фото появятся в папке Teggy. "
            "С галочкой исходники удалятся только после полностью успешной обработки."
        )
        self.delete_sources_checkbox: QCheckBox = old_checkbox

        for label in self.findChildren(QLabel):
            if label.text().startswith("Не включено: исходники"):
                label.setText(
                    "Без галочки исходники сохраняются. С галочкой они удаляются "
                    "только после успешной обработки всех выбранных файлов."
                )

        self.drop_hint.setText("Перетащите папки или фото сюда")

    def _valid_local_paths(self, event) -> list[Path]:
        if not event.mimeData().hasUrls():
            return []
        result: list[Path] = []
        for url in event.mimeData().urls():
            local_file = url.toLocalFile()
            if not local_file:
                continue
            path = Path(local_file)
            if not path.exists():
                continue
            if path.is_dir() or (path.is_file() and FileService.is_image(path)):
                result.append(path)
        return result

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._valid_local_paths(event):
            event.acceptProposedAction()
            self.drop_hint.setText("Отпускайте, папки не убегут")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.drop_hint.setText("Перетащите папки или фото сюда")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._valid_local_paths(event)
        self.drop_hint.setText("Перетащите папки или фото сюда")
        if not paths:
            event.ignore()
            return

        changed = False
        for path in paths:
            if path.is_dir():
                value = str(path)
                if value not in self.selected_folders:
                    self.selected_folders.append(value)
                    changed = True
            else:
                value = str(path)
                if value not in self.selected_files:
                    self.selected_files.append(value)
                    changed = True

        if changed:
            QTimer.singleShot(0, self.update_folder_list)
        event.acceptProposedAction()

    def remove_file(self, file_path: str) -> None:
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
        QTimer.singleShot(0, self.update_folder_list)

    def update_folder_list(self) -> None:
        while self.folder_container.count():
            item = self.folder_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for folder in self.selected_folders:
            files = FileService.get_files(Path(folder))
            self.folder_container.addWidget(
                self._source_card(
                    "📁",
                    Path(folder).name,
                    f"{folder}\n{len(files)} изображений",
                    lambda checked=False, value=folder: self.remove_folder(value),
                )
            )

        for file_path in self.selected_files:
            path = Path(file_path)
            self.folder_container.addWidget(
                self._source_card(
                    "🖼",
                    path.name,
                    str(path.parent),
                    lambda checked=False, value=file_path: self.remove_file(value),
                )
            )

        self.update_gallery()

    @staticmethod
    def _source_card(icon_text: str, title: str, details: str, callback) -> QFrame:
        card = QFrame()
        card.setObjectName("FolderItem")
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(10)

        icon = QLabel(icon_text)
        icon.setFixedWidth(24)
        row.addWidget(icon)

        info = QLabel(f"{title}\n{details}")
        info.setObjectName("FolderText")
        info.setWordWrap(True)
        row.addWidget(info, 1)

        remove = QPushButton("✕")
        remove.setObjectName("RemoveButton")
        remove.clicked.connect(callback)
        row.addWidget(remove)
        return card

    def _collect_source_files(self) -> list[Path]:
        result: list[Path] = []
        seen: set[str] = set()

        for folder in self.selected_folders:
            for file_info in FileService.get_files(Path(folder)):
                path = Path(file_info.path)
                key = str(path.resolve()).casefold()
                if key not in seen:
                    seen.add(key)
                    result.append(path)

        for value in self.selected_files:
            path = Path(value)
            if not path.exists() or not FileService.is_image(path):
                continue
            key = str(path.resolve()).casefold()
            if key not in seen:
                seen.add(key)
                result.append(path)

        return result

    def _prepare_processing_files(self, source_files: list[Path]) -> tuple[list[Path], Path]:
        base = Path(self.selected_folders[0]) if self.selected_folders else source_files[0].parent
        output_dir = base / "Teggy"
        output_dir.mkdir(parents=True, exist_ok=True)

        prepared: list[Path] = []
        for source in source_files:
            target = self._unique_target(output_dir, source)
            copy2(source, target)
            prepared.append(target)
        self.last_output_dir = output_dir
        return prepared, output_dir

    def start_processing(self) -> None:
        source_files = self._collect_source_files()
        if not source_files:
            QMessageBox.warning(self, "Фото не выбраны", "Добавьте папку или отдельные фотографии.")
            return

        tags = TagGenerator.parse_tags_input(self.metadata_fields["keywords"].toPlainText())
        if not tags:
            QMessageBox.warning(self, "Теги не заполнены", "Добавьте хотя бы один тег.")
            return

        metadata = {
            key: widget.toPlainText() if key == "keywords" else widget.text()
            for key, widget in self.metadata_fields.items()
        }
        try:
            files, output_dir = self._prepare_processing_files(source_files)
        except OSError as error:
            QMessageBox.critical(self, "Не удалось подготовить файлы", str(error))
            return

        self._pending_source_deletion = (
            source_files if self.delete_sources_checkbox.isChecked() else []
        )
        self.start_button.setEnabled(False)
        self.start_button.setText("Обработка…")

        self.processing_thread = ProcessingThread()
        self.processing_thread.setup(
            folder_path=str(output_dir),
            file_list=files,
            metadata=metadata,
            tags=tags,
            delete_original=True,
            output_dir=str(output_dir),
        )
        self.processing_thread.progress.connect(self.processing_progress)
        self.processing_thread.log.connect(print)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_failed)
        self.processing_thread.start()

    def processing_finished(self, stats: dict) -> None:
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Запустить тегирование")

        total = int(stats.get("total", 0))
        processed = int(stats.get("processed", 0))
        failed = int(stats.get("failed", 0))
        cancelled = bool(stats.get("cancelled", False))

        if self._pending_source_deletion and not cancelled and failed == 0 and processed == total:
            for source in self._pending_source_deletion:
                try:
                    if source.exists():
                        source.unlink()
                except OSError:
                    failed += 1
        self._pending_source_deletion = []

        ProcessingResultDialog(
            total=total,
            processed=processed,
            converted=int(stats.get("converted", 0)),
            failed=failed,
            output_dir=self.last_output_dir,
            cancelled=cancelled,
            parent=self,
        ).exec()

    def processing_failed(self, message: str) -> None:
        self._pending_source_deletion = []
        super().processing_failed(message)

    def update_gallery(self) -> None:
        self.selected_card = None
        self.selected_photo_path = None
        self._gallery_generation += 1
        generation = self._gallery_generation

        while self.gallery_grid.count():
            item = self.gallery_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        files = self._collect_source_files()
        if not files:
            empty = QLabel("Фотографии появятся здесь")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gallery_grid.addWidget(empty, 0, 0, 1, 4)
            return
        self._append_gallery_batch(files, 0, generation)

    def _append_gallery_batch(self, files: list[Path], start: int, generation: int) -> None:
        if generation != self._gallery_generation:
            return
        end = min(start + self.GALLERY_BATCH_SIZE, len(files))
        for index in range(start, end):
            path = files[index]
            if path.exists() and path.stat().st_size:
                self.gallery_grid.addWidget(
                    self._thumbnail_card(path), index // 5, index % 5
                )
        if end < len(files):
            QTimer.singleShot(
                0, lambda: self._append_gallery_batch(files, end, generation)
            )

    def _thumbnail_card(self, file_path: Path) -> ClickableThumbnailCard:
        card = ClickableThumbnailCard(str(file_path))
        card.double_clicked.connect(self.open_image_viewer)
        card.clicked.connect(
            lambda path, current_card=card: self.select_thumbnail(current_card, path)
        )
        card.setFixedWidth(160)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        preview = QLabel()
        preview.setObjectName("ThumbnailImage")
        preview.setFixedSize(144, 105)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reader = QImageReader(str(file_path))
        reader.setAutoTransform(True)
        reader.setScaledSize(QSize(144, 105))
        image = reader.read()
        if image.isNull():
            preview.setText("Нет превью")
        else:
            preview.setPixmap(QPixmap.fromImage(image))

        name = QLabel(file_path.name)
        name.setObjectName("ThumbnailName")
        name.setWordWrap(True)
        name.setToolTip(str(file_path))
        layout.addWidget(preview)
        layout.addWidget(name)
        return card