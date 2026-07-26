from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QTextEdit,
    QFileDialog,
    QScrollArea,
)
from pathlib import Path
from PySide6.QtGui import QPixmap
from core.worker_thread import ProcessingThread
from core.tag_generator import TagGenerator
from gui.dialogs.image_viewer import ImageViewerDialog

from core.files.file_service import FileService

class ClickableThumbnailCard(QFrame):
    """
    Карточка миниатюры фотографии.
    """

    clicked = Signal(str)
    double_clicked = Signal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)

        # Сохраняем путь к изображению.
        self.file_path = file_path

        self.setObjectName("ThumbnailCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """
        Обычный клик по карточке.
        """

        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Двойной клик открывает изображение.
        """

        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.file_path)

        super().mouseDoubleClickEvent(event)

class TaggingPage(QWidget):

    def choose_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с фотографиями"
        )


        if not folder:
            return


        files = FileService.get_files(
            Path(folder)
        )


        print(
            f"Найдено файлов: {len(files)}"
        )

    def add_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку"
        )


        if not folder:
            return


        if folder not in self.selected_folders:

            self.selected_folders.append(
                folder
            )


        self.update_folder_list()
    def remove_folder(self, folder):

        if folder in self.selected_folders:

            self.selected_folders.remove(
                folder
            )

        self.update_folder_list()
    def update_folder_list(self):

        # очищаем старые карточки

        while self.folder_container.count():

            item = self.folder_container.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()



        for folder in self.selected_folders:
            files = FileService.get_files(
                Path(folder)
            )

            count = len(files)
            card = QFrame()

            card.setObjectName(
                "FolderItem"
            )


            row = QHBoxLayout(
                card
            )


            row.setContentsMargins(
                12,
                8,
                12,
                8
            )


            folder_icon = QLabel()

            folder_icon.setPixmap(
                QPixmap(
                    "assets/icons/teggy/folder-open.svg"
                ).scaled(
                    22,
                    22,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )


            info = QLabel(
                f"{Path(folder).name}\n"
                f"{folder}\n\n"
                f"{count} изображений"
            )


            info.setObjectName(
                "FolderText"
            )


            row.addWidget(
                folder_icon
            )


            row.addWidget(
                info
            )


            row.addStretch()



            remove = QPushButton(
                "✕"
            )


            remove.setObjectName(
                "RemoveButton"
            )


            remove.clicked.connect(
                lambda checked=False, f=folder:
                self.remove_folder(f)
            )


            row.addWidget(
                remove
            )


            self.folder_container.addWidget(
                card
            )
        self.update_gallery()

    def open_image_viewer(self, file_path: str):
        """
        Открывает изображение в отдельном окне Teggy.
        """

        viewer = ImageViewerDialog(
            file_path=file_path,
            parent=self,
        )

        # exec() открывает модальное окно
        # и удерживает объект в памяти до закрытия.
        viewer.exec()

    def start_processing(self):

        if not self.selected_folders:
            print("Нет выбранных папок")
            return


        files = []

        for folder in self.selected_folders:

            result = FileService.get_files(
                Path(folder)
            )

            files.extend(
                [f.path for f in result]
            )


        if not files:
            print("Фото не найдены")
            return


        # временные теги
        raw_tags = """
    Стоматология
    Клиника
    """


        tags = TagGenerator.parse_tags_input(
            raw_tags
        )


        # собираем метаданные из формы
        metadata = {}

        for key, widget in self.metadata_fields.items():

            if key == "keywords":
                metadata[key] = widget.toPlainText()

            else:
                metadata[key] = widget.text()

        self.processing_thread = ProcessingThread()


        self.processing_thread.setup(
            folder_path=self.selected_folders[0],
            file_list=files,
            metadata=metadata,
            tags=tags
        )


        self.processing_thread.progress.connect(
            self.processing_progress
        )


        self.processing_thread.log.connect(
            print
        )


        self.processing_thread.finished.connect(
            self.processing_finished
        )


        self.processing_thread.error.connect(
            print
        )


        self.processing_thread.start()

    def processing_progress(self, current, total):

        print(
            f"{current}/{total}"
        )


    def processing_finished(self, stats):

        print(
            "Готово:",
            stats
        )
    def update_gallery(self):
        # После перестроения галереи старые карточки будут удалены,
        # поэтому сбрасываем сохранённый выбор.
        self.selected_card = None
        self.selected_photo_path = None

        # Галерея ещё не создана
        if not hasattr(self, "gallery_grid"):
            return

        # Очищаем старые миниатюры
        while self.gallery_grid.count():

            item = self.gallery_grid.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()


        files = []

        for folder in self.selected_folders:

            folder_files = FileService.get_files(
                Path(folder)
            )

            files.extend(
                folder_files
            )


        if not files:

            empty = QLabel(
                "Фотографии появятся здесь"
            )

            empty.setObjectName(
                "EmptyState"
            )

            empty.setAlignment(
                Qt.AlignCenter
            )

            self.gallery_grid.addWidget(
                empty,
                0,
                0,
                1,
                4
            )

            return


        columns = 5
        visible_index = 0

        for file_info in files:

            file_path = Path(file_info.path)

            if not file_path.exists() or file_path.stat().st_size == 0:
                continue


            # Создаём кликабельную карточку фотографии.
            card = ClickableThumbnailCard(
                str(file_path)
            )
            # Двойной клик открывает просмотрщик.
            card.double_clicked.connect(
                self.open_image_viewer
            )

            # Передаём клик в метод выбора фотографии.
            card.clicked.connect(
                lambda path, current_card=card:
                    self.select_thumbnail(current_card, path)
            )
            card.setFixedWidth(160)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(6)


            preview = QLabel()
            preview.setObjectName("ThumbnailImage")
            preview.setFixedSize(144, 105)
            preview.setAlignment(Qt.AlignCenter)


            pixmap = QPixmap(str(file_path))

            if not pixmap.isNull():

                preview.setPixmap(
                    pixmap.scaled(
                        144,
                        105,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
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

            self.gallery_grid.addWidget(
                card,
                row,
                column
            )

            visible_index += 1   

    def select_thumbnail(
        self,
        card: ClickableThumbnailCard,
        file_path: str
    ):
        """
        Выбирает карточку фотографии.

        Одновременно выбранной может быть только одна карточка.
        """

        # Если нажали на уже выбранную карточку,
        # оставляем её выбранной и ничего не меняем.
        if self.selected_card is card:
            return

        # Снимаем выделение с предыдущей карточки.
        if self.selected_card is not None:
            self.selected_card.setProperty(
                "selected",
                False
            )

            # Заставляем Qt заново применить QSS.
            self.selected_card.style().unpolish(
                self.selected_card
            )
            self.selected_card.style().polish(
                self.selected_card
            )
            self.selected_card.update()

        # Запоминаем новую выбранную карточку и путь.
        self.selected_card = card
        self.selected_photo_path = file_path

        # Устанавливаем свойство, используемое в style.qss.
        card.setProperty(
            "selected",
            True
        )

        # Обновляем внешний вид карточки.
        card.style().unpolish(card)
        card.style().polish(card)
        card.update()

        # Пока оставим для проверки.
        print(
            f"Выбрана фотография: {file_path}"
            )

    def __init__(self):

        super().__init__()
        self.selected_folders = []
        self.metadata_fields = {}
        self.processing_thread = None


        root = QVBoxLayout(
            self
        )


        root.setContentsMargins(
            32,
            24,
            32,
            24
        )


        root.setSpacing(
            18
        )


        # =========================
        # HEADER
        # =========================


        title = QLabel(
            "Тегирование"
        )

        title.setObjectName(
            "SectionTitle"
        )


        root.addWidget(
            title
        )
        # =========================
        # METADATA
        # =========================

        metadata_card = QFrame()

        metadata_card.setObjectName(
            "PhotoPanel"
        )


        metadata_layout = QVBoxLayout(
            metadata_card
        )


        metadata_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )


        metadata_title = QLabel(
            "Метаданные"
        )

        metadata_title.setObjectName(
            "CardTitle"
        )

        metadata_layout.addWidget(
            metadata_title
        )


        fields = [
            ("title", "Название"),
            ("subject", "Тема"),
            ("comment", "Комментарий"),
            ("artist", "Автор"),
            ("copyright", "Авторские права"),
            ("keywords", "Теги"),
        ]


        for key, label in fields:

            row = QHBoxLayout()

            name = QLabel(
                label
            )

            name.setFixedWidth(
                150
            )


            if key == "keywords":

                edit = QTextEdit()

                edit.setPlaceholderText(
                    "Введите теги по одному в строке"
                )

                edit.setMinimumHeight(
                    180
                )

            else:

                edit = QLineEdit()

                placeholders = {
                    "title": "Введите название",
                    "subject": "Введите тему",
                    "comment": "Введите комментарий",
                    "artist": "Введите автора",
                    "copyright": "Введите авторские права",
                }

                edit.setPlaceholderText(
                    placeholders.get(key, "")
                )


            self.metadata_fields[key] = edit


            row.addWidget(
                name
            )

            row.addWidget(
                edit
            )


            metadata_layout.addLayout(
                row
            )


        root.addWidget(
            metadata_card
        )
        # =========================
        # PROCESS BUTTON
        # =========================

        self.start_button = QPushButton(
            "▶ Запустить тегирование"
        )

        self.start_button.setObjectName(
            "PrimaryButton"
        )

        self.start_button.clicked.connect(
            self.start_processing
        )

        root.addWidget(
            self.start_button
        )

        subtitle = QLabel(
            "Подготовка изображений и запись метаданных"
        )

        subtitle.setObjectName(
            "CardSubtitle"
        )


        root.addWidget(
            subtitle
        )



        # =========================
        # UPLOAD CARD
        # =========================


        upload = QFrame()

        upload.setObjectName(
            "PhotoPanel"
        )


        upload_layout = QVBoxLayout(
            upload
        )


        upload_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )


        upload_layout.setSpacing(
            12
        )


        icon = QLabel()

        icon.setPixmap(
            QPixmap(
                "assets/icons/teggy/folder.svg"
            ).scaled(
                50,
                40,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        icon.setObjectName(
            "CardIcon"
        )


        upload_layout.addWidget(
            icon
        )



        # =========================
        # FOLDER MANAGER
        # =========================


        folder_card = QFrame()

        folder_card.setObjectName(
            "PhotoPanel"
        )


        folder_layout = QVBoxLayout(
            folder_card
        )


        folder_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )


        folder_layout.setSpacing(
            12
        )



        folder_title = QLabel(
            "Папки обработки"
        )

        folder_title.setObjectName(
            "CardTitle"
        )


        folder_layout.addWidget(
            folder_title
        )



        folder_text = QLabel(
            "Добавьте папки, фотографии из которых нужно обработать"
        )


        folder_text.setObjectName(
            "CardSubtitle"
        )


        folder_layout.addWidget(
            folder_text
        )



        self.folder_container = QVBoxLayout()

        folder_layout.addLayout(
            self.folder_container
        )


        button_row = QHBoxLayout()



        add_folder_button = QPushButton(
            "+ Добавить папки"
        )

        add_folder_button.setObjectName(
            "PrimaryButton"
        )

        add_folder_button.clicked.connect(
            self.add_folder
        )


        button_row.addWidget(
            add_folder_button
        )


        button_row.addStretch()



        folder_layout.addLayout(
            button_row
        )



        root.addWidget(
            folder_card
        )


        # =========================
        # GALLERY
        # =========================

        gallery = QFrame()

        gallery.setObjectName(
            "PhotoPanel"
        )


        gallery_layout = QVBoxLayout(
            gallery
        )

        gallery_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        gallery_layout.setSpacing(
            14
        )


        gallery_title = QLabel(
            "Фотографии"
        )

        gallery_title.setObjectName(
            "CardTitle"
        )

        gallery_layout.addWidget(
            gallery_title
        )


        self.gallery_scroll = QScrollArea()

        self.gallery_scroll.setObjectName(
            "GalleryScroll"
        )

        self.gallery_scroll.setWidgetResizable(
            True
        )

        self.gallery_scroll.setMinimumHeight(
            240
        )


        gallery_content = QWidget()

        gallery_content.setObjectName(
            "GalleryContent"
        )


        self.gallery_grid = QGridLayout(
            gallery_content
        )

        self.gallery_grid.setContentsMargins(
            4,
            4,
            4,
            4
        )

        self.gallery_grid.setHorizontalSpacing(
            12
        )

        self.gallery_grid.setVerticalSpacing(
            12
        )

        self.gallery_grid.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )


        self.gallery_scroll.setWidget(
            gallery_content
        )


        gallery_layout.addWidget(
            self.gallery_scroll
        )


        root.addWidget(
            gallery
        )


        self.update_gallery()


        root.addStretch()