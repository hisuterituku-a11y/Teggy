from pathlib import Path
from shutil import copy2

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QPixmap
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

from core.files.file_service import FileService
from core.tag_generator import TagGenerator
from core.worker_thread import ProcessingThread
from gui.dialogs.image_viewer import ImageViewerDialog


class ClickableThumbnailCard(QFrame):
    clicked = Signal(str)
    double_clicked = Signal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("ThumbnailCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

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
        self.metadata_fields: dict[str, QWidget] = {}
        self.processing_thread = None
        self.selected_card = None
        self.selected_photo_path = None
        self.last_output_dir: Path | None = None

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
            "Добавьте папки кнопкой или перетащите их прямо в это окно"
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

        self.drop_hint = QLabel("Перетащите папки сюда")
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

        title = QLabel("3. Куда сохранить результат")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self.replace_originals_checkbox = QCheckBox(
            "Заменить исходные фото готовыми"
        )
        self.replace_originals_checkbox.setToolTip(
            "Включено: исходные JPG будут протегированы на месте, а остальные "
            "форматы будут заменены JPG. Выключено: исходники сохранятся, "
            "готовые фото появятся в папке Teggy."
        )
        layout.addWidget(self.replace_originals_checkbox)

        explanation = QLabel(
            "Не включено: исходники останутся нетронутыми, готовые фото сохранятся "
            "в папку Teggy. Включено: готовые фото заменят исходные."
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

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(
            Path(url.toLocalFile()).exists() for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()
            self.drop_hint.setText("Отпускайте, папки не убегут")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.drop_hint.setText("Перетащите папки сюда")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        added = False
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            folder = path if path.is_dir() else path.parent
            if folder.exists() and str(folder) not in self.selected_folders:
                self.selected_folders.append(str(folder))
                added = True
        self.drop_hint.setText("Перетащите папки сюда")
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
        self.update_folder_list()

    def update_folder_list(self):
        while self.folder_container.count():
            item = self.folder_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for folder in self.selected_folders:
            files = FileService.get_files(Path(folder))
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

        self.update_gallery()

    def open_image_viewer(self, file_path: str):
        ImageViewerDialog(file_path=file_path, parent=self).exec()

    def _unique_target(self, output_dir: Path, source: Path) -> Path:
        target = output_dir / source.name
        counter = 2
        while target.exists():
            target = output_dir / f"{source.stem}_{counter}{source.suffix}"
            counter += 1
        return target

    def _prepare_processing_files(self, source_files: list[Path]) -> tuple[list[Path], Path | None]:
        if self.replace_originals_checkbox.isChecked():
            self.last_output_dir = None
            return source_files, None

        output_dir = Path(self.selected_folders[0]) / "Teggy"
        output_dir.mkdir(parents=True, exist_ok=True)
        prepared: list[Path] = []
        for source in source_files:
            target = self._unique_target(output_dir, source)
            copy2(source, target)
            prepared.append(target)
        self.last_output_dir = output_dir
        return prepared, output_dir

    def start_processing(self):
        if not self.selected_folders:
            QMessageBox.warning(self, "Папка не выбрана", "Сначала добавьте папку с фотографиями.")
            return

        source_files: list[Path] = []
        for folder in self.selected_folders:
            source_files.extend(Path(file_info.path) for file_info in FileService.get_files(Path(folder)))

        if not source_files:
            QMessageBox.warning(self, "Фотографии не найдены", "В выбранных папках нет поддерживаемых изображений.")
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
            QMessageBox.critical(self, "Не удалось подготовить файлы", str(error))
            return

        self.start_button.setEnabled(False)
        self.start_button.setText("Обработка…")

        self.processing_thread = ProcessingThread()
        self.processing_thread.setup(
            folder_path=self.selected_folders[0],
            file_list=files,
            metadata=metadata,
            tags=tags,
            delete_original=True,
            output_dir=str(output_dir) if output_dir else None,
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

        total = stats.get("total", 0)
        processed = stats.get("processed", 0)
        converted = stats.get("converted", 0)
        failed = stats.get("failed", 0)
        cancelled = stats.get("cancelled", False)

        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle("Обработка завершена")
        message.setText("Готово" if not cancelled else "Обработка отменена")
        message.setInformativeText(
            f"Всего файлов: {total}\n"
            f"Протегировано: {processed}\n"
            f"Преобразовано в JPG: {converted}\n"
            f"Ошибок: {failed}"
        )
        open_button = None
        if self.last_output_dir and self.last_output_dir.exists():
            open_button = message.addButton("Открыть папку Teggy", QMessageBox.ButtonRole.ActionRole)
        message.addButton("Закрыть", QMessageBox.ButtonRole.AcceptRole)
        message.exec()
        if open_button is not None and message.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output_dir)))

    def processing_failed(self, message):
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Запустить тегирование")
        QMessageBox.critical(self, "Ошибка обработки", str(message))

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

        files = []
        for folder in self.selected_folders:
            files.extend(FileService.get_files(Path(folder)))

        if not files:
            empty = QLabel("Фотографии появятся здесь")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gallery_grid.addWidget(empty, 0, 0, 1, 4)
            return

        columns = 5
        for visible_index, file_info in enumerate(files):
            file_path = Path(file_info.path)
            if not file_path.exists() or file_path.stat().st_size == 0:
                continue

            card = ClickableThumbnailCard(str(file_path))
            card.double_clicked.connect(self.open_image_viewer)
            card.clicked.connect(
                lambda path, current_card=card: self.select_thumbnail(current_card, path)
            )
            card.setFixedWidth(160)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(6)

            preview = QLabel()
            preview.setObjectName("ThumbnailImage")
            preview.setFixedSize(144, 105)
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                preview.setPixmap(
                    pixmap.scaled(
                        144,
                        105,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
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
