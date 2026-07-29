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

FAQ_SECTIONS = [
    (
        "Начало работы",
        [
            (
                "Как добавить фотографии?",
                "Откройте раздел «Тегирование», выберите папку или перетащите фотографии в окно приложения.",
            ),
            (
                "В каком порядке обрабатываются фотографии?",
                "Файлы идут в том порядке, в котором они показаны в списке. Перед запуском проверьте последовательность фотографий в интерфейсе.",
            ),
        ],
    ),
    (
        "Теги и шаблоны",
        [
            (
                "Почему теги не записались?",
                "Проверьте, что файлы доступны для записи, не открыты другой программой и имеют поддерживаемый формат. Если ошибка повторяется, сохраните диагностический отчёт.",
            ),
            (
                "Где находятся шаблоны тегов?",
                "Шаблоны доступны из раздела тегирования. Их можно создавать, изменять и применять к выбранным фотографиям.",
            ),
        ],
    ),
    (
        "Яндекс Карты и видео",
        [
            (
                "Как импортировать материалы из Яндекс Карт?",
                "Откройте раздел «Яндекс Карты», вставьте ссылку на карточку или публикацию и запустите импорт.",
            ),
            (
                "Что делать, если видео не скачивается?",
                "Проверьте интернет-соединение, корректность ссылки и наличие FFmpeg. Затем повторите попытку. Если проблема остаётся, приложите диагностический отчёт.",
            ),
        ],
    ),
    (
        "Поддержка",
        [
            (
                "Как сообщить об ошибке?",
                "Перейдите на вкладку «Поддержка», сохраните диагностический отчёт и создайте обращение в GitHub Issues.",
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
        self.resize(780, 640)
        self.setMinimumSize(680, 540)

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
        layout.setSpacing(18)

        intro = QLabel("Краткие ответы на основные вопросы по работе с Teggy.")
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
                card_layout.setContentsMargins(18, 15, 18, 16)
                card_layout.setSpacing(8)

                question_label = QLabel(question)
                question_label.setObjectName("FaqQuestion")
                question_label.setWordWrap(True)
                card_layout.addWidget(question_label)

                accent = QFrame()
                accent.setObjectName("FaqAccent")
                accent.setFixedHeight(2)
                card_layout.addWidget(accent)

                answer_label = QLabel(answer)
                answer_label.setObjectName("FaqAnswer")
                answer_label.setWordWrap(True)
                answer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
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

        title = QLabel("Диагностический отчёт")
        title.setObjectName("SupportTitle")
        layout.addWidget(title)

        description = QLabel(
            "При обращении приложите этот отчёт. Он не содержит фотографии, теги или пароли, "
            "но включает сведения о системе и последние строки журнала."
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
        issues_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(ISSUES_URL)))
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
            QPushButton#HelpSectionButton:hover {
                color: #e5edf8;
                background: #172033;
                border-radius: 7px 7px 0 0;
            }
            QPushButton#HelpSectionButton:checked {
                color: #ffffff;
                background: #172033;
                border-bottom: 2px solid #7c3aed;
                border-radius: 7px 7px 0 0;
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
            QLabel#SupportDescription {
                color: #9da9bb;
                font-size: 13px;
            }
            QLabel#FaqSectionTitle {
                color: #8b9ab0;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 0 2px 2px 2px;
            }
            QLabel#SupportTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }
            QFrame#FaqCard {
                background: #151f32;
                border: 1px solid #2b3850;
                border-radius: 10px;
            }
            QFrame#FaqCard:hover {
                border-color: #4c3f78;
                background: #18233a;
            }
            QLabel#FaqQuestion {
                color: #f7f9fc;
                font-size: 14px;
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
            QPushButton#HelpCloseButton {
                min-height: 36px;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
            }
            QPushButton#HelpPrimaryButton {
                background: #6d3fc0;
                color: white;
                border: 1px solid #8150d4;
            }
            QPushButton#HelpPrimaryButton:hover {
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
        QMessageBox.information(self, "Готово", "Диагностический отчёт скопирован.")

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
            Path(path).write_text(self.report_view.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт:\n{exc}")
            return
        QMessageBox.information(self, "Готово", "Диагностический отчёт сохранён.")

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
        candidates = [
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
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                return f"Файл: {path}\n" + "\n".join(lines[-100:])
            except OSError as exc:
                return f"Не удалось прочитать {path}: {exc}"
        return "Журнал не найден."
