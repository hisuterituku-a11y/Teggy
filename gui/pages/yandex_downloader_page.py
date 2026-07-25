from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from core.yandex.service import YandexService
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from gui.widgets.cards import PremiumCard
from gui.widgets.inputs import TextField
from gui.widgets.log_widget import LogWidget
from gui.widgets.section import Section
from gui.widgets.toolbar import Toolbar


class YandexDownloaderPage(QWidget):
    """Страница импорта фотографий из Яндекс Карт."""

    log_message = Signal(str)
    progress_message = Signal(str)
    import_finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "YandexDownloaderPage")

        self.service = YandexService()
        self.import_running = False

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_settings_section())
        root.addWidget(self._build_progress_section())
        root.addWidget(self._build_log_section(), stretch=1)

        self.log_message.connect(self.log_widget.info, Qt.QueuedConnection)
        self.progress_message.connect(self._update_progress, Qt.QueuedConnection)
        self.import_finished.connect(self._on_import_finished, Qt.QueuedConnection)

    def _build_toolbar(self) -> Toolbar:
        toolbar = Toolbar(
            title="Импорт из Яндекс Карт",
            subtitle="Скачивание фотографий организации и отзывов по ссылке Яндекс Карт",
        )

        self.start_btn = PrimaryButton("Скачать")
        self.start_btn.clicked.connect(self._start_import)

        self.cancel_btn = SecondaryButton("Отмена")
        self.cancel_btn.clicked.connect(self._cancel_import)
        self.cancel_btn.setEnabled(False)

        toolbar.add_actions(self.cancel_btn, self.start_btn)
        return toolbar

    def _build_settings_section(self) -> Section:
        section = Section(
            "Настройки импорта",
            "Укажите ссылку на организацию и папку для сохранения фотографий",
        )

        card = PremiumCard(variant="default", compact=False)

        url_row = QWidget()
        url_layout = QHBoxLayout(url_row)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(12)

        url_label = QLabel("Ссылка:")
        url_label.setProperty("class", "FieldLabel")
        url_label.setFixedWidth(150)

        self.url_input = TextField("https://yandex.ru/maps/org/...")

        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input, stretch=1)
        card.add_widget(url_row)

        folder_row = QWidget()
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(12)

        folder_label = QLabel("Папка:")
        folder_label.setProperty("class", "FieldLabel")
        folder_label.setFixedWidth(150)

        self.folder_input = TextField("Выберите папку...")
        self.folder_input.setReadOnly(True)

        self.folder_browse_btn = SecondaryButton("Обзор")
        self.folder_browse_btn.clicked.connect(self._browse_folder)

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input, stretch=1)
        folder_layout.addWidget(self.folder_browse_btn)
        card.add_widget(folder_row)

        self.skip_existing_cb = QCheckBox("Не скачивать существующие файлы")
        self.skip_existing_cb.setChecked(True)
        card.add_widget(self.skip_existing_cb)

        section.add_widget(card)
        return section

    def _build_progress_section(self) -> Section:
        section = Section(
            "Состояние импорта",
            "Текущий этап загрузки и обработки фотографий",
            show_divider=False,
            variant="compact",
        )

        status_card = PremiumCard(variant="muted", compact=True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        status_card.add_widget(self.progress_bar)

        self.status_label = QLabel("Готов к работе")
        self.status_label.setProperty("class", "StatusLabel")
        self.status_label.setWordWrap(True)
        status_card.add_widget(self.status_label)

        section.add_widget(status_card)
        return section

    def _build_log_section(self) -> Section:
        section = Section(
            "Лог",
            "Сообщения загрузчика и результаты выполнения",
            show_divider=True,
        )

        self.log_widget = LogWidget()
        section.add_widget(self.log_widget, stretch=1)
        return section

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.folder_input.setText(folder)
            self.folder_input.clear_state()

    def _start_import(self):
        if self.import_running:
            return

        url = self.url_input.text().strip()
        if not url:
            self.url_input.set_error("Введите ссылку Яндекс Карт")
            self.log_message.emit("Введите ссылку Яндекс Карт")
            return
        self.url_input.clear_state()

        folder_text = self.folder_input.text().strip()
        save_dir = Path(folder_text) if folder_text else Path()
        if not folder_text or not save_dir.exists() or not save_dir.is_dir():
            self.folder_input.set_error("Выберите существующую папку сохранения")
            self.log_message.emit("Выберите папку сохранения")
            return
        self.folder_input.clear_state()

        self.import_running = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.folder_browse_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.folder_input.setEnabled(False)
        self.skip_existing_cb.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Запуск...")

        try:
            self.service.start(
                url=url,
                save_dir=save_dir,
                on_log=self.log_message.emit,
                on_progress=self.progress_message.emit,
                on_finished=self.import_finished.emit,
                skip_existing=self.skip_existing_cb.isChecked(),
            )
        except Exception as error:
            self.log_message.emit(f"Ошибка запуска: {error}")
            self._reset_ui()

    @Slot(str)
    def _update_progress(self, text: str):
        self.status_label.setText(text)

    @Slot(bool)
    def _on_import_finished(self, success: bool):
        if success:
            self.log_message.emit("Импорт Яндекс завершён")
        else:
            self.log_message.emit("Импорт Яндекс завершился с ошибкой")
        self._reset_ui()

    def _cancel_import(self):
        if not self.import_running:
            return

        try:
            self.service.cancel()
            self.log_message.emit("Отмена импорта...")
            self.status_label.setText("Отмена...")
            self.cancel_btn.setEnabled(False)
        except Exception as error:
            self.log_message.emit(f"Ошибка отмены: {error}")

    def _reset_ui(self):
        self.import_running = False
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.folder_browse_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        self.folder_input.setEnabled(True)
        self.skip_existing_cb.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Готов к работе")
