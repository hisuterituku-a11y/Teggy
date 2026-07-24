from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.yandex.service import YandexService
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from gui.widgets.cards import Card, CardBody, CardHeader
from gui.widgets.log_widget import LogWidget


class YandexDownloaderPage(QWidget):
    """Downloader 2.0 — импорт фотографий из Яндекс Карт."""

    log_message = Signal(str)
    progress_message = Signal(str)
    import_finished = Signal(bool)
    import_context_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "YandexDownloaderPage DownloaderWorkspace")

        self.service = YandexService()
        self.import_running = False
        self._last_status = "Готов к работе"

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(self._build_header())

        self.workspace = QSplitter(Qt.Horizontal)
        self.workspace.setProperty("class", "DownloaderSplitter")
        self.workspace.setChildrenCollapsible(False)
        self.workspace.addWidget(self._build_settings_panel())
        self.workspace.addWidget(self._build_activity_panel())
        self.workspace.setStretchFactor(0, 1)
        self.workspace.setStretchFactor(1, 2)
        self.workspace.setSizes([390, 720])
        root.addWidget(self.workspace, stretch=1)

        root.addWidget(self._build_status_bar())

        self.log_message.connect(self.log_widget.info, Qt.QueuedConnection)
        self.progress_message.connect(self._update_progress, Qt.QueuedConnection)
        self.import_finished.connect(self._on_import_finished, Qt.QueuedConnection)

        self.url_input.textChanged.connect(self._on_form_changed)
        self.folder_input.textChanged.connect(self._on_form_changed)
        self.skip_existing_cb.toggled.connect(self._emit_context)
        self._on_form_changed()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setProperty("class", "DownloaderWorkspaceHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        title = QLabel("Downloader 2.0")
        title.setProperty("class", "PageTitle")
        text_box.addWidget(title)

        subtitle = QLabel("Импортируйте фотографии организаций из Яндекс Карт")
        subtitle.setProperty("class", "PageSubtitle")
        text_box.addWidget(subtitle)

        layout.addLayout(text_box)
        layout.addStretch()

        self.open_folder_btn = SecondaryButton("Открыть папку")
        self.open_folder_btn.clicked.connect(self._open_target_folder)
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)
        return header

    def _build_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setProperty("class", "DownloaderSettingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        source_card = Card()
        source_header = CardHeader()
        source_header.set_title("Источник")
        source_card.add_widget(source_header)

        source_body = CardBody()

        source_hint = QLabel(
            "Вставьте ссылку на организацию или подборку организаций в Яндекс Картах."
        )
        source_hint.setWordWrap(True)
        source_hint.setProperty("class", "DownloaderHint")
        source_body.add_widget(source_hint)

        self.url_input = QLineEdit()
        self.url_input.setProperty("class", "DownloaderUrlInput")
        self.url_input.setPlaceholderText("https://yandex.ru/maps/org/...")
        self.url_input.setClearButtonEnabled(True)
        source_body.add_widget(self.url_input)

        self.url_state_label = QLabel("Ссылка не указана")
        self.url_state_label.setProperty("class", "DownloaderValidationText")
        source_body.add_widget(self.url_state_label)

        source_card.add_widget(source_body)
        layout.addWidget(source_card)

        destination_card = Card()
        destination_header = CardHeader()
        destination_header.set_title("Сохранение")
        destination_card.add_widget(destination_header)

        destination_body = CardBody()

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)

        self.folder_input = QLineEdit()
        self.folder_input.setProperty("class", "DownloaderFolderInput")
        self.folder_input.setPlaceholderText("Выберите папку для фотографий...")
        self.folder_input.setReadOnly(True)
        folder_row.addWidget(self.folder_input, stretch=1)

        self.folder_browse_btn = SecondaryButton("Обзор")
        self.folder_browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folder_browse_btn)
        destination_body.add_layout(folder_row)

        self.folder_state_label = QLabel("Папка не выбрана")
        self.folder_state_label.setProperty("class", "DownloaderValidationText")
        destination_body.add_widget(self.folder_state_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setProperty("class", "DownloaderSeparator")
        destination_body.add_widget(separator)

        self.skip_existing_cb = QCheckBox("Пропускать уже скачанные файлы")
        self.skip_existing_cb.setChecked(True)
        destination_body.add_widget(self.skip_existing_cb)

        option_hint = QLabel(
            "Рекомендуется оставить включённым при повторном импорте в ту же папку."
        )
        option_hint.setWordWrap(True)
        option_hint.setProperty("class", "DownloaderHint")
        destination_body.add_widget(option_hint)

        destination_card.add_widget(destination_body)
        layout.addWidget(destination_card)
        layout.addStretch()

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.cancel_btn = SecondaryButton("Отмена")
        self.cancel_btn.clicked.connect(self._cancel_import)
        self.cancel_btn.setEnabled(False)
        action_row.addWidget(self.cancel_btn)

        self.start_btn = PrimaryButton("Начать импорт")
        self.start_btn.clicked.connect(self._start_import)
        action_row.addWidget(self.start_btn, stretch=1)

        layout.addLayout(action_row)
        return panel

    def _build_activity_panel(self) -> QWidget:
        panel = QWidget()
        panel.setProperty("class", "DownloaderActivityPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        activity_card = Card()
        activity_header = CardHeader()
        activity_header.set_title("Ход импорта")
        activity_card.add_widget(activity_header)

        activity_body = CardBody()

        self.activity_title = QLabel("Ожидание запуска")
        self.activity_title.setProperty("class", "DownloaderActivityTitle")
        activity_body.add_widget(self.activity_title)

        self.activity_description = QLabel(
            "После запуска здесь будет отображаться текущий этап загрузки."
        )
        self.activity_description.setWordWrap(True)
        self.activity_description.setProperty("class", "DownloaderHint")
        activity_body.add_widget(self.activity_description)

        self.progress_bar = QProgressBar()
        self.progress_bar.setProperty("class", "DownloaderProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        activity_body.add_widget(self.progress_bar)

        self.status_label = QLabel("Готов к работе")
        self.status_label.setProperty("class", "StatusLabel DownloaderStatusLabel")
        self.status_label.setWordWrap(True)
        activity_body.add_widget(self.status_label)

        activity_card.add_widget(activity_body)
        layout.addWidget(activity_card)

        log_card = Card()
        log_header = CardHeader()
        log_header.set_title("Журнал")
        log_card.add_widget(log_header)

        log_body = CardBody()
        self.log_widget = LogWidget()
        log_body.add_widget(self.log_widget)
        log_card.add_widget(log_body)
        layout.addWidget(log_card, stretch=1)
        return panel

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setProperty("class", "DownloaderStatusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)

        self.form_status_label = QLabel("Заполните ссылку и выберите папку")
        self.form_status_label.setProperty("class", "DownloaderFormStatus")
        layout.addWidget(self.form_status_label)
        layout.addStretch()

        self.mode_label = QLabel("Режим: безопасный импорт")
        self.mode_label.setProperty("class", "DownloaderModeLabel")
        layout.addWidget(self.mode_label)
        return bar

    def _browse_folder(self) -> None:
        initial = self.folder_input.text().strip()
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения",
            initial,
        )
        if folder:
            self.folder_input.setText(folder)
            self.log_message.emit(f"Папка сохранения: {folder}")

    def _open_target_folder(self) -> None:
        folder = Path(self.folder_input.text().strip())
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _is_valid_yandex_url(self, value: str) -> bool:
        value = value.strip().lower()
        return value.startswith(("https://yandex.ru/maps/", "https://yandex.com/maps/", "https://maps.yandex.ru/"))

    def _on_form_changed(self, *_args) -> None:
        url = self.url_input.text().strip()
        folder_text = self.folder_input.text().strip()
        folder = Path(folder_text) if folder_text else None

        url_valid = self._is_valid_yandex_url(url)
        folder_valid = bool(folder and folder.exists() and folder.is_dir())

        self.url_state_label.setText(
            "Ссылка распознана" if url_valid else "Укажите корректную ссылку Яндекс Карт"
        )
        self.url_state_label.setProperty("state", "valid" if url_valid else "invalid")

        self.folder_state_label.setText(
            f"Папка доступна: {folder}" if folder_valid else "Выберите существующую папку"
        )
        self.folder_state_label.setProperty("state", "valid" if folder_valid else "invalid")

        self.open_folder_btn.setEnabled(folder_valid)
        self.start_btn.setEnabled(url_valid and folder_valid and not self.import_running)

        if url_valid and folder_valid:
            self.form_status_label.setText("Готово к запуску")
        elif not url_valid and not folder_valid:
            self.form_status_label.setText("Заполните ссылку и выберите папку")
        elif not url_valid:
            self.form_status_label.setText("Осталось указать ссылку")
        else:
            self.form_status_label.setText("Осталось выбрать папку")

        for widget in (self.url_state_label, self.folder_state_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self._emit_context()

    def _emit_context(self, *_args) -> None:
        self.import_context_changed.emit(
            {
                "url": self.url_input.text().strip(),
                "folder": self.folder_input.text().strip(),
                "skip_existing": self.skip_existing_cb.isChecked(),
                "running": self.import_running,
                "status": self._last_status,
            }
        )

    def _start_import(self) -> None:
        if self.import_running:
            return

        url = self.url_input.text().strip()
        folder_text = self.folder_input.text().strip()
        save_dir = Path(folder_text) if folder_text else None

        if not self._is_valid_yandex_url(url):
            self.log_message.emit("Введите корректную ссылку Яндекс Карт")
            self.url_input.setFocus()
            return

        if save_dir is None or not save_dir.exists() or not save_dir.is_dir():
            self.log_message.emit("Выберите существующую папку сохранения")
            return

        self.import_running = True
        self._set_running_state(True)
        self._update_progress("Подготовка к импорту...")
        self.log_message.emit("Запуск импорта из Яндекс Карт")

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

    def _set_running_state(self, running: bool) -> None:
        self.import_running = running
        self.url_input.setEnabled(not running)
        self.folder_input.setEnabled(not running)
        self.folder_browse_btn.setEnabled(not running)
        self.skip_existing_cb.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        self.progress_bar.setVisible(running)
        self.activity_title.setText("Импорт выполняется" if running else "Ожидание запуска")
        self._on_form_changed()

    @Slot(str)
    def _update_progress(self, text: str) -> None:
        self._last_status = text or "Импорт выполняется"
        self.status_label.setText(self._last_status)
        self.activity_description.setText(self._last_status)
        self._emit_context()

    @Slot(bool)
    def _on_import_finished(self, success: bool) -> None:
        if success:
            self.log_message.emit("Импорт Яндекс завершён")
            self._last_status = "Импорт успешно завершён"
            self.activity_title.setText("Импорт завершён")
            self.activity_description.setText(
                "Фотографии сохранены. Папку можно открыть кнопкой в верхней панели."
            )
        else:
            self.log_message.emit("Импорт Яндекс завершился с ошибкой")
            self._last_status = "Импорт завершился с ошибкой"
            self.activity_title.setText("Ошибка импорта")
            self.activity_description.setText(
                "Проверьте журнал, ссылку и доступность папки, затем повторите попытку."
            )
            QMessageBox.warning(
                self,
                "Импорт не завершён",
                "Во время импорта произошла ошибка. Подробности доступны в журнале.",
            )

        self.status_label.setText(self._last_status)
        self._reset_ui(keep_status=True)

    def _cancel_import(self) -> None:
        if not self.import_running:
            return

        try:
            self.cancel_btn.setEnabled(False)
            self.service.cancel()
            self._update_progress("Отмена импорта...")
            self.log_message.emit("Отмена импорта...")
        except Exception as error:
            self.log_message.emit(f"Ошибка отмены: {error}")
            self.cancel_btn.setEnabled(True)

    def _reset_ui(self, keep_status: bool = False) -> None:
        self._set_running_state(False)
        self.progress_bar.setVisible(False)
        if not keep_status:
            self._last_status = "Готов к работе"
            self.status_label.setText(self._last_status)
            self.activity_description.setText(
                "После запуска здесь будет отображаться текущий этап загрузки."
            )
        self._emit_context()
