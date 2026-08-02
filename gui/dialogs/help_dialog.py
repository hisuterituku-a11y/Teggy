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

from core.version import display_version
from gui.components.window_title_bar import WindowTitleBar


ISSUES_URL = "https://github.com/hisuterituku-a11y/Teggy/issues"
REPOSITORY_URL = "https://github.com/hisuterituku-a11y/Teggy"
TELEGRAM_HANDLE = "@olablud"
TELEGRAM_URL = "https://t.me/olablud"

FAQ_SECTIONS = [
    (
        "О программе",
        [
            (
                "Что умеет Teggy?",
                "Teggy помогает собирать и обрабатывать материалы для карточек Яндекс Бизнес: "
                "импортирует фото организации, фото отзывов, Stories и видео, удаляет дубликаты, "
                "показывает изображения во встроенной галерее, записывает метаданные, применяет "
                "шаблоны и генерирует теги по данным Wordstat.",
            ),
            (
                "Нужно ли устанавливать браузер или FFmpeg отдельно?",
                "Нет. Chromium и FFmpeg входят в установщик Teggy. Приложение использует встроенные "
                "компоненты автоматически, поэтому отдельная установка Playwright, браузера или FFmpeg "
                "обычно не требуется.",
            ),
            (
                "Куда сохраняются материалы из Яндекс Карт?",
                "В выбранную папку проекта. Для разных типов материалов Teggy создаёт отдельные папки: "
                "«Фото организации», «Фото отзывы», «Сторис» и «Видео».",
            ),
        ],
    ),
    (
        "Начало работы",
        [
            (
                "Как добавить фотографии для обработки?",
                "Откройте раздел «Тегирование», нажмите «Добавить папки» либо перетащите папки "
                "и отдельные фотографии прямо в окно приложения.",
            ),
            (
                "Можно ли перетащить целую папку?",
                "Да. Teggy поддерживает drag and drop папок и отдельных изображений.",
            ),
            (
                "В каком порядке обрабатываются фотографии?",
                "Файлы обрабатываются в порядке, в котором они показаны в галерее Teggy. "
                "Перед запуском можно проверить список и убрать лишние изображения.",
            ),
            (
                "Какие форматы изображений поддерживаются?",
                "JPG и JPEG обрабатываются без преобразования. PNG, WebP, BMP и TIFF автоматически "
                "преобразуются в JPG.",
            ),
        ],
    ),
    (
        "Тегирование",
        [
            (
                "Куда сохраняются обработанные фотографии?",
                "По умолчанию исходники сохраняются, а обработанные копии помещаются в папку «Teggy» "
                "внутри выбранной папки.",
            ),
            (
                "Что делает опция «Заменять исходные фото обработанными»?",
                "При включённой опции отдельная папка «Teggy» не создаётся. После полностью успешной "
                "обработки исходные файлы заменяются обработанными прямо в выбранной папке.",
            ),
            (
                "Когда удаляются исходники?",
                "Исходный файл заменяется только после успешного создания и проверки обработанного файла. "
                "Если обработка завершилась с ошибкой, исходник сохраняется.",
            ),
            (
                "Что происходит с PNG, WebP, BMP и TIFF при замене исходников?",
                "Такие файлы преобразуются в JPG. После успешной обработки рядом с исходником появляется "
                "JPG с тем же именем, а исходный файл другого формата удаляется.",
            ),
        ],
    ),
    (
        "Яндекс Карты",
        [
            (
                "Как импортировать материалы из Яндекс Карт?",
                "Откройте раздел «Яндекс Карты», вставьте ссылку на организацию, выберите папку проекта, "
                "отметьте нужные типы материалов и запустите импорт.",
            ),
            (
                "Какие материалы можно скачать?",
                "Фото организации, фото из отзывов, Stories и видео. Каждый этап можно включать "
                "или отключать отдельно.",
            ),
            (
                "Что делает опция «Пропускать уже скачанные файлы»?",
                "Если опция включена, Teggy не скачивает повторно файлы, которые уже есть в папке проекта. "
                "Если выключена, существующие материалы могут быть загружены заново.",
            ),
            (
                "Что делает сравнение фотографий?",
                "После загрузки Teggy сравнивает фото организации и фото отзывов. Полные дубликаты удаляются "
                "только из папки организации. Фото отзывов не удаляются.",
            ),
            (
                "Как Teggy собирает Stories?",
                "Сначала Teggy пролистывает карусель Stories до конца, собирая доступные обложки, затем "
                "возвращается в начало, открывает первую карточку и ждёт автоматического показа слайдов. "
                "Если Stories зависают, приложение один раз нажимает стрелку вправо и продолжает сбор.",
            ),
            (
                "Почему Stories или видео могут не найтись?",
                "У организации может не быть таких материалов, либо Яндекс мог изменить интерфейс или "
                "формат выдачи. При повторяющейся проблеме сохраните диагностический отчёт.",
            ),
            (
                "Почему импорт может идти долго?",
                "Скорость зависит от количества материалов, соединения с интернетом и ответа серверов "
                "Яндекса. Stories требуют ожидания показа слайдов, а видео скачиваются по сегментам, "
                "поэтому эти этапы обычно дольше фотографий.",
            ),
        ],
    ),
    (
        "Видео",
        [
            (
                "Нужно ли устанавливать FFmpeg?",
                "Нет. FFmpeg входит в установщик Teggy и располагается рядом с Teggy.exe.",
            ),
            (
                "Нужно ли устанавливать Chromium или Playwright?",
                "Нет. Подходящая версия Chromium включена в сборку. Teggy самостоятельно находит "
                "встроенный браузер и использует его для сбора материалов.",
            ),
            (
                "Как скачиваются видео?",
                "Teggy находит видеоматериалы в галерее Яндекс Карт, выбирает доступные видео- и "
                "аудиодорожки DASH, скачивает сегменты и объединяет их с помощью FFmpeg.",
            ),
            (
                "Почему у некоторых видео нет звука?",
                "У исходного материала может отсутствовать отдельная аудиодорожка. В таком случае "
                "Teggy сохраняет только видеодорожку.",
            ),
        ],
    ),
    (
        "Галерея",
        [
            (
                "Для чего нужна встроенная галерея?",
                "В ней можно просматривать изображения, листать их, увеличивать, быстро переходить "
                "между файлами и проверять результаты обработки.",
            ),
            (
                "Можно ли открыть собственную папку?",
                "Да. Выберите её через интерфейс или перетащите в окно программы.",
            ),
            (
                "Можно ли удалять изображения из галереи?",
                "Да, если соответствующая команда доступна для выбранного файла. Удаление затрагивает "
                "реальный файл на диске, поэтому программа запрашивает подтверждение.",
            ),
        ],
    ),
    (
        "Метаданные",
        [
            (
                "Какие метаданные поддерживаются?",
                "Teggy записывает поддерживаемые поля EXIF, IPTC и XMP.",
            ),
            (
                "Можно ли записать метаданные сразу в несколько фотографий?",
                "Да. Добавьте папку или несколько отдельных фотографий, заполните поля и запустите "
                "пакетную обработку.",
            ),
            (
                "Какие поля можно заполнить?",
                "Название, тема, комментарий, автор, авторские права и ключевые слова.",
            ),
            (
                "Почему метаданные не записались?",
                "Проверьте, что файл доступен для записи, не открыт другой программой и имеет "
                "поддерживаемый формат. При повторной ошибке сохраните диагностический отчёт.",
            ),
        ],
    ),
    (
        "Шаблоны",
        [
            (
                "Что такое шаблон метаданных?",
                "Это сохранённый набор полей, который можно повторно применять к выбранным изображениям.",
            ),
            (
                "Можно ли создать несколько шаблонов?",
                "Да. Можно хранить разные шаблоны для Яндекс Бизнес, Google Maps, 2ГИС или отдельных клиентов.",
            ),
            (
                "Где находятся шаблоны?",
                "Нажмите кнопку «Шаблоны метаданных» в разделе тегирования. Там можно создавать, "
                "изменять, удалять и применять шаблоны.",
            ),
        ],
    ),
    (
        "Wordstat",
        [
            (
                "Что делает генератор тегов Wordstat?",
                "Он собирает поисковые запросы, объединяет результаты, удаляет дубликаты и нерелевантные "
                "фразы, после чего формирует итоговую строку тегов до 3000 символов.",
            ),
            (
                "Что такое базовые запросы?",
                "Это основные поисковые фразы, с которых начинается сбор. Их можно заменить своими.",
            ),
            (
                "Почему часть запросов удаляется?",
                "Фильтр исключает чужую географию, бренды, годы, товарные и нерелевантные запросы.",
            ),
            (
                "Почему итог короче 3000 символов?",
                "После фильтрации могло остаться меньше качественных запросов. Teggy не добавляет "
                "случайные слова только ради заполнения лимита.",
            ),
        ],
    ),
    (
        "Диагностика",
        [
            (
                "Где находятся журналы?",
                r"Основной журнал: %USERPROFILE%\.teggy\logs\teggy.log. Журнал ошибок: "
                r"%USERPROFILE%\.teggy\logs\teggy-errors.log. При новом запуске создаётся свежий "
                "основной журнал, а предыдущие сессии сохраняются в архивных файлах.",
            ),
            (
                "Что входит в диагностический отчёт?",
                "Версия Teggy, сведения об операционной системе и Python, архитектура, путь к FFmpeg, "
                "рабочая папка, путь к исполняемому файлу и последние строки текущего журнала.",
            ),
            (
                "Как создать диагностический отчёт?",
                "Перейдите на вкладку «Поддержка» в этом окне и нажмите «Сохранить отчёт…» "
                "или «Скопировать отчёт».",
            ),
            (
                "Что приложить при обращении в поддержку?",
                "Диагностический отчёт, краткое описание действий перед ошибкой и, по возможности, "
                "снимок экрана.",
            ),
            (
                "Как сообщить об ошибке?",
                "На вкладке «Поддержка» можно открыть Telegram разработчика или создать обращение "
                "в GitHub Issues.",
            ),
        ],
    ),
    (
        "Обновления",
        [
            (
                "Нужно ли удалять старую версию?",
                "Нет. Новую версию можно устанавливать поверх существующей.",
            ),
            (
                "Где посмотреть версию программы?",
                "Версия отображается в интерфейсе, диагностическом отчёте и журнале запуска.",
            ),
            (
                "Как удалить Teggy?",
                "Используйте пункт удаления Teggy в меню «Пуск» или стандартный раздел установленных "
                "приложений Windows.",
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
        self.resize(860, 720)
        self.setMinimumSize(720, 620)

        self._faq_scroll: QScrollArea | None = None
        self._faq_sections: dict[str, QWidget] = {}

        shell = QWidget(self)
        shell.setObjectName("HelpDialogShell")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)

        title_bar = WindowTitleBar(
            self,
            title="Помощь и поддержка",
            show_help=False,
            show_minimize=False,
            show_maximize=False,
        )
        shell_layout.addWidget(title_bar)

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

    def _scroll_to_section(self, title: str) -> None:
        scroll = self._faq_scroll
        target = self._faq_sections.get(title)
        if scroll is None or target is None:
            return
        scroll.ensureWidgetVisible(target, 0, 12)

    def _build_faq_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("HelpPage")
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(12)

        nav_scroll = QScrollArea()
        nav_scroll.setObjectName("FaqNavScroll")
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        nav_scroll.setFixedHeight(48)

        nav_content = QWidget()
        nav_content.setObjectName("FaqNavContent")
        nav_layout = QHBoxLayout(nav_content)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        for section_title, _ in FAQ_SECTIONS:
            button = QPushButton(section_title)
            button.setObjectName("FaqNavButton")
            button.clicked.connect(
                lambda checked=False, title=section_title: self._scroll_to_section(title)
            )
            nav_layout.addWidget(button)
        nav_layout.addStretch(1)
        nav_scroll.setWidget(nav_content)
        tab_layout.addWidget(nav_scroll)

        scroll = QScrollArea()
        scroll.setObjectName("HelpScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._faq_scroll = scroll

        content = QWidget()
        content.setObjectName("FaqContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 2, 10, 8)
        layout.setSpacing(22)

        intro = QLabel(
            "Краткие ответы по основным функциям Teggy. Используйте кнопки выше, чтобы быстро перейти к нужному разделу."
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
            self._faq_sections[section_title] = section

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
        tab_layout.addWidget(scroll, 1)
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
            "Если возникла проблема или есть идея для Teggy, напишите мне в Telegram. "
            "При ошибке кратко опишите, что произошло, и приложите диагностический отчёт. "
            "Скриншот тоже пригодится, потому что телепатия в сборку пока не вошла."
        )
        contact_hint.setObjectName("ContactHint")
        contact_hint.setWordWrap(True)
        contact_layout.addWidget(contact_hint)

        telegram_button = QPushButton("Открыть Telegram")
        telegram_button.setObjectName("TelegramButton")
        telegram_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(TELEGRAM_URL))
        )
        telegram_button.setMinimumHeight(40)
        contact_layout.addWidget(telegram_button)
        layout.addWidget(contact_card)

        title = QLabel("Диагностический отчёт")
        title.setObjectName("SupportTitle")
        layout.addWidget(title)

        description = QLabel(
            "Отчёт не содержит фотографии, теги или пароли, но включает сведения о системе "
            "и последние строки журнала."
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
            QWidget#FaqNavContent,
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
            QScrollArea#HelpScroll > QWidget > QWidget,
            QScrollArea#FaqNavScroll,
            QScrollArea#FaqNavScroll > QWidget > QWidget {
                background: transparent;
                border: none;
            }
            QPushButton#FaqNavButton {
                min-height: 34px;
                padding: 0 14px;
                color: #c7d1e0;
                background: #172033;
                border: 1px solid #30405a;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#FaqNavButton:hover {
                color: #ffffff;
                background: #201a35;
                border-color: #6d3fc0;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px 0;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 7px;
                margin: 0 4px;
            }
            QScrollBar::handle:vertical,
            QScrollBar::handle:horizontal {
                background: #5b35a6;
                min-height: 34px;
                min-width: 34px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical,
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
                border: none;
                width: 0;
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
        executable_dir = Path(sys.executable).resolve().parent
        bundled_ffmpeg = executable_dir / "ffmpeg.exe"
        ffmpeg_path = (
            str(bundled_ffmpeg)
            if bundled_ffmpeg.is_file()
            else shutil.which("ffmpeg") or "не найден"
        )
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
        candidates = [
            Path.home() / ".teggy" / "logs" / "teggy.log",
            Path.cwd() / "teggy.log",
            Path.cwd() / "app.log",
            Path.cwd() / "logs" / "teggy.log",
            Path.cwd() / "logs" / "app.log",
            Path.home() / ".teggy" / "teggy.log",
        ]
        for path in candidates:
            if not path.is_file():
                continue
            try:
                lines = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()
                return f"Файл: {path}\n" + "\n".join(lines[-100:])
            except OSError as exc:
                return f"Не удалось прочитать {path}: {exc}"
        return "Журнал не найден."