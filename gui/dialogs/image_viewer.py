from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ImageViewerDialog(QDialog):
    """
    Окно просмотра изображения внутри Teggy.
    """

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)

        # Путь к открываемому изображению.
        self.file_path = Path(file_path)

        # Оригинальный pixmap нужен для корректного
        # масштабирования при изменении размера окна.
        self.original_pixmap = QPixmap()

        self.setObjectName("ImageViewerDialog")
        self.setWindowTitle(self.file_path.name)
        self.setMinimumSize(800, 600)

        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        """
        Создаёт интерфейс просмотрщика.
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # -------------------------
        # Верхняя панель
        # -------------------------

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.file_name_label = QLabel(self.file_path.name)
        self.file_name_label.setObjectName("ViewerFileName")

        header_layout.addWidget(self.file_name_label)
        header_layout.addStretch()

        self.close_button = QPushButton("Закрыть")
        self.close_button.setObjectName("ViewerCloseButton")
        self.close_button.clicked.connect(self.close)

        header_layout.addWidget(self.close_button)

        main_layout.addLayout(header_layout)

        # -------------------------
        # Область изображения
        # -------------------------

        self.image_container = QFrame()
        self.image_container.setObjectName("ViewerImageContainer")

        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(12, 12, 12, 12)

        self.image_label = QLabel()
        self.image_label.setObjectName("ViewerImage")
        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setText("Загрузка изображения...")

        image_layout.addWidget(self.image_label)

        main_layout.addWidget(
            self.image_container,
            stretch=1
        )

        # -------------------------
        # Нижняя панель
        # -------------------------

        footer_layout = QHBoxLayout()

        self.image_info_label = QLabel()
        self.image_info_label.setObjectName("ViewerImageInfo")

        footer_layout.addWidget(self.image_info_label)
        footer_layout.addStretch()

        main_layout.addLayout(footer_layout)

    def load_image(self):
        """
        Загружает изображение с диска.
        """

        if not self.file_path.exists():
            self.show_error("Файл не найден")
            return

        pixmap = QPixmap(str(self.file_path))

        if pixmap.isNull():
            self.show_error(
                "Не удалось открыть изображение"
            )
            return

        # Сохраняем оригинальное изображение.
        self.original_pixmap = pixmap

        width = pixmap.width()
        height = pixmap.height()

        file_size_mb = (
            self.file_path.stat().st_size
            / 1024
            / 1024
        )

        self.image_info_label.setText(
            f"{width} × {height} px  •  "
            f"{file_size_mb:.2f} МБ"
        )

        self.update_scaled_image()

    def update_scaled_image(self):
        """
        Подгоняет изображение под размер окна,
        сохраняя пропорции.
        """

        if self.original_pixmap.isNull():
            return

        available_size = self.image_label.size()

        scaled_pixmap = self.original_pixmap.scaled(
            available_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """
        Перемасштабирует изображение
        при изменении размера окна.
        """

        super().resizeEvent(event)
        self.update_scaled_image()

    def show_error(self, message: str):
        """
        Показывает ошибку прямо в области изображения.
        """

        self.image_label.clear()
        self.image_label.setText(message)
        self.image_info_label.clear()