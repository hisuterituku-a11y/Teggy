import threading
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QSpinBox, QProgressBar
)
from PySide6.QtCore import Signal, Qt
from pathlib import Path

from core.photo_import import PhotoImportService, SourceType, ImportProgress
from gui.widgets.cards import Card, CardHeader, CardBody
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from gui.widgets.log_widget import LogWidget


class YandexDownloaderPage(QWidget):
    log_message = Signal(str)
    progress_updated = Signal(ImportProgress)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setProperty("class", "YandexDownloaderPage")
        self.service = PhotoImportService()
        self.current_task_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Заголовок
        title = QLabel("Импорт из Яндекс Карт")
        title.setProperty("class", "PageTitle")
        layout.addWidget(title)

        # Карточка
        card = Card()
        header = CardHeader()
        header.set_title("Настройки")
        card.add_widget(header)

        body = CardBody()

        # URL
        url_widget = QWidget()
        url_layout = QHBoxLayout(url_widget)
        url_label = QLabel("Ссылка на карточку:")
        url_label.setFixedWidth(150)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://yandex.ru/maps/org/...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        body.add_widget(url_widget)

        # Папка
        folder_widget = QWidget()
        folder_layout = QHBoxLayout(folder_widget)
        folder_label = QLabel("Папка сохранения:")
        folder_label.setFixedWidth(150)
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Выберите папку...")
        self.folder_input.setReadOnly(True)
        self.folder_browse_btn = SecondaryButton("Обзор")
        self.folder_browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_browse_btn)
        body.add_widget(folder_widget)

        # Максимум
        max_widget = QWidget()
        max_layout = QHBoxLayout(max_widget)
        max_label = QLabel("Максимум фото:")
        max_label.setFixedWidth(150)
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 500)
        self.max_spin.setValue(100)
        max_layout.addWidget(max_label)
        max_layout.addWidget(self.max_spin)
        max_layout.addStretch()
        body.add_widget(max_widget)

        # Чекбокс
        self.skip_existing_cb = QCheckBox("Не скачивать существующие")
        self.skip_existing_cb.setChecked(True)
        body.add_widget(self.skip_existing_cb)

        card.add_widget(body)
        layout.addWidget(card)

        # Кнопка
        self.start_btn = PrimaryButton("Скачать")
        self.start_btn.clicked.connect(self._start_import)
        layout.addWidget(self.start_btn)

        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setProperty("class", "StatusLabel")
        layout.addWidget(self.status_label)

        # Лог
        log_card = Card()
        log_header = CardHeader()
        log_header.set_title("Лог")
        log_card.add_widget(log_header)
        log_body = CardBody()
        self.log_widget = LogWidget()
        log_body.add_widget(self.log_widget)
        log_card.add_widget(log_body)
        layout.addWidget(log_card)

        self.log_message.connect(self.log_widget.info)
        self.progress_updated.connect(
            self._update_progress,
            Qt.QueuedConnection
        )
       

    def _browse_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder:
            self.folder_input.setText(folder)

    def _start_import(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_message.emit("Введите ссылку на карточку Яндекс Карт")
            return

        save_dir = Path(self.folder_input.text())
        if not save_dir.exists():
            self.log_message.emit("Выберите существующую папку для сохранения")
            return

        
        skip_existing = self.skip_existing_cb.isChecked()

        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Импорт запущен...")

        try:
            self.current_task_id = self.service.start_import(
                url=url,
                save_dir=save_dir,
                source_type=SourceType.YANDEX,
                skip_existing=skip_existing,
                on_progress=self._on_progress,
                on_log=self.log_message.emit
            )
        except Exception as e:
            self.log_message.emit(f"Ошибка: {e}")
            self._reset_ui()

    def _on_progress(self, progress: ImportProgress):
        
        self.progress_updated.emit(progress)
       
        self.progress_bar.setValue(int(progress.percent))
        self.status_label.setText(
            f"Скачано: {progress.downloaded}/{progress.total} | "
            f"Ошибок: {progress.failed} | Пропущено: {progress.skipped}"
        )

        if progress.status.value in ("success", "failed", "cancelled"):
            self._reset_ui()

    def _reset_ui(self):
        self.start_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Готов к работе")

    def _update_progress(self, progress: ImportProgress):
        
        self.progress_bar.setValue(int(progress.percent))
        self.status_label.setText(
            f"Скачано: {progress.downloaded}/{progress.total} | "
            f"Ошибок: {progress.failed} | Пропущено: {progress.skipped}"
        )