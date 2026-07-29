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
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.version import display_version
from gui.components.window_title_bar import WindowTitleBar


ISSUES_URL = "https://github.com/hisuterituku-a11y/Teggy/issues"
REPOSITORY_URL = "https://github.com/hisuterituku-a11y/Teggy"


FAQ_HTML = """
<h2>Частые вопросы</h2>
<h3>Как добавить фотографии?</h3>
<p>Откройте раздел «Тегирование», выберите папку или перетащите фотографии в окно приложения.</p>

<h3>В каком порядке обрабатываются фотографии?</h3>
<p>Файлы обрабатываются в порядке, в котором их возвращает выбранная папка. Перед запуском проверьте список фотографий в интерфейсе.</p>

<h3>Почему теги не записались?</h3>
<p>Проверьте, что файлы доступны для записи, не открыты другой программой и имеют поддерживаемый формат. Повторите обработку и сохраните отчёт для поддержки, если ошибка остаётся.</p>

<h3>Как импортировать материалы из Яндекс Карт?</h3>
<p>Откройте раздел «Яндекс Карты», вставьте ссылку на карточку или публикацию и запустите импорт. Для видео в системе должен быть доступен FFmpeg.</p>

<h3>Где находятся шаблоны тегов?</h3>
<p>Шаблоны доступны из раздела тегирования. Их можно создавать, изменять и применять к выбранным фотографиям.</p>

<h3>Что делать, если видео не скачивается?</h3>
<p>Проверьте интернет-соединение, корректность ссылки и наличие FFmpeg. Затем повторите попытку. Если проблема сохраняется, приложите диагностический отчёт.</p>

<h3>Как сообщить об ошибке?</h3>
<p>Перейдите на вкладку «Поддержка», сохраните диагностический отчёт и создайте обращение в GitHub Issues.</p>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Помощь и поддержка")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(720, 620)
        self.setMinimumSize(620, 520)

        shell = QWidget(self)
        shell.setObjectName("AboutDialog")

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
        content.setObjectName("AboutContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(14)

        tabs = QTabWidget()
        tabs.addTab(self._build_faq_tab(), "FAQ")
        tabs.addTab(self._build_support_tab(), "Поддержка")
        content_layout.addWidget(tabs, 1)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("AboutSecondaryButton")
        close_button.clicked.connect(self.reject)
        content_layout.addWidget(close_button)

        shell_layout.addWidget(content, 1)

    def _build_faq_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(FAQ_HTML)
        layout.addWidget(browser)
        return tab

    def _build_support_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        description = QLabel(
            "При обращении приложите диагностический отчёт. Он не содержит фотографии, "
            "теги или пароли, но включает сведения о системе и последние строки журнала."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.report_view = QTextBrowser()
        self.report_view.setPlainText(self._build_report())
        layout.addWidget(self.report_view, 1)

        buttons = QHBoxLayout()

        copy_button = QPushButton("Скопировать отчёт")
        copy_button.setObjectName("AboutPrimaryButton")
        copy_button.clicked.connect(self._copy_report)
        buttons.addWidget(copy_button)

        save_button = QPushButton("Сохранить отчёт…")
        save_button.clicked.connect(self._save_report)
        buttons.addWidget(save_button)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._refresh_report)
        buttons.addWidget(refresh_button)

        layout.addLayout(buttons)

        links = QHBoxLayout()
        issues_button = QPushButton("Создать обращение")
        issues_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(ISSUES_URL)))
        links.addWidget(issues_button)

        repository_button = QPushButton("Открыть GitHub")
        repository_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(REPOSITORY_URL))
        )
        links.addWidget(repository_button)
        layout.addLayout(links)

        return tab

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
