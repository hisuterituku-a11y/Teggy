from __future__ import annotations

import os
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.logger import ERROR_LOG_FILE, LOG_FILE
from core.version import display_version
from gui.components.window_title_bar import WindowTitleBar


ISSUES_URL = "https://github.com/hisuterituku-a11y/Teggy/issues"
REPOSITORY_URL = "https://github.com/hisuterituku-a11y/Teggy"
TELEGRAM_HANDLE = "@olablud"
TELEGRAM_URL = "https://t.me/olablud"

FAQ_SECTIONS = [
    (
        "Начало работы",
        [
            (
                "Что вообще умеет Teggy?",
                "Teggy загружает материалы из Яндекс Карт, обрабатывает изображения, записывает теги в метаданные, сравнивает фотографии, удаляет дубли и помогает готовить контент для карточки организации.",
            ),
            (
                "С чего начать работу?",
                "Выберите нужный инструмент на главной странице. Для импорта из Яндекс Карт вставьте ссылку на организацию и укажите папку сохранения. Для тегирования выберите папку с фотографиями и подготовьте набор тегов.",
            ),
            (
                "Можно ли работать сразу с несколькими организациями?",
                "Да, но каждую организацию лучше сохранять в отдельную папку. Так фотографии, результаты обработки и диагностика не перемешаются в один великолепный цифровой суп.",
            ),
            (
                "Нужен ли интернет?",
                "Для локального тегирования фотографий интернет не требуется. Для Яндекс Карт, Wordstat, загрузки видео и проверки обновлений подключение необходимо.",
            ),
        ],
    ),
    (
        "Импорт из Яндекс Карт",
        [
            (
                "Какую ссылку вставлять?",
                "Подойдёт ссылка на карточку организации в Яндекс Картах. Ссылки на разделы «Фото» и «Отзывы» тоже принимаются и приводятся к нужному виду автоматически.",
            ),
            (
                "Что именно скачивает Teggy?",
                "Teggy отдельно собирает фотографии организации, изображения из отзывов, доступные Stories и видео. После этого материалы можно сравнить и очистить от дублей.",
            ),
            (
                "Куда сохраняются материалы?",
                "В папку, выбранную перед запуском импорта. Точный путь отображается в журнале операции.",
            ),
            (
                "Можно ли повторно запустить импорт в ту же папку?",
                "Да. Уже существующие файлы могут быть пропущены, а новые добавлены. После повторного импорта рекомендуется снова запустить сравнение дублей.",
            ),
            (
                "Почему скачалось меньше фотографий, чем видно на карте?",
                "Некоторые изображения могут быть скрыты, повторяться, относиться к служебным ресурсам Яндекса или не успеть загрузиться. Teggy также исключает часть неподходящих ссылок и удаляет найденные дубли.",
            ),
            (
                "Почему импорт идёт долго?",
                "Teggy прокручивает галерею, ждёт загрузку материалов и проверяет новые ссылки. Скорость зависит от количества фотографий, интернета и настроения Яндекса, которое, как известно, величина переменная.",
            ),
            (
                "Можно ли остановить импорт?",
                "Да. После отмены текущая операция остановится, а уже сохранённые файлы останутся в выбранной папке.",
            ),
        ],
    ),
    (
        "Фото, Stories и видео",
        [
            (
                "Почему фото организации и отзывов лежат отдельно?",
                "Это разные источники контента. Раздельное сохранение помогает понимать происхождение файлов и корректно сравнивать папки между собой.",
            ),
            (
                "Что означает удаление дублей?",
                "Teggy сравнивает изображения по визуальному содержимому. Если одна и та же фотография найдена в нескольких источниках, повтор можно удалить из выбранной папки.",
            ),
            (
                "Может ли Teggy удалить похожие, но разные фото?",
                "Очень похожие кадры иногда могут считаться дублями. Перед массовой обработкой лучше проверить результат на небольшой папке.",
            ),
            (
                "Почему Stories не скачались?",
                "У организации может не быть активных Stories, они могут быть недоступны без авторизации или Яндекс мог изменить способ их загрузки. Ошибка Stories не должна останавливать импорт остальных материалов.",
            ),
            (
                "Почему видео не найдено?",
                "Не все карточки содержат видео, а некоторые ролики недоступны для прямой загрузки. В этом случае Teggy продолжает работу без критической ошибки.",
            ),
            (
                "Почему при работе открывается браузер?",
                "Teggy использует Chromium через Playwright для работы с Яндекс Картами и Wordstat. Не закрывайте окно до завершения операции.",
            ),
        ],
    ),
    (
        "Тегирование фотографий",
        [
            (
                "Что происходит при тегировании?",
                "Teggy записывает ключевые слова в метаданные изображения. Внешний вид фотографии не меняется, если отдельно не включено преобразование формата.",
            ),
            (
                "Куда записываются теги?",
                "В поддерживаемые поля метаданных изображения. Их можно проверить в свойствах файла или программе, которая показывает EXIF и IPTC.",
            ),
            (
                "Меняется ли качество фотографии?",
                "При обычной записи метаданных качество не должно меняться. При преобразовании в JPG результат зависит от исходного формата и настроек сохранения.",
            ),
            (
                "Зачем преобразовывать PNG и WEBP в JPG?",
                "JPG удобнее для загрузки во многие сервисы и лучше поддерживает нужные метаданные. Прозрачность PNG при преобразовании будет заменена обычным фоном.",
            ),
            (
                "Какие форматы поддерживаются?",
                "Основные форматы: JPG, JPEG, PNG и WEBP. Повреждённые или неподдерживаемые файлы будут пропущены с записью причины в журнал.",
            ),
            (
                "Можно ли использовать одни теги для всей папки?",
                "Да. Общий набор тегов можно применить ко всем выбранным изображениям одной организации или услуги.",
            ),
            (
                "Почему теги не записались?",
                "Проверьте, что файл не открыт другой программой, доступен для записи и имеет поддерживаемый формат. Если ошибка повторяется, сохраните диагностический отчёт.",
            ),
        ],
    ),
    (
        "Wordstat и ключевые запросы",
        [
            (
                "Для чего нужен Wordstat?",
                "Wordstat помогает получать реальные поисковые запросы по конкретной услуге и региону. Их можно использовать как основу для тегов и материалов для продвижения карточки.",
            ),
            (
                "Что вводить в поле услуги?",
                "Указывайте конкретную позицию прайса: например «Элайнеры», «Лечение кариеса» или «Имплантация зубов». Слишком общий запрос даст больше мусора.",
            ),
            (
                "Зачем выбирать город или регион?",
                "Частотность и формулировки запросов отличаются по регионам. Для локальной карточки нужно выбирать город, где находится организация.",
            ),
            (
                "Почему Wordstat просит войти в Яндекс?",
                "Яндекс требует авторизацию. Войдите в аккаунт в открывшемся браузере. Сессия сохраняется и обычно используется при следующих запусках.",
            ),
            (
                "Что такое базовые запросы?",
                "Это несколько исходных формулировок, по которым Teggy собирает расширенную статистику. Для элайнеров это могут быть «элайнеры», «капы для выравнивания зубов» и «исправление прикуса элайнерами».",
            ),
            (
                "Почему запросов получилось так много?",
                "Wordstat может вернуть тысячи вариантов. Teggy объединяет результаты, убирает дубли, фильтрует известный мусор и выбирает наиболее полезные фразы.",
            ),
            (
                "Почему появляются другие города и бренды?",
                "Wordstat показывает реальные пользовательские запросы, включая чужую географию и названия систем. Автоматические фильтры удаляют часть мусора, но итоговый список всё равно стоит просмотреть.",
            ),
            (
                "Почему итог ограничен 3000 символами?",
                "Генератор собирает строку в заданный лимит независимо от количества тегов. Добавляются только целые фразы, последний тег посередине не обрезается.",
            ),
            (
                "Нужно ли брать только самые частотные запросы?",
                "Нет. Самые частотные фразы часто слишком общие. Teggy также учитывает коммерческие слова, город, адрес, отзывы, цену и близость запроса к услуге.",
            ),
        ],
    ),
    (
        "Ошибки, установка и обновления",
        [
            (
                "Windows предупреждает об опасном приложении. Что делать?",
                "Если установщик скачан из официального релиза Teggy, нажмите «Подробнее», затем «Выполнить в любом случае». Предупреждение появляется из-за отсутствия цифровой подписи.",
            ),
            (
                "Куда установилась Teggy?",
                "По умолчанию программа устанавливается в выбранную при установке папку. Обычно это Program Files, если путь не меняли.",
            ),
            (
                "Нужно ли удалять старую версию перед обновлением?",
                "Обычно нет. Новый установщик можно запустить поверх текущей версии. Пользовательские файлы при этом не должны удаляться.",
            ),
            (
                "Где посмотреть ошибки?",
                "Откройте вкладку «Поддержка» и диагностический отчёт. При ошибках импорта Teggy также создаёт папку diagnostics в каталоге сохранения.",
            ),
            (
                "Что отправить в поддержку?",
                "Пришлите описание проблемы, скриншот, диагностический отчёт и папку diagnostics, если она была создана. Телепатия всё ещё не прошла тестирование.",
            ),
        ],
    ),
    (
        "Готовые сценарии",
        [
            (
                "Как скачать все материалы организации?",
                "Откройте раздел Яндекс Карт, вставьте ссылку на организацию, выберите папку и запустите импорт. Teggy последовательно обработает галерею, отзывы, Stories и видео.",
            ),
            (
                "Как подготовить фотографии к загрузке?",
                "Скачайте или выберите фотографии, удалите дубли, при необходимости преобразуйте их в JPG, добавьте релевантные теги и проверьте итоговую папку.",
            ),
            (
                "Как получить теги для одной услуги прайса?",
                "Укажите услугу, город и адрес. Добавьте несколько базовых запросов, соберите Wordstat, выполните фильтрацию и оптимизацию строки до 3000 символов.",
            ),
            (
                "Как понять, почему импорт завершился с предупреждениями?",
                "Откройте журнал операции. Для каждого этапа Teggy показывает тип ошибки, сообщение, URL и путь к диагностическим материалам.",
            ),
        ],
    ),
]


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Помощь и поддержка")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(780, 680)
        self.setMinimumSize(680, 580)

        shell = QWidget(self)
        shell.setObjectName("HelpDialogShell")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)

        shell_layout.addWidget(
            WindowTitleBar(
                self,
                title="Помощь и поддержка",
                show_help=False,
                show_minimize=False,
                show_maximize=False,
            )
        )

        content = QWidget()
        content.setObjectName("HelpDialogContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(8)

        self.faq_button = QPushButton("FAQ")
        self.faq_button.setObjectName("HelpSectionButton")
        self.faq_button.setCheckable(True)
        self.faq_button.setChecked(True)
        self.faq_button.clicked.connect(lambda: self._switch_page(0))
        header.addWidget(self.faq_button)

        self.support_button = QPushButton("Поддержка")
        self.support_button.setObjectName("HelpSectionButton")
        self.support_button.setCheckable(True)
        self.support_button.clicked.connect(lambda: self._switch_page(1))
        header.addWidget(self.support_button)
        header.addStretch(1)
        content_layout.addLayout(header)

        divider = QFrame()
        divider.setObjectName("HelpDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(divider)

        self.stack = QStackedWidget()
        self.stack.setObjectName("HelpStack")
        self.stack.addWidget(self._build_faq_tab())
        self.stack.addWidget(self._build_support_tab())
        content_layout.addWidget(self.stack, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        close_button = QPushButton("Закрыть")
        close_button.setObjectName("HelpCloseButton")
        close_button.clicked.connect(self.reject)
        footer.addWidget(close_button)
        content_layout.addLayout(footer)

        shell_layout.addWidget(content, 1)
        self._apply_styles()

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.faq_button.setChecked(index == 0)
        self.support_button.setChecked(index == 1)

    def _build_faq_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("HelpPage")
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("HelpScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("FaqContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 2, 10, 8)
        layout.setSpacing(22)

        intro = QLabel(
            "Ответы по установке, импорту, тегированию, Wordstat и типовым сценариям."
        )
        intro.setObjectName("FaqIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        for section_title, questions in FAQ_SECTIONS:
            section = QWidget()
            section.setObjectName("FaqSection")
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(10)

            section_label = QLabel(section_title.upper())
            section_label.setObjectName("FaqSectionTitle")
            section_layout.addWidget(section_label)

            for question, answer in questions:
                card = QFrame()
                card.setObjectName("FaqCard")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(22, 20, 22, 20)
                card_layout.setSpacing(8)

                question_label = QLabel(question)
                question_label.setObjectName("FaqQuestion")
                question_label.setWordWrap(True)
                card_layout.addWidget(question_label)

                accent = QFrame()
                accent.setObjectName("FaqAccent")
                accent.setFixedHeight(3)
                accent.setMaximumWidth(64)
                card_layout.addWidget(accent)

                answer_label = QLabel(answer)
                answer_label.setObjectName("FaqAnswer")
                answer_label.setWordWrap(True)
                answer_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                card_layout.addWidget(answer_label)
                section_layout.addWidget(card)

            layout.addWidget(section)

        layout.addStretch(1)
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)
        return tab

    def _build_support_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("HelpPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(12)

        contact_card = QFrame()
        contact_card.setObjectName("ContactCard")
        contact_layout = QVBoxLayout(contact_card)
        contact_layout.setContentsMargins(18, 16, 18, 16)
        contact_layout.setSpacing(9)

        contact_title = QLabel("Нашли баг? Или он нашёл вас?")
        contact_title.setObjectName("ContactTitle")
        contact_layout.addWidget(contact_title)

        contact_handle = QLabel(f"Telegram:  {TELEGRAM_HANDLE}")
        contact_handle.setObjectName("ContactHandle")
        contact_handle.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        contact_layout.addWidget(contact_handle)

        contact_hint = QLabel(
            "Если возникла проблема или есть идея для Teggy, напишите в Telegram. "
            "При ошибке кратко опишите, что произошло, приложите отчёт и скриншот."
        )
        contact_hint.setObjectName("ContactHint")
        contact_hint.setWordWrap(True)
        contact_layout.addWidget(contact_hint)

        telegram_button = QPushButton("Открыть Telegram")
        telegram_button.setObjectName("TelegramButton")
        telegram_button.setMinimumHeight(40)
        telegram_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(TELEGRAM_URL))
        )
        contact_layout.addWidget(telegram_button)
        layout.addWidget(contact_card)

        title = QLabel("Диагностический отчёт")
        title.setObjectName("SupportTitle")
        layout.addWidget(title)

        description = QLabel(
            "Отчёт не содержит фотографии, теги или пароли, но включает сведения "
            "о системе и последние строки журнала."
        )
        description.setObjectName("SupportDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.report_view = QTextBrowser()
        self.report_view.setObjectName("ReportView")
        self.report_view.setPlainText(self._build_report())
        layout.addWidget(self.report_view, 1)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        copy_button = QPushButton("Скопировать отчёт")
        copy_button.setObjectName("HelpPrimaryButton")
        copy_button.clicked.connect(self._copy_report)
        actions.addWidget(copy_button)

        save_button = QPushButton("Сохранить отчёт…")
        save_button.setObjectName("HelpSecondaryButton")
        save_button.clicked.connect(self._save_report)
        actions.addWidget(save_button)

        refresh_button = QPushButton("Обновить")
        refresh_button.setObjectName("HelpSecondaryButton")
        refresh_button.clicked.connect(self._refresh_report)
        actions.addWidget(refresh_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        links = QHBoxLayout()
        links.setSpacing(10)

        issues_button = QPushButton("Создать обращение")
        issues_button.setObjectName("HelpSecondaryButton")
        issues_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(ISSUES_URL))
        )
        links.addWidget(issues_button)

        repository_button = QPushButton("Открыть GitHub")
        repository_button.setObjectName("HelpSecondaryButton")
        repository_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(REPOSITORY_URL))
        )
        links.addWidget(repository_button)
        links.addStretch(1)
        layout.addLayout(links)

        return tab

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#HelpDialogShell {
                background: #111827;
                border: 1px solid #2f3b52;
                border-radius: 14px;
            }
            QWidget#HelpDialogContent,
            QWidget#HelpPage,
            QWidget#FaqContent,
            QWidget#FaqSection,
            QStackedWidget#HelpStack {
                background: transparent;
                border: none;
            }
            QFrame#HelpDivider {
                background: #28344a;
                border: none;
                max-height: 1px;
            }
            QPushButton#HelpSectionButton {
                min-width: 108px;
                min-height: 36px;
                padding: 0 18px;
                color: #9ca9bd;
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#HelpSectionButton:hover,
            QPushButton#HelpSectionButton:checked {
                color: #ffffff;
                background: #172033;
                border-radius: 7px 7px 0 0;
            }
            QPushButton#HelpSectionButton:checked {
                border-bottom: 2px solid #7c3aed;
            }
            QScrollArea#HelpScroll,
            QScrollArea#HelpScroll > QWidget > QWidget {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px 0;
            }
            QScrollBar::handle:vertical {
                background: #5b35a6;
                min-height: 34px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
                border: none;
                height: 0;
            }
            QLabel#FaqIntro,
            QLabel#SupportDescription,
            QLabel#ContactHint {
                color: #9da9bb;
                font-size: 13px;
                border: none;
                background: transparent;
            }
            QLabel#FaqSectionTitle,
            QLabel#FaqQuestion,
            QLabel#FaqAnswer,
            QLabel#SupportTitle,
            QLabel#ContactTitle,
            QLabel#ContactHandle {
                border: none;
                background: transparent;
            }
            QLabel#FaqSectionTitle {
                color: #8b9ab0;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 0 2px 2px 2px;
            }
            QLabel#SupportTitle,
            QLabel#ContactTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }
            QFrame#FaqCard,
            QFrame#ContactCard {
                background: #151f32;
                border: 1px solid #2b3850;
                border-radius: 10px;
            }
            QFrame#FaqCard:hover {
                border-color: #4c3f78;
                background: #18233a;
            }
            QFrame#ContactCard {
                border-color: #4d3977;
                background: #171f34;
            }
            QLabel#FaqQuestion {
                color: #f7f9fc;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#ContactHandle {
                color: #c9b7ff;
                font-size: 15px;
                font-weight: 700;
            }
            QFrame#FaqAccent {
                background: #6d3fc0;
                border: none;
                border-radius: 1px;
                max-width: 52px;
            }
            QLabel#FaqAnswer {
                color: #b4bfd0;
                font-size: 13px;
                padding-top: 1px;
            }
            QTextBrowser#ReportView {
                background: #0c1322;
                color: #d5deeb;
                border: 1px solid #2b3850;
                border-radius: 9px;
                padding: 12px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QPushButton#HelpPrimaryButton,
            QPushButton#HelpSecondaryButton,
            QPushButton#HelpCloseButton,
            QPushButton#TelegramButton {
                min-height: 36px;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
            }
            QPushButton#HelpPrimaryButton,
            QPushButton#TelegramButton {
                background: #6d3fc0;
                color: white;
                border: 1px solid #8150d4;
            }
            QPushButton#HelpPrimaryButton:hover,
            QPushButton#TelegramButton:hover {
                background: #7b4acd;
            }
            QPushButton#HelpSecondaryButton,
            QPushButton#HelpCloseButton {
                background: #172033;
                color: #dce5f2;
                border: 1px solid #30405a;
            }
            QPushButton#HelpSecondaryButton:hover,
            QPushButton#HelpCloseButton:hover {
                background: #1d2a42;
                border-color: #445878;
            }
            QPushButton#HelpCloseButton {
                min-width: 118px;
            }
            """
        )

    def _refresh_report(self) -> None:
        self.report_view.setPlainText(self._build_report())

    def _copy_report(self) -> None:
        QGuiApplication.clipboard().setText(self.report_view.toPlainText())
        QMessageBox.information(
            self,
            "Готово",
            "Диагностический отчёт скопирован.",
        )

    def _save_report(self) -> None:
        default_name = f"teggy-report-{datetime.now():%Y%m%d-%H%M%S}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить диагностический отчёт",
            str(Path.home() / default_name),
            "Текстовые файлы (*.txt)",
        )
        if not path:
            return

        try:
            Path(path).write_text(
                self.report_view.toPlainText(),
                encoding="utf-8",
            )
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить отчёт:\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Готово",
            "Диагностический отчёт сохранён.",
        )

    def _build_report(self) -> str:
        ffmpeg_path = shutil.which("ffmpeg") or "не найден"
        lines = [
            "Teggy — диагностический отчёт",
            f"Дата: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"Версия: {display_version()}",
            f"ОС: {platform.platform()}",
            f"Python: {sys.version.replace(os.linesep, ' ')}",
            f"Архитектура: {platform.machine() or 'не определена'}",
            f"FFmpeg: {ffmpeg_path}",
            f"Рабочая папка: {Path.cwd()}",
            f"Исполняемый файл: {sys.executable}",
            "",
            "Последние строки журнала:",
            self._read_recent_log(),
        ]
        return "\n".join(lines)

    @staticmethod
    def _read_recent_log() -> str:
        parts: list[str] = []

        for path, title in (
            (LOG_FILE, "Основной журнал"),
            (ERROR_LOG_FILE, "Журнал ошибок"),
        ):
            if not path.is_file():
                parts.append(f"{title}: файл не найден: {path}")
                continue

            try:
                lines = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()

                parts.extend(
                    [
                        f"{title}: {path}",
                        *lines[-200:],
                    ]
                )
            except OSError as exc:
                parts.append(
                    f"{title}: не удалось прочитать {path}: {exc}"
                )

            parts.append("")

        return "\n".join(parts).rstrip()