from pathlib import Path
from core.yandex.service import YandexService

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QPlainTextEdit,
    QProgressBar,
)


class YandexMapsPage(QWidget):
    """
    Страница загрузки данных из карточки организации
    на Яндекс Картах.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Путь к папке текущего проекта.
        # В настройки не сохраняется.
        self.output_folder = None
        self.service = YandexService()
        self.is_downloading = False

        self.setup_ui()
        self.update_download_button()

    def setup_ui(self):
        """
        Создаёт интерфейс страницы.
        """

        root = QVBoxLayout(self)

        root.setContentsMargins(
            32,
            24,
            32,
            24,
        )

        root.setSpacing(
            18
        )

        # =========================
        # HEADER
        # =========================

        title = QLabel(
            "Яндекс Карты"
        )

        title.setObjectName(
            "SectionTitle"
        )

        root.addWidget(
            title
        )

        subtitle = QLabel(
            "Загрузка фотографий и данных из карточки нового проекта"
        )

        subtitle.setObjectName(
            "CardSubtitle"
        )

        root.addWidget(
            subtitle
        )

        # =========================
        # SOURCE CARD
        # =========================

        source_card = QFrame()

        source_card.setObjectName(
            "PhotoPanel"
        )

        source_layout = QVBoxLayout(
            source_card
        )

        source_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        source_layout.setSpacing(
            14
        )

        source_title = QLabel(
            "Карточка организации"
        )

        source_title.setObjectName(
            "CardTitle"
        )

        source_layout.addWidget(
            source_title
        )

        source_text = QLabel(
            "Вставьте ссылку на организацию в Яндекс Картах"
        )

        source_text.setObjectName(
            "CardSubtitle"
        )

        source_layout.addWidget(
            source_text
        )

        url_row = QHBoxLayout()

        url_row.setSpacing(
            10
        )

        self.url_input = QLineEdit()

        self.url_input.setPlaceholderText(
            "https://yandex.ru/maps/org/..."
        )

        self.url_input.textChanged.connect(
            self.update_download_button
        )

        url_row.addWidget(
            self.url_input,
            1
        )

        self.check_button = QPushButton(
            "Проверить"
        )

        self.check_button.setObjectName(
            "YandexActionButton"
        )

        self.check_button.clicked.connect(
            self.check_url
        )

        url_row.addWidget(
            self.check_button
        )

        source_layout.addLayout(
            url_row
        )

        self.url_status = QLabel(
            "Ссылка ещё не проверена"
        )

        self.url_status.setObjectName(
            "CardSubtitle"
        )

        source_layout.addWidget(
            self.url_status
        )

        root.addWidget(
            source_card
        )

        # =========================
        # OUTPUT FOLDER CARD
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
            24,
        )

        folder_layout.setSpacing(
            14
        )

        folder_title = QLabel(
            "Папка проекта"
        )

        folder_title.setObjectName(
            "CardTitle"
        )

        folder_layout.addWidget(
            folder_title
        )

        folder_text = QLabel(
            "Выберите папку, куда будут сохранены фотографии и другие данные"
        )

        folder_text.setObjectName(
            "CardSubtitle"
        )

        folder_text.setWordWrap(
            True
        )

        folder_layout.addWidget(
            folder_text
        )

        folder_row = QHBoxLayout()

        folder_row.setSpacing(
            10
        )

        self.folder_path_input = QLineEdit()

        self.folder_path_input.setPlaceholderText(
            "Папка не выбрана"
        )

        self.folder_path_input.setReadOnly(
            True
        )

        folder_row.addWidget(
            self.folder_path_input,
            1
        )

        self.folder_button = QPushButton(
            "Выбрать папку"
        )

        self.folder_button.setObjectName(
            "YandexActionButton"
        )

        self.folder_button.clicked.connect(
            self.choose_output_folder
        )

        folder_row.addWidget(
            self.folder_button
        )

        folder_layout.addLayout(
            folder_row
        )

        root.addWidget(
            folder_card
        )

        # =========================
        # DOWNLOAD OPTIONS
        # =========================

        options_card = QFrame()

        options_card.setObjectName(
            "PhotoPanel"
        )

        options_layout = QVBoxLayout(
            options_card
        )

        options_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        options_layout.setSpacing(
            12
        )

        options_title = QLabel(
            "Дополнительно"
        )

        options_title.setObjectName(
            "CardTitle"
        )

        options_layout.addWidget(
            options_title
        )


        stories_card, self.stories_checkbox = (
            self.create_download_option(
                title="Скачать сторис",
                description=(
                    "Дополнительно сохранить изображения "
                    "из историй организации"
                ),
                checked=False,
            )
        )

        options_layout.addWidget(
            stories_card
        )

        root.addWidget(
            options_card
        )

        # =========================
        # DOWNLOAD BUTTON
        # =========================

        download_buttons_layout = QHBoxLayout()

        download_buttons_layout.setSpacing(
            10
        )

        self.download_button = QPushButton(
            "Скачать данные"
        )

        self.download_button.setObjectName(
            "PrimaryButton"
        )

        self.download_button.clicked.connect(
            self.start_download
        )

        download_buttons_layout.addWidget(
            self.download_button,
            1
        )

        self.cancel_button = QPushButton(
            "Отменить"
        )

        self.cancel_button.setObjectName(
            "YandexActionButton"
        )

        self.cancel_button.setEnabled(
            False
        )

        self.cancel_button.clicked.connect(
            self.cancel_download
        )

        download_buttons_layout.addWidget(
            self.cancel_button
        )

        root.addLayout(
            download_buttons_layout
        )

        self.download_status = QLabel(
            "Укажите ссылку и выберите папку проекта"
        )

        self.download_status.setObjectName(
            "CardSubtitle"
        )

        self.download_status.setAlignment(
            Qt.AlignLeft
        )

        root.addWidget(
            self.download_status
        )
        # =========================
        # DOWNLOAD PROGRESS
        # =========================

        self.download_progress = QProgressBar()

        self.download_progress.setObjectName(
            "YandexDownloadProgress"
        )

        self.download_progress.setRange(
            0,
            0
        )

        self.download_progress.setVisible(
            False
        )

        self.download_progress.setTextVisible(
            False
        )

        root.addWidget(
            self.download_progress
        )

        # =========================
        # DOWNLOAD LOG
        # =========================

        log_card = QFrame()

        log_card.setObjectName(
            "PhotoPanel"
        )

        log_layout = QVBoxLayout(
            log_card
        )

        log_layout.setContentsMargins(
            20,
            18,
            20,
            18
        )

        log_layout.setSpacing(
            12
        )

        log_title = QLabel(
            "Журнал загрузки"
        )

        log_title.setObjectName(
            "CardTitle"
        )

        log_layout.addWidget(
            log_title
        )

        self.download_log = QPlainTextEdit()

        self.download_log.setObjectName(
            "YandexDownloadLog"
        )

        self.download_log.setReadOnly(
            True
        )

        self.download_log.setPlaceholderText(
            "Здесь появится информация о загрузке"
        )

        self.download_log.setMinimumHeight(
            150
        )

        log_layout.addWidget(
            self.download_log
        )

        root.addWidget(
            log_card
        )

        

    def create_download_option(
        self,
        title: str,
        description: str,
        checked: bool = False,
    ):
        """
        Создаёт оформленную карточку выбора типа данных.
        """

        card = QFrame()

        card.setObjectName(
            "DownloadOptionCard"
        )

        card.setProperty(
            "selected",
            checked
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14
        )

        layout.setSpacing(
            12
        )

        checkbox = QCheckBox()

        checkbox.setObjectName(
            "DownloadOptionCheck"
        )

        checkbox.setChecked(
            checked
        )

        layout.addWidget(
            checkbox
        )

        text_layout = QVBoxLayout()

        text_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        text_layout.setSpacing(
            3
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "DownloadOptionTitle"
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "DownloadOptionDescription"
        )

        description_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            description_label
        )

        layout.addLayout(
            text_layout,
            1
        )

        def update_card_state(state):
            """
            Обновляет оформление карточки при выборе.
            """

            selected = (
                state == Qt.CheckState.Checked.value
            )

            card.setProperty(
                "selected",
                selected
            )

            card.style().unpolish(
                card
            )

            card.style().polish(
                card
            )

            card.update()

            self.update_download_button()

        checkbox.stateChanged.connect(
            update_card_state
        )

        return card, checkbox

    def choose_output_folder(self):
        """
        Выбирает папку текущего проекта.
        """

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку проекта"
        )

        if not folder:
            return

        self.output_folder = Path(folder)

        self.folder_path_input.setText(
            str(self.output_folder)
        )

        self.update_download_button()

    def check_url(self):
        """
        Выполняет базовую проверку введённой ссылки.

        Реальная проверка через backend будет добавлена позже.
        """

        url = self.url_input.text().strip()

        if not url:
            self.url_status.setText(
                "Введите ссылку на карточку организации"
            )

            return

        if (
            "yandex.ru/maps" not in url
            and "yandex.com/maps" not in url
        ):
            self.url_status.setText(
                "Ссылка не похожа на ссылку Яндекс Карт"
            )

            return

        self.url_status.setText(
            "Ссылка выглядит корректно"
        )

    def update_download_button(self):
        """
        Включает кнопку загрузки только тогда, когда
        заполнены обязательные данные.
        """

        has_url = bool(
            self.url_input.text().strip()
        )

        has_folder = (
            self.output_folder is not None
        )



        can_download = (
            has_url
            and has_folder
        )

        self.download_button.setEnabled(
            can_download
        )

        if not has_url:
            self.download_status.setText(
                "Укажите ссылку на организацию"
            )

        elif not has_folder:
            self.download_status.setText(
                "Выберите папку текущего проекта"
            )


        else:
            self.download_status.setText(
                "Данные готовы к загрузке"
            )

    def start_download(self):
        """
        Запускает скачивание данных из Яндекс Карт.

        Фото организации и фото из отзывов
        скачиваются всегда.

        Stories скачиваются только по выбору пользователя.
        """
        if self.is_downloading:
            return
        
        url = self.url_input.text().strip()

        if self.output_folder is None:
            self.download_status.setText(
                "Сначала выберите папку проекта"
            )
            return

        download_stories = (
            self.stories_checkbox.isChecked()
        )
        self.is_downloading = True

        self.download_log.clear()

        self.download_progress.setVisible(
            True
        )

        self.download_button.setEnabled(
            False
        )
        self.cancel_button.setEnabled(
            True
        )

        self.folder_button.setEnabled(
            False
        )

        self.check_button.setEnabled(
            False
        )

        self.url_input.setEnabled(
            False
        )

        self.stories_checkbox.setEnabled(
            False
        )

        self.download_status.setText(
            "Загрузка запущена"
        )

        self.service.start(
            url=url,
            save_dir=self.output_folder,
            download_stories=download_stories,
            on_log=self.append_download_log,
            on_progress=self.update_download_progress,
            on_finished=self.on_download_finished,
            skip_existing=True,
        )

    def cancel_download(self):
        """
        Запрашивает отмену текущей загрузки.
        """

        if not self.is_downloading:
            return

        self.cancel_button.setEnabled(
            False
        )

        self.download_status.setText(
            "Отмена загрузки..."
        )

        self.append_download_log(
            "Запрошена отмена загрузки"
        )

        self.service.cancel()

    def append_download_log(self, text: str):
        """
        Добавляет сообщение backend в журнал загрузки.
        """

        self.download_log.appendPlainText(
            str(text)
        )
    def update_download_progress(self, text: str):
        """
        Показывает название текущего этапа загрузки.
        """

        self.download_status.setText(
            str(text)
        )
    def on_download_finished(self, success: bool):
        """
        Завершает состояние загрузки и возвращает интерфейс
        в обычный режим.
        """
        self.is_downloading = False

        self.cancel_button.setEnabled(
            False
        )
        self.download_progress.setVisible(
            False
        )

        self.folder_button.setEnabled(
            True
        )

        self.check_button.setEnabled(
            True
        )

        self.url_input.setEnabled(
            True
        )

        self.stories_checkbox.setEnabled(
            True
        )

        if success:
            self.download_status.setText(
                "Загрузка завершена"
            )
        else:
            self.download_status.setText(
                "Загрузка не завершена"
            )

        self.update_download_button()