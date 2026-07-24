from pathlib import Path

from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QProgressBar,
    QFileDialog
)

from core.yandex.service import YandexService

from gui.widgets.cards import (
    Card,
    CardHeader,
    CardBody
)

from gui.widgets.buttons import (
    PrimaryButton,
    SecondaryButton
)

from gui.widgets.log_widget import LogWidget


class YandexDownloaderPage(QWidget):
    """
    Страница импорта фотографий из Яндекс Карт.

    Поток:

    GUI
      |
      | _start_import()
      |
    YandexService
      |
      | YandexWorker (QThread) -> сигналы log / progress / finished_ok
      |
    Signal этой страницы (log_message / progress_message / import_finished)
      |
    GUI thread (через Qt.QueuedConnection)

    ИСПРАВЛЕНО (по сравнению с предыдущей версией файла):
    1. Было `progress_updated = Signal(ImportProgress)`, а ImportProgress
       нигде не импортировался — это NameError прямо при импорте модуля
       (аргумент Signal(...) вычисляется в момент выполнения тела класса),
       то есть приложение падало ещё до открытия окна. Новый пайплайн
       (core.yandex.YandexRouter) вообще не считает проценты — он шлёт
       только текстовые сообщения о прогрессе, поэтому вместо
       Signal(ImportProgress) + Slot(ImportProgress) теперь простой
       Signal(str) + Slot(str).
    2. Было: `on_finished=self._import_finished` передавался в
       service.start(...), а СРАЗУ после этого вызова определялась
       ЛОКАЛЬНАЯ функция `def _import_finished(self, success):` —
       она не являлась методом класса и была определена ПОЗЖЕ, чем на
       неё ссылались. Реальный запуск падал с AttributeError ещё до
       старта импорта. Теперь `_on_import_finished` — обычный метод
       класса, подключённый через сигнал.
    3. Было: `on_progress=lambda text: self.status_label.setText(text)` —
       прямое обращение к виджету из колбэка, вызываемого не в GUI-потоке
       (см. комментарий "НИКАКОГО UI здесь!" у старого _on_progress).
       Теперь единственный безопасный путь наружу из потока — через
       сигналы этой страницы, подключённые с явным Qt.QueuedConnection.
    """

    log_message = Signal(str)
    progress_message = Signal(str)
    import_finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setProperty(
            "class",
            "YandexDownloaderPage"
        )

        self.service = YandexService()

        self.import_running = False

        # ==========================
        # Layout
        # ==========================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            16,
            16,
            16
        )

        layout.setSpacing(16)

        # ==========================
        # Заголовок
        # ==========================

        title = QLabel(
            "Импорт из Яндекс Карт"
        )

        title.setProperty(
            "class",
            "PageTitle"
        )

        layout.addWidget(title)

        # ==========================
        # Настройки
        # ==========================

        card = Card()

        header = CardHeader()
        header.set_title(
            "Настройки"
        )

        card.add_widget(header)

        body = CardBody()

        # URL

        url_widget = QWidget()

        url_layout = QHBoxLayout(
            url_widget
        )

        url_label = QLabel(
            "Ссылка:"
        )

        url_label.setFixedWidth(
            150
        )

        self.url_input = QLineEdit()

        self.url_input.setPlaceholderText(
            "https://yandex.ru/maps/org/..."
        )

        url_layout.addWidget(
            url_label
        )

        url_layout.addWidget(
            self.url_input
        )

        body.add_widget(
            url_widget
        )

        # Папка

        folder_widget = QWidget()

        folder_layout = QHBoxLayout(
            folder_widget
        )

        folder_label = QLabel(
            "Папка:"
        )

        folder_label.setFixedWidth(
            150
        )

        self.folder_input = QLineEdit()

        self.folder_input.setPlaceholderText(
            "Выберите папку..."
        )

        self.folder_input.setReadOnly(
            True
        )

        self.folder_browse_btn = SecondaryButton(
            "Обзор"
        )

        self.folder_browse_btn.clicked.connect(
            self._browse_folder
        )

        folder_layout.addWidget(
            folder_label
        )

        folder_layout.addWidget(
            self.folder_input
        )

        folder_layout.addWidget(
            self.folder_browse_btn
        )

        body.add_widget(
            folder_widget
        )

        # Опции

        self.skip_existing_cb = QCheckBox(
            "Не скачивать существующие"
        )

        self.skip_existing_cb.setChecked(
            True
        )

        body.add_widget(
            self.skip_existing_cb
        )

        card.add_widget(
            body
        )

        layout.addWidget(
            card
        )

        # ==========================
        # Кнопки
        # ==========================

        buttons = QWidget()

        buttons_layout = QHBoxLayout(
            buttons
        )

        self.start_btn = PrimaryButton(
            "Скачать"
        )

        self.start_btn.clicked.connect(
            self._start_import
        )

        self.cancel_btn = SecondaryButton(
            "Отмена"
        )

        self.cancel_btn.clicked.connect(
            self._cancel_import
        )

        self.cancel_btn.setEnabled(
            False
        )

        buttons_layout.addWidget(
            self.start_btn
        )

        buttons_layout.addWidget(
            self.cancel_btn
        )

        layout.addWidget(
            buttons
        )

        # ==========================
        # Прогресс
        # ==========================

        self.progress_bar = QProgressBar()

        self.progress_bar.setVisible(
            False
        )

        # ИЗМЕНЕНО: новый пайплайн шлёт только текстовые сообщения о
        # прогрессе ("Организация: 3/12 — ...", "Скачиваем фото отзывов"),
        # без процентов — точного "сколько всего шагов" на старте
        # заранее не известно (парсинг ещё не закончен). Диапазон (0, 0)
        # в Qt переключает QProgressBar в режим "бегущей полосы"
        # (indeterminate/busy), что честнее, чем показывать
        # придуманный процент.
        self.progress_bar.setRange(
            0,
            0
        )

        layout.addWidget(
            self.progress_bar
        )

        # ==========================
        # Статус
        # ==========================

        self.status_label = QLabel(
            "Готов к работе"
        )

        self.status_label.setProperty(
            "class",
            "StatusLabel"
        )

        layout.addWidget(
            self.status_label
        )

        # ==========================
        # Лог
        # ==========================

        log_card = Card()

        log_header = CardHeader()

        log_header.set_title(
            "Лог"
        )

        log_card.add_widget(
            log_header
        )

        log_body = CardBody()

        self.log_widget = LogWidget()

        log_body.add_widget(
            self.log_widget
        )

        log_card.add_widget(
            log_body
        )

        layout.addWidget(
            log_card
        )

        # ==========================
        # Signals
        # ==========================
        # Все три канала явно подключены с Qt.QueuedConnection — это
        # гарантирует, что реальное обновление виджетов происходит в
        # GUI-потоке, даже если сигнал пришёл из YandexWorker
        # (отдельный QThread), а не полагается на неявное автоопределение
        # типа соединения.

        self.log_message.connect(
            self.log_widget.info,
            Qt.QueuedConnection
        )

        self.progress_message.connect(
            self._update_progress,
            Qt.QueuedConnection
        )

        self.import_finished.connect(
            self._on_import_finished,
            Qt.QueuedConnection
        )

    # =================================================
    # Выбор папки
    # =================================================

    def _browse_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку"
        )

        if folder:
            self.folder_input.setText(
                folder
            )

    # =================================================
    # Старт
    # =================================================

    def _start_import(self):

        if self.import_running:
            return

        url = self.url_input.text().strip()

        if not url:
            self.log_message.emit(
                "Введите ссылку Яндекс Карт"
            )
            return

        save_dir = Path(
            self.folder_input.text()
        )

        if not save_dir.exists():

            self.log_message.emit(
                "Выберите папку сохранения"
            )

            return

        self.import_running = True

        self.start_btn.setEnabled(
            False
        )

        self.cancel_btn.setEnabled(
            True
        )

        self.progress_bar.setVisible(
            True
        )

        self.status_label.setText(
            "Запуск..."
        )

        # Колбэки идут ТОЛЬКО в сигналы этой страницы — они уже
        # подключены выше через Qt.QueuedConnection, поэтому это
        # единственное безопасное место передачи данных из фонового
        # потока в GUI.
        try:
            self.service.start(
                url=url,
                save_dir=save_dir,
                on_log=self.log_message.emit,
                on_progress=self.progress_message.emit,
                on_finished=self.import_finished.emit,
                skip_existing=self.skip_existing_cb.isChecked()
            )
        except Exception as e:
            self.log_message.emit(
                f"Ошибка запуска: {e}"
            )
            self._reset_ui()

    # =================================================
    # Прогресс (GUI thread — вызывается через Qt.QueuedConnection)
    # =================================================

    @Slot(str)
    def _update_progress(self, text: str):
        self.status_label.setText(text)

    # =================================================
    # Завершение (GUI thread — вызывается через Qt.QueuedConnection)
    # =================================================

    @Slot(bool)
    def _on_import_finished(self, success: bool):

        if success:
            self.log_message.emit(
                "Импорт Яндекс завершён"
            )
        else:
            self.log_message.emit(
                "Импорт Яндекс завершился с ошибкой"
            )

        self._reset_ui()

    # =================================================
    # Отмена
    # =================================================

    def _cancel_import(self):

        if not self.import_running:
            return

        try:

            self.service.cancel()

            self.log_message.emit(
                "Отмена импорта..."
            )

            self.status_label.setText(
                "Отмена..."
            )

        except Exception as e:

            self.log_message.emit(
                f"Ошибка отмены: {e}"
            )

    # =================================================
    # Сброс UI
    # =================================================

    def _reset_ui(self):

        self.import_running = False

        self.start_btn.setEnabled(
            True
        )

        self.cancel_btn.setEnabled(
            False
        )

        self.progress_bar.setVisible(
            False
        )

        self.status_label.setText(
            "Готов к работе"
        )