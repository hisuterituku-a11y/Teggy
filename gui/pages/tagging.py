from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QFileDialog,
)
from pathlib import Path
from PySide6.QtGui import QPixmap


from core.files.file_service import FileService

from PySide6.QtGui import QPixmap
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
class PhotoPage(QWidget):

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
    def __init__(self):

        super().__init__()
        self.selected_folders = []


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
            "Фото"
        )

        title.setObjectName(
            "SectionTitle"
        )


        root.addWidget(
            title
        )


        subtitle = QLabel(
            "Загрузка и подготовка изображений для AI-тегов"
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


        gallery_title = QLabel(
            "Галерея"
        )

        gallery_title.setObjectName(
            "CardTitle"
        )


        gallery_layout.addWidget(
            gallery_title
        )



        empty = QLabel(
            "Фотографии появятся здесь"
        )


        empty.setObjectName(
            "EmptyState"
        )


        empty.setAlignment(
            Qt.AlignCenter
        )


        gallery_layout.addWidget(
            empty
        )



        root.addWidget(
            gallery
        )


        root.addStretch()