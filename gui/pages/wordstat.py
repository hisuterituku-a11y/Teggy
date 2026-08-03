from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class WordstatFormData:
    service_name: str
    offer_text: str
    region: str
    city: str
    address: str
    manual_queries: tuple[str, ...]
    max_characters: int
    min_frequency: int
    remove_info: bool
    use_ai_filter: bool


class WordstatPage(QWidget):
    generate_requested = Signal(object)
    cancel_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._running = False
        self._last_result_text = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        title = QLabel("Генератор тегов Wordstat")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "Опишите услугу или рекламное предложение. Teggy сформирует поисковые "
            "направления, проверит их через Яндекс Wordstat, очистит результат "
            "и соберёт строку тегов в заданный лимит."
        )
        subtitle.setObjectName("CardSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        root.addWidget(self._build_offer_card())
        root.addWidget(self._build_settings_card())
        root.addWidget(self._build_actions_card())
        root.addWidget(self._build_result_card())

        self._apply_wordstat_styles()
        self._update_character_counter()

    def _build_offer_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")

        layout = QGridLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)
        layout.setColumnMinimumWidth(0, 170)
        layout.setColumnStretch(1, 1)

        title = QLabel("1. Услуга и предложение")
        title.setObjectName("CardTitle")
        layout.addWidget(title, 0, 0, 1, 2)

        service_label = QLabel("Название услуги")
        self.service_edit = QLineEdit()
        self.service_edit.setPlaceholderText("Например: падел-корт")
        self.service_edit.setClearButtonEnabled(True)
        layout.addWidget(service_label, 1, 0)
        layout.addWidget(self.service_edit, 1, 1)

        city_label = QLabel("Город")
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("Например: Москва")
        self.city_edit.setClearButtonEnabled(True)
        layout.addWidget(city_label, 2, 0)
        layout.addWidget(self.city_edit, 2, 1)

        region_label = QLabel("Регион Wordstat")
        self.region_combo = QComboBox()
        self.region_combo.setObjectName("WordstatCombo")
        self.region_combo.setEditable(False)
        self.region_combo.addItems(
            [
                "all",
                "Москва",
                "Санкт-Петербург",
                "Казань",
                "Екатеринбург",
                "Новосибирск",
            ]
        )
        self.region_combo.setCurrentText("all")
        self.region_combo.setToolTip(
            "Выберите регион Wordstat или оставьте all."
        )
        layout.addWidget(region_label, 3, 0)
        layout.addWidget(self.region_combo, 3, 1)

        address_label = QLabel("Адрес и география")
        address_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.address_edit = QTextEdit()
        self.address_edit.setFixedHeight(82)
        self.address_edit.setPlaceholderText(
            "Адрес, район, округ, метро, улицы и ориентиры.\n"
            "Например: Научный пр., 6А, ЮЗАО, Черёмушки, "
            "метро Воронцовская, рядом с Калужской."
        )
        layout.addWidget(address_label, 4, 0)
        layout.addWidget(self.address_edit, 4, 1)

        offer_label = QLabel("Описание предложения")
        offer_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.offer_edit = QTextEdit()
        self.offer_edit.setMinimumHeight(170)
        self.offer_edit.setPlaceholderText(
            "Вставьте полное описание услуги, тарифа или предложения:\n"
            "форматы занятий, аудитория, расписание, цена, особенности, "
            "условия бронирования и другие важные детали."
        )
        layout.addWidget(offer_label, 5, 0)
        layout.addWidget(self.offer_edit, 5, 1)

        manual_label = QLabel("Базовые запросы")
        manual_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.manual_queries_edit = QTextEdit()
        self.manual_queries_edit.setFixedHeight(92)
        self.manual_queries_edit.setPlaceholderText(
            "Необязательно. По одному запросу в строке.\n"
            "Если заполнено, эти запросы будут добавлены к автоматически созданным."
        )
        layout.addWidget(manual_label, 6, 0)
        layout.addWidget(self.manual_queries_edit, 6, 1)

        return card

    def _build_settings_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")

        layout = QGridLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        title = QLabel("2. Параметры")
        title.setObjectName("CardTitle")
        layout.addWidget(title, 0, 0, 1, 4)

        limit_label = QLabel("Лимит символов")
        self.max_characters_spin = QSpinBox()
        self.max_characters_spin.setObjectName("WordstatSpin")
        self.max_characters_spin.setRange(100, 10_000)
        self.max_characters_spin.setValue(3000)
        self.max_characters_spin.setSingleStep(100)
        layout.addWidget(limit_label, 1, 0)
        layout.addWidget(self.max_characters_spin, 1, 1)

        frequency_label = QLabel("Мин. частотность")
        self.min_frequency_spin = QSpinBox()
        self.min_frequency_spin.setObjectName("WordstatSpin")
        self.min_frequency_spin.setRange(0, 10_000_000)
        self.min_frequency_spin.setValue(1)
        layout.addWidget(frequency_label, 1, 2)
        layout.addWidget(self.min_frequency_spin, 1, 3)

        self.remove_info_checkbox = QCheckBox(
            "Удалять информационные запросы"
        )
        self.remove_info_checkbox.setObjectName("DownloadOptionCheck")
        self.remove_info_checkbox.setToolTip(
            "Удаляет запросы со словами вроде «что», «как», «почему», "
            "«фото», «видео» и похожими информационными намерениями."
        )
        layout.addWidget(self.remove_info_checkbox, 2, 0, 1, 2)

        self.ai_filter_checkbox = QCheckBox(
            "Использовать AI-фильтрацию"
        )
        self.ai_filter_checkbox.setObjectName("DownloadOptionCheck")
        self.ai_filter_checkbox.setChecked(True)
        self.ai_filter_checkbox.setToolTip(
            "Работает только если в приложении подключён AI-клиент. "
            "Без него этап будет пропущен."
        )
        layout.addWidget(self.ai_filter_checkbox, 2, 2, 1, 2)

        return card

    def _build_actions_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("3. Генерация")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.generate_button = QPushButton("▶ Сгенерировать теги")
        self.generate_button.setObjectName("PrimaryButton")
        self.generate_button.setMinimumHeight(38)
        self.generate_button.clicked.connect(self._request_generation)
        actions.addWidget(self.generate_button)

        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setObjectName("AboutSecondaryButton")
        self.cancel_button.setMinimumHeight(38)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        actions.addWidget(self.cancel_button)

        actions.addStretch(1)
        layout.addLayout(actions)

        self.status_label = QLabel("Готово к запуску")
        self.status_label.setObjectName("CardSubtitle")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.log_edit = QTextEdit()
        self.log_edit.setObjectName("LogView")
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(150)
        self.log_edit.setPlaceholderText(
            "Здесь появится ход сбора Wordstat и фильтрации."
        )
        layout.addWidget(self.log_edit)

        return card

    def _build_result_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        header = QHBoxLayout()

        title = QLabel("4. Результат")
        title.setObjectName("CardTitle")
        header.addWidget(title)

        header.addStretch(1)

        self.stats_label = QLabel(
            "Собрано: 0 · Уникальных: 0 · После фильтра: 0 · Тегов: 0"
        )
        self.stats_label.setObjectName("CardSubtitle")
        header.addWidget(self.stats_label)

        layout.addLayout(header)

        self.result_edit = QTextEdit()
        self.result_edit.setMinimumHeight(190)
        self.result_edit.setPlaceholderText(
            "Итоговая строка тегов появится здесь."
        )
        self.result_edit.textChanged.connect(self._update_character_counter)
        layout.addWidget(self.result_edit)

        footer = QHBoxLayout()
        footer.setSpacing(10)

        self.character_label = QLabel("0 / 3000 символов")
        self.character_label.setObjectName("CardSubtitle")
        footer.addWidget(self.character_label)

        footer.addStretch(1)

        self.copy_button = QPushButton("Копировать")
        self.copy_button.setObjectName("AboutSecondaryButton")
        self.copy_button.clicked.connect(self._copy_result)
        footer.addWidget(self.copy_button)

        self.clear_button = QPushButton("Очистить")
        self.clear_button.setObjectName("AboutSecondaryButton")
        self.clear_button.clicked.connect(self.clear_result)
        footer.addWidget(self.clear_button)

        layout.addLayout(footer)
        return card

    def _apply_wordstat_styles(self) -> None:
        self.setStyleSheet(
            """
            QComboBox#WordstatCombo,
            QSpinBox#WordstatSpin {
                min-height: 36px;
                padding-left: 12px;
                padding-right: 34px;
                color: #eef2ff;
                background: #121a2f;
                border: 1px solid #33415f;
                border-radius: 9px;
                selection-background-color: #7c3aed;
            }
            QComboBox#WordstatCombo:hover,
            QSpinBox#WordstatSpin:hover {
                border-color: #6d4bc3;
            }
            QComboBox#WordstatCombo:focus,
            QSpinBox#WordstatSpin:focus {
                border: 1px solid #8b5cf6;
            }
            QComboBox#WordstatCombo::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border-left: 1px solid #33415f;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background: #17223a;
            }
            QComboBox#WordstatCombo::drop-down:hover {
                background: #21304f;
            }
            QComboBox#WordstatCombo QAbstractItemView {
                color: #eef2ff;
                background: #121a2f;
                border: 1px solid #33415f;
                selection-background-color: #6d3fc0;
                selection-color: #ffffff;
                outline: none;
                padding: 4px;
            }
            QSpinBox#WordstatSpin::up-button,
            QSpinBox#WordstatSpin::down-button {
                subcontrol-origin: border;
                width: 28px;
                border-left: 1px solid #33415f;
                background: #17223a;
            }
            QSpinBox#WordstatSpin::up-button {
                subcontrol-position: top right;
                border-top-right-radius: 8px;
            }
            QSpinBox#WordstatSpin::down-button {
                subcontrol-position: bottom right;
                border-bottom-right-radius: 8px;
            }
            QSpinBox#WordstatSpin::up-button:hover,
            QSpinBox#WordstatSpin::down-button:hover {
                background: #21304f;
            }
            QCheckBox#DownloadOptionCheck {
                spacing: 9px;
                color: #dbe4f3;
                font-size: 13px;
            }
            QCheckBox#DownloadOptionCheck::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #52617d;
                border-radius: 5px;
                background: #111a2e;
            }
            QCheckBox#DownloadOptionCheck::indicator:hover {
                border-color: #8b5cf6;
            }
            QCheckBox#DownloadOptionCheck::indicator:checked {
                background: #8b5cf6;
                border-color: #8b5cf6;
            }
            QCheckBox#DownloadOptionCheck:disabled {
                color: #69758b;
            }
            """
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value).split()).strip(" ,;\n\t")

    def _manual_queries(self) -> tuple[str, ...]:
        values: list[str] = []
        seen: set[str] = set()

        for line in self.manual_queries_edit.toPlainText().splitlines():
            value = self._normalize(line)
            if not value:
                continue

            key = value.casefold()
            if key in seen:
                continue

            seen.add(key)
            values.append(value)

        return tuple(values)

    def form_data(self) -> WordstatFormData:
        return WordstatFormData(
            service_name=self._normalize(self.service_edit.text()),
            offer_text=self.offer_edit.toPlainText().strip(),
            region=self._normalize(self.region_combo.currentText()) or "all",
            city=self._normalize(self.city_edit.text()),
            address=self.address_edit.toPlainText().strip(),
            manual_queries=self._manual_queries(),
            max_characters=self.max_characters_spin.value(),
            min_frequency=self.min_frequency_spin.value(),
            remove_info=self.remove_info_checkbox.isChecked(),
            use_ai_filter=self.ai_filter_checkbox.isChecked(),
        )

    def _request_generation(self) -> None:
        data = self.form_data()

        if not data.service_name:
            QMessageBox.warning(
                self,
                "Не указана услуга",
                "Введите название услуги.",
            )
            self.service_edit.setFocus()
            return

        if not data.offer_text and not data.manual_queries:
            answer = QMessageBox.question(
                self,
                "Нет описания предложения",
                "Описание и базовые запросы не заполнены. "
                "Продолжить только с названием услуги?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.offer_edit.setFocus()
                return

        self.log_edit.clear()
        self.set_running(True, "Подготовка генерации…")
        self.generate_requested.emit(data)

    def set_running(
        self,
        running: bool,
        status: str | None = None,
    ) -> None:
        self._running = running

        self.generate_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)

        controls = (
            self.service_edit,
            self.offer_edit,
            self.region_combo,
            self.city_edit,
            self.address_edit,
            self.manual_queries_edit,
            self.max_characters_spin,
            self.min_frequency_spin,
            self.remove_info_checkbox,
            self.ai_filter_checkbox,
        )

        for control in controls:
            control.setEnabled(not running)

        self.generate_button.setText(
            "Генерация…"
            if running
            else "▶ Сгенерировать теги"
        )

        if status is not None:
            self.status_label.setText(status)
        elif not running:
            self.status_label.setText("Готово к запуску")

    def append_log(self, message: str) -> None:
        text = str(message).strip()
        if not text:
            return

        self.log_edit.append(text)
        scrollbar = self.log_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.status_label.setText(text)

    def set_result(
        self,
        *,
        text: str,
        collected_count: int,
        merged_count: int,
        filtered_count: int,
        tag_count: int,
    ) -> None:
        self._last_result_text = text
        self.result_edit.setPlainText(text)
        self.stats_label.setText(
            f"Собрано: {collected_count} · "
            f"Уникальных: {merged_count} · "
            f"После фильтра: {filtered_count} · "
            f"Тегов: {tag_count}"
        )
        self.set_running(False, "Генерация завершена")

    def show_error(self, message: str) -> None:
        self.set_running(False, "Генерация завершилась ошибкой")
        QMessageBox.critical(
            self,
            "Ошибка Wordstat",
            str(message),
        )

    def show_cancelled(self) -> None:
        self.set_running(False, "Генерация отменена")

    def clear_result(self) -> None:
        if self._running:
            return

        self._last_result_text = ""
        self.result_edit.clear()
        self.log_edit.clear()
        self.stats_label.setText(
            "Собрано: 0 · Уникальных: 0 · После фильтра: 0 · Тегов: 0"
        )
        self.status_label.setText("Готово к запуску")

    def _copy_result(self) -> None:
        text = self.result_edit.toPlainText().strip()

        if not text:
            QMessageBox.information(
                self,
                "Копировать нечего",
                "Сначала сгенерируйте или введите теги.",
            )
            return

        QGuiApplication.clipboard().setText(text)
        self.status_label.setText("Теги скопированы в буфер обмена")

    def _update_character_counter(self) -> None:
        count = len(self.result_edit.toPlainText())
        limit = self.max_characters_spin.value()
        self.character_label.setText(
            f"{count} / {limit} символов"
        )
