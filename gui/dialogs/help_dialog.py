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
    QTabWidget,
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
        self.resize(820, 680)
        self.setMinimumSize(700, 560)

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
        content_layout.setContentsMargins(22, 18, 22, 18)
        content_layout.setSpacing(14)

        tabs = QTabWidget()
        tabs.setObjectName("HelpTabs")
        tabs.addTab(self._build_faq_tab(), "FAQ")
        tabs.addTab(self._build_support_tab(), "Поддержка")
        content_layout.addWidget(tabs, 1)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("HelpCloseButton")
        close_button.clicked.connect(self.reject)
        content_layout.addWidget(close_button)

        shell_layout.addWidget(content, 1)
        self._apply_styles()

    def _build_faq_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("HelpTab")
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
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        intro = QLabel("Краткие ответы на основные вопросы по работе с Teggy.")
        intro.setObjectName("FaqIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        for section_title, questions in FAQ_SECTIONS:
            section_label = QLabel(section_title)
            section_label.setObjectName("FaqSectionTitle")
            layout.addWidget(section_label)

            for question, answer in questions:
                card = QFrame()
                card.setObjectName("FaqCard")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(16, 13, 16, 14)
                card_layout.setSpacing(7)

                question_label = QLabel(question)
                question_label.setObjectName("FaqQuestion")
                question_label.setWordWrap(True)
                card_layout.addWidget(question_label)

                answer_label = QLabel(answer)
                answer_label.setObjectName("FaqAnswer")
                answer_label.setWordWrap(True)
                answer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                card_layout.addWidget(answer_label)

                layout.addWidget(card)

        layout.addStretch(1)
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)
        return tab

    def _build_support_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("HelpTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
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

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        copy_button = QPushButton("Скопировать отчёт")
        copy_button.setObjectName("HelpPrimaryButton")
        copy_button.clicked.connect(self._copy_report)
        buttons.addWidget(copy_button)

        save_button = QPushButton("Сохранить отчёт…")
        save_button.setObjectName("HelpSecondaryButton")
        save_button.clicked.connect(self._save_report)
        buttons.addWidget(save_button)

        refresh_button = QPushButton("Обновить")
        refresh_button.setObjectName("HelpSecondaryButton")
        refresh_button.clicked.connect(self._refresh_report)
        buttons.addWidget(refresh_button)

        layout.addLayout(buttons)

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
        layout.addLayout(links)

        return tab

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#HelpDialogShell {
                background: #15181d;
                border: 1px solid #2b313a;
                border-radius: 14px;
            }
            QWidget#HelpDialogContent,
            QWidget#HelpTab,
            QWidget#FaqContent {
                background: #15181d;
            }
            QTabWidget#HelpTabs::pane {
                border: 1px solid #2b313a;
                border-radius: 10px;
                background: #15181d;
                top: -1px;
            }
            QTabWidget#HelpTabs QTabBar::tab {
                background: #1d2229;
                color: #aeb7c2;
                border: 1px solid #2b313a;
                padding: 9px 22px;
                min-width: 110px;
            }
            QTabWidget#HelpTabs QTabBar::tab:selected {
                background: #252c35;
                color: #ffffff;
                border-bottom: 2px solid #3b82f6;
            }
            QScrollArea#HelpScroll {
                background: transparent;
                border: none;
            }
            QLabel#FaqIntro,
            QLabel#SupportDescription {
                color: #9da7b3;
                font-size: 13px;
            }
            QLabel#FaqSectionTitle,
            QLabel#SupportTitle {
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
                padding-top: 4px;
                padding-bottom: 2px;
                border-bottom: 1px solid #303741;
            }
            QFrame#FaqCard {
                background: #1b2027;
                border: 1px solid #2d343e;
                border-radius: 10px;
            }
            QLabel#FaqQuestion {
                color: #f4f7fb;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#FaqAnswer {
                color: #aeb7c2;
                font-size: 13px;
                line-height: 1.4;
            }
            QTextBrowser#ReportView {
                background: #101318;
                color: #d7dde5;
                border: 1px solid #2b313a;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QPushButton#HelpPrimaryButton,
            QPushButton#HelpSecondaryButton,
            QPushButton#HelpCloseButton {
                min-height: 34px;
                border-radius: 8px;
                padding: 0 16px;
            }
            QPushButton#HelpPrimaryButton {
                background: #2563eb;
                color: white;
                border: 1px solid #3b82f6;
                font-weight: 600;
            }
            QPushButton#HelpPrimaryButton:hover {
                background: #2f6ff0;
            }
            QPushButton#HelpSecondaryButton,
            QPushButton#HelpCloseButton {
                background: #1d2229;
                color: #d7dde5;
                border: 1px solid #333b46;
            }
            QPushButton#HelpSecondaryButton:hover,
            QPushButton#HelpCloseButton:hover {
                background: #272e38;
            }
            QPushButton#HelpCloseButton {
                min-width: 120px;
                align-self: center;
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
