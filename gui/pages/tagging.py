from __future__ import annotations

import os
from pathlib import Path
from shutil import copy2, rmtree
from tempfile import mkdtemp

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
    QImageReader,
    QPixmap,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.converter import ImageConverter
from core.files.file_service import FileService
from core.tag_generator import TagGenerator
from core.worker_thread import ProcessingThread
from gui.dialogs.image_viewer import ImageViewerDialog
from gui.dialogs.processing_result_dialog import ProcessingResultDialog


class ClickableThumbnailCard(QFrame):
    clicked = Signal(str)
    double_clicked = Signal(str)
    remove_requested = Signal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("ThumbnailCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        self.remove_button = QPushButton("✕", self)
        self.remove_button.setObjectName("ThumbnailRemoveButton")
        self.remove_button.setFixedSize(26, 26)
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.hide()
        self.remove_button.clicked.connect(
            lambda checked=False: self.remove_requested.emit(self.file_path)
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        margin = 7
        self.remove_button.move(self.width() - self.remove_button.width() - margin, margin)
        self.remove_button.raise_()

    def enterEvent(self, event) -> None:
        self.remove_button.show()
        self.remove_button.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self.remove_button.underMouse():
            self.remove_button.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.file_path)
        super().mouseDoubleClickEvent(event)


class TaggingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.selected_folders: list[str] = []
        self.selected_files: list[Path] = []
        self.excluded_files: set[Path] = set()
        self.metadata_fields: dict[str, QWidget] = {}
        self.processing_thread = None
        self.selected_card = None
        self.selected_photo_path = None
        self.last_output_dir: Path | None = None
        self._replace_originals = False
        self._replacement_jobs: list[tuple[Path, Path]] = []
        self._temporary_output_dir: Path | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        title = QLabel("Тегирование")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "1. Выберите папки  ·  2. Заполните метаданные  ·  3. Запустите обработку"
        )
        subtitle.setObjectName("CardSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        root.addWidget(self._build_folder_card())
        root.addWidget(self._build_metadata_card())
        root.addWidget(self._build_processing_options())

        self.start_button = QPushButton("▶ Запустить тегирование")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.setMinimumHeight(38)
        self.start_button.clicked.connect(self.start_processing)
        root.addWidget(self.start_button)

        process_hint = QLabel(
            "PNG, WebP, BMP и TIFF автоматически преобразуются в JPG. "
            "Спрашивать разрешения у форматов никто не будет."
        )
        process_hint.setObjectName("CardSubtitle")
        process_hint.setWordWrap(True)
        root.addWidget(process_hint)

        root.addWidget(self._build_gallery_card())
        self.update_gallery()

    def _build_folder_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("1. Папки обработки")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        description = QLabel(
            "Добавьте папки кнопкой или перетащите папки и отдельные фотографии прямо в это окно"
        )
        description.setObjectName("CardSubtitle")
        description.setWordWrap(True)
        layout.addWidget(description)

        button_row = QHBoxLayout()
        self.add_folder_button = QPushButton("+ Добавить папки")
        self.add_folder_button.setObjectName("PrimaryButton")
        self.add_folder_button.setMinimumHeight(36)
        self.add_folder_button.clicked.connect(self.add_folder)
        button_row.addWidget(self.add_folder_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.drop_hint = QLabel("Перетащите папки или фото сюда")
        self.drop_hint.setObjectName("CardSubtitle")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setMinimumHeight(34)
        layout.addWidget(self.drop_hint)

        self.folder_container = QVBoxLayout()
        self.folder_container.setSpacing(8)
        layout.addLayout(self.folder_container)
        return card

    def _build_metadata_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QGridLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(6)
        layout.setColumnMinimumWidth(0, 140)
        layout.setColumnStretch(1, 1)

        title = QLabel("2. Метаданные")
        title.setObjectName("CardTitle")
        layout.addWidget(title, 0, 0, 1, 2)

        fields = [
            ("title", "Название", "Введите название"),
            ("subject", "Тема", "Введите тему"),
            ("comment", "Комментарий", "Введите комментарий"),
            ("artist", "Автор", "Введите автора"),
            ("copyright", "Авторские права", "Введите авторские права"),
            ("keywords", "Теги", "Введите теги по одному в строке"),
        ]

        for row_index, (key, label_text, placeholder) in enumerate(fields, start=1):
            label = QLabel(label_text)
            label.setFixedWidth(140)

            if key == "keywords":
                label.setAlignment(Qt.AlignmentFlag.AlignTop)
                edit = QTextEdit()
                edit.setFixedHeight(76)
            else:
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                edit = QLineEdit()
                edit.setFixedHeight(30)

            edit.setPlaceholderText(placeholder)
            edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.metadata_fields[key] = edit
            layout.addWidget(label, row_index, 0)
            layout.addWidget(edit, row_index, 1)

        return card

    def _build_processing_options(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(6)

        self.delete_originals_checkbox = QCheckBox(
            "Заменять исходные фото обработанными"
        )
        self.delete_originals_checkbox.setToolTip(
            "Если включено, Teggy сначала обрабатывает временную копию, а затем "
            "заменяет исходный файл только после успешной обработки."
        )
        layout.addWidget(self.delete_originals_checkbox)

        explanation = QLabel(
            "По умолчанию исходники сохраняются, а готовые фото появляются в папке Teggy. "
            "При включённой замене отдельная папка Teggy не создаётся: обработанные файлы "
            "заменяют исходники в выбранных папках."
        )
        explanation.setObjectName("CardSubtitle")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        return card

    def _build_gallery_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("Фотографии")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setObjectName("GalleryScroll")
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setMinimumHeight(240)

        gallery_content = QWidget()
        gallery_content.setObjectName("GalleryContent")
        self.gallery_grid = QGridLayout(gallery_content)
        self.gallery_grid.setContentsMargins(4, 4, 4, 4)
        self.gallery_grid.setHorizontalSpacing(12)
        self.gallery_grid.setVerticalSpacing(12)
        self.gallery_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.gallery_scroll.setWidget(gallery_content)
        layout.addWidget(self.gallery_scroll)
        return card

    def _valid_drop_paths(self, event) -> list[Path]:
        paths: list[Path] = []
        if not event.mimeData().hasUrls():
            return paths
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if not local_path:
                continue
            path = Path(local_path)
            try:
                if path.exists():
                    paths.append(path)
            except OSError:
                continue
        return paths

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._valid_drop_paths(event):
            event.acceptProposedAction()
            self.drop_hint.setText("Отпускайте, папки не убегут")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.drop_hint.setText("Перетащите папки или фото сюда")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        added = False
        for path in self._valid_drop_paths(event):
            if path.is_dir():
                folder = str(path)
                if folder not in self.selected_folders:
                    self.selected_folders.append(folder)
                    added = True
            elif FileService.is_image(path):
                resolved = path.resolve()
                if resolved not in self.selected_files:
                    self.selected_files.append(resolved)
                    self.excluded_files.discard(resolved)
                    added = True

        self.drop_hint.setText("Перетащите папки или фото сюда")
        if added:
            self.update_folder_list()
        event.acceptProposedAction()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder and folder not in self.selected_folders:
            self.selected_folders.append(folder)
            self.update_folder_list()

    def remove_folder(self, folder: str):
        if folder in self.selected_folders:
            self.selected_folders.remove(folder)
        folder_path = Path(folder)
        self.excluded_files = {
            path for path in self.excluded_files if path.parent != folder_path
        }
        self.update_folder_list()

    def update_folder_list(self):
        while self.folder_container.count():
            item = self.folder_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for folder in self.selected_folders:
            files = self._files_from_folder(Path(folder))
            card = QFrame()
            card.setObjectName("FolderItem")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 8, 12, 8)
            row.setSpacing(10)

            icon = QLabel()
            pixmap = QPixmap("assets/icons/teggy/folder-open.svg")
            if not pixmap.isNull():
                icon.setPixmap(
                    pixmap.scaled(
                        22,
                        22,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            row.addWidget(icon)

            info = QLabel(f"{Path(folder).name}\n{folder}\n{len(files)} изображений")
            info.setObjectName("FolderText")
            info.setWordWrap(True)
            row.addWidget(info, 1)

            remove = QPushButton("✕")
            remove.setObjectName("RemoveButton")
            remove.clicked.connect(lambda checked=False, f=folder: self.remove_folder(f))
            row.addWidget(remove)
            self.folder_container.addWidget(card)

        if self.selected_files:
            card = QFrame()
            card.setObjectName("FolderItem")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 8, 12, 8)
            info = QLabel(f"Отдельные фотографии\n{len(self.selected_files)} файлов")
            info.setObjectName("FolderText")
            row.addWidget(info, 1)
            clear_button = QPushButton("Очистить")
            clear_button.setObjectName("RemoveButton")
            clear_button.clicked.connect(self._clear_selected_files)
            row.addWidget(clear_button)
            self.folder_container.addWidget(card)

        self.update_gallery()

    def _clear_selected_files(self) -> None:
        self.selected_files.clear()
        self.update_folder_list()

    def _files_from_folder(self, folder: Path) -> list[Path]:
        return [
            Path(file_info.path).resolve()
            for file_info in FileService.get_files(folder)
            if Path(file_info.path).resolve() not in self.excluded_files
        ]

    def _collect_source_files(self) -> list[Path]:
        files: list[Path] = []
        seen: set[Path] = set()

        for folder in self.selected_folders:
            for path in self._files_from_folder(Path(folder)):
                if path not in seen:
                    files.append(path)
                    seen.add(path)

        for path in self.selected_files:
            resolved = path.resolve()
            if resolved.exists() and resolved not in self.excluded_files and resolved not in seen:
                files.append(resolved)
                seen.add(resolved)

        return files

    def remove_photo(self, file_path: str) -> None:
        path = Path(file_path).resolve()
        self.selected_files = [item for item in self.selected_files if item.resolve() != path]
        self.excluded_files.add(path)
        if self.selected_photo_path == str(path):
            self.selected_photo_path = None
            self.selected_card = None
        self.update_folder_list()

    def open_image_viewer(self, file_path: str):
        ImageViewerDialog(file_path=file_path, parent=self).exec()

    def _unique_target(self, output_dir: Path, source: Path) -> Path:
        target = output_dir / source.name
        counter = 2
        while target.exists():
            target = output_dir / f"{source.stem}_{counter}{source.suffix}"
            counter += 1
        return target

    def _cleanup_temporary_output(self) -> None:
        temporary_dir = self._temporary_output_dir
        self._temporary_output_dir = None
        if temporary_dir is not None:
            rmtree(temporary_dir, ignore_errors=True)

    def _prepare_processing_files(self, source_files: list[Path]) -> tuple[list[Path], Path]:
        self._cleanup_temporary_output()
        self._replacement_jobs = []
        self._replace_originals = self.delete_originals_checkbox.isChecked()

        if self._replace_originals:
            output_dir = Path(mkdtemp(prefix="teggy-tagging-"))
            self._temporary_output_dir = output_dir
            prepared: list[Path] = []
            for index, source in enumerate(source_files, start=1):
                target = output_dir / f"{index:06d}{source.suffix.lower()}"
                copy2(source, target)
                prepared.append(target)
                self._replacement_jobs.append((source, target))
            self.last_output_dir = source_files[0].parent
            return prepared, output_dir

        base_folder = Path(self.selected_folders[0]) if self.selected_folders else source_files[0].parent
        output_dir = base_folder / "Teggy"
        output_dir.mkdir(parents=True, exist_ok=True)

        prepared = []
        for source in source_files:
            target = self._unique_target(output_dir, source)
            copy2(source, target)
            prepared.append(target)

        self.last_output_dir = output_dir
        return prepared, output_dir

    def _replace_processed_sources(self) -> list[str]:
        errors: list[str] = []
        updated_selected_files: dict[Path, Path] = {}

        for source, prepared in self._replacement_jobs:
            converted = ImageConverter.needs_conversion(source)
            processed = prepared.with_suffix(".jpg") if converted else prepared
            destination = source.with_suffix(".jpg") if converted else source

            try:
                if not processed.is_file() or processed.stat().st_size == 0:
                    raise OSError("обработанный файл не создан")
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(processed, destination)
                if destination.resolve() != source.resolve():
                    source.unlink(missing_ok=True)
                updated_selected_files[source.resolve()] = destination.resolve()
            except OSError as error:
                errors.append(f"{source}: {error}")

        if updated_selected_files:
            self.selected_files = [
                updated_selected_files.get(path.resolve(), path)
                for path in self.selected_files
                if updated_selected_files.get(path.resolve(), path).exists()
            ]
        return errors

    def start_processing(self):
        source_files = self._collect_source_files()
        if not source_files:
            QMessageBox.warning(
                self,
                "Фотографии не найдены",
                "Добавьте папку или отдельные фотографии для обработки.",
            )
            return

        raw_tags = self.metadata_fields["keywords"].toPlainText()
        tags = TagGenerator.parse_tags_input(raw_tags)
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
            self._cleanup_temporary_output()
            QMessageBox.critical(self, "Не удалось подготовить файлы", str(error))
            return

        self.start_button.setEnabled(False)
        self.start_button.setText("Обработка…")

        self.processing_thread = ProcessingThread()
        self.processing_thread.setup(
            folder_path=str(source_files[0].parent),
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

    def processing_progress(self, current, total):
        self.start_button.setText(f"Обработка: {current} / {total}")

    def processing_finished(self, stats):
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Запустить тегирование")

        failed = stats.get("failed", 0)
        cancelled = stats.get("cancelled", False)
        processed = stats.get("processed", 0)
        total = stats.get("total", 0)

        replacement_errors: list[str] = []
        if self._replace_originals and not cancelled and failed == 0 and processed == total:
            replacement_errors = self._replace_processed_sources()
            failed += len(replacement_errors)

        self._cleanup_temporary_output()
        self._replacement_jobs = []

        if replacement_errors:
            QMessageBox.critical(
                self,
                "Не удалось заменить часть исходников",
                "\n".join(replacement_errors[:10]),
            )

        ProcessingResultDialog(
            total=total,
            processed=processed,
            converted=stats.get("converted", 0),
            failed=failed,
            output_dir=self.last_output_dir,
            cancelled=cancelled,
            parent=self,
        ).exec()

        self.update_folder_list()

    def processing_failed(self, message):
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Запустить тегирование")
        self._cleanup_temporary_output()
        self._replacement_jobs = []
        QMessageBox.critical(self, "Ошибка обработки", str(message))

    def _load_thumbnail(self, file_path: Path, target_size: QSize) -> QPixmap:
        reader = QImageReader(str(file_path))
        reader.setAutoTransform(True)
        source_size = reader.size()
        if source_size.isValid():
            scaled_size = source_size.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            reader.setScaledSize(scaled_size)
        image = reader.read()
        if image.isNull():
            return QPixmap()
        return QPixmap.fromImage(image)

    def update_gallery(self):
        self.selected_card = None
        self.selected_photo_path = None
        if not hasattr(self, "gallery_grid"):
            return

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

        columns = 5
        visible_index = 0
        preview_size = QSize(144, 105)

        for file_path in files:
            if not file_path.exists() or file_path.stat().st_size == 0:
                continue

            card = ClickableThumbnailCard(str(file_path))
            card.double_clicked.connect(self.open_image_viewer)
            card.remove_requested.connect(self.remove_photo)
            card.clicked.connect(
                lambda path, current_card=card: self.select_thumbnail(current_card, path)
            )
            card.setFixedWidth(160)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(6)

            preview = QLabel()
            preview.setObjectName("ThumbnailImage")
            preview.setFixedSize(preview_size)
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setScaledContents(False)

            pixmap = self._load_thumbnail(file_path, preview_size)
            if not pixmap.isNull():
                preview.setPixmap(pixmap)
            else:
                preview.setText("Нет превью")

            filename = QLabel(file_path.name)
            filename.setObjectName("ThumbnailName")
            filename.setWordWrap(True)
            filename.setToolTip(str(file_path))
            card_layout.addWidget(preview)
            card_layout.addWidget(filename)

            row = visible_index // columns
            column = visible_index % columns
            self.gallery_grid.addWidget(card, row, column)
            visible_index += 1

    def select_thumbnail(self, card: ClickableThumbnailCard, file_path: str):
        if self.selected_card is card:
            return
        if self.selected_card is not None:
            self.selected_card.setProperty("selected", False)
            self.selected_card.style().unpolish(self.selected_card)
            self.selected_card.style().polish(self.selected_card)
            self.selected_card.update()

        self.selected_card = card
        self.selected_photo_path = file_path
        card.setProperty("selected", True)
        card.style().unpolish(card)
        card.style().polish(card)
        card.update()
