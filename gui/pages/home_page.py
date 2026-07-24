from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.paths import resource_path
from core.settings import Settings
from core.svg_loader import load_svg_icon
from core.template_manager import TemplateManager

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class DashboardCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "DashboardCard")
        self.setStyleSheet(
            "QFrame[class='DashboardCard'] {"
            "background: rgba(28, 31, 39, 235);"
            "border: 1px solid rgba(255,255,255,24);"
            "border-radius: 18px;}"
        )

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(self._shadow)

        self._animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._animation.setDuration(160)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self and event.type() in (QEvent.Enter, QEvent.Leave):
            self._animation.stop()
            self._animation.setStartValue(self._shadow.blurRadius())
            self._animation.setEndValue(38 if event.type() == QEvent.Enter else 24)
            self._animation.start()
        return super().eventFilter(watched, event)


class QuickAction(QPushButton):
    def __init__(self, title: str, icon_path: str, parent=None):
        super().__init__(title, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setIcon(load_svg_icon(resource_path(icon_path), "#F59E0B"))
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet(
            "QPushButton {"
            "background: rgba(255,255,255,10);"
            "border: 1px solid rgba(255,255,255,22);"
            "border-radius: 12px; padding: 0 16px;"
            "text-align: left; font-weight: 600;}"
            "QPushButton:hover {"
            "background: rgba(245,158,11,28);"
            "border-color: rgba(245,158,11,100);}"
            "QPushButton:pressed {background: rgba(245,158,11,42);}"
        )


class StatCard(DashboardCard):
    def __init__(self, value: str, caption: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: 800;")
        caption_label = QLabel(caption)
        caption_label.setStyleSheet("color: rgba(255,255,255,145); font-size: 12px;")

        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)


class HomePage(QWidget):
    page_requested = Signal(str)
    open_folder_requested = Signal()
    create_template_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "HomePage")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 36)
        layout.setSpacing(22)

        eyebrow = QLabel("TEGGY WORKSPACE")
        eyebrow.setStyleSheet(
            "color: #F59E0B; font-size: 11px; font-weight: 800; letter-spacing: 2px;"
        )
        layout.addWidget(eyebrow)

        title = QLabel("Добро пожаловать в Teggy")
        title.setStyleSheet("font-size: 28px; font-weight: 800;")
        layout.addWidget(title)

        subtitle = QLabel("Продолжайте последний проект или начните новую задачу.")
        subtitle.setStyleSheet("color: rgba(255,255,255,150); font-size: 14px;")
        layout.addWidget(subtitle)

        top = QGridLayout()
        top.setHorizontalSpacing(18)
        top.setVerticalSpacing(18)
        top.setColumnStretch(0, 3)
        top.setColumnStretch(1, 2)
        layout.addLayout(top)

        self.project_card = DashboardCard()
        project_layout = QVBoxLayout(self.project_card)
        project_layout.setContentsMargins(24, 22, 24, 22)
        project_layout.setSpacing(10)

        project_kicker = QLabel("ПОСЛЕДНИЙ ПРОЕКТ")
        project_kicker.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 800;")
        self.project_name = QLabel("Проектов пока нет")
        self.project_name.setStyleSheet("font-size: 20px; font-weight: 750;")
        self.project_path = QLabel("Откройте папку с изображениями, чтобы начать работу")
        self.project_path.setWordWrap(True)
        self.project_path.setStyleSheet("color: rgba(255,255,255,140);")
        self.project_meta = QLabel("0 фотографий")
        self.project_meta.setStyleSheet("color: rgba(255,255,255,175); font-weight: 600;")

        self.continue_button = QPushButton("Продолжить")
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.setFixedHeight(42)
        self.continue_button.setStyleSheet(
            "QPushButton {background: #F59E0B; color: #17191F; border: 0;"
            "border-radius: 11px; padding: 0 20px; font-weight: 800;}"
            "QPushButton:hover {background: #FBBF24;}"
            "QPushButton:disabled {background: rgba(255,255,255,20);"
            "color: rgba(255,255,255,80);}"
        )
        self.continue_button.clicked.connect(lambda: self.page_requested.emit("metadata"))

        project_layout.addWidget(project_kicker)
        project_layout.addWidget(self.project_name)
        project_layout.addWidget(self.project_path)
        project_layout.addWidget(self.project_meta)
        project_layout.addStretch()
        project_layout.addWidget(self.continue_button, alignment=Qt.AlignLeft)
        top.addWidget(self.project_card, 0, 0)

        actions_card = DashboardCard()
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(10)

        actions_title = QLabel("Быстрые действия")
        actions_title.setStyleSheet("font-size: 17px; font-weight: 750;")
        actions_layout.addWidget(actions_title)

        open_folder = QuickAction("Открыть папку", "assets/icons/folder-open.svg")
        open_folder.clicked.connect(self.open_folder_requested)
        yandex = QuickAction("Импорт из Яндекса", "assets/icons/download.svg")
        yandex.clicked.connect(lambda: self.page_requested.emit("yandex"))
        templates = QuickAction("Шаблоны", "assets/icons/files.svg")
        templates.clicked.connect(lambda: self.page_requested.emit("templates"))
        create_template = QuickAction("Создать шаблон", "assets/icons/file-pen.svg")
        create_template.clicked.connect(self.create_template_requested)

        for button in (open_folder, yandex, templates, create_template):
            actions_layout.addWidget(button)
        actions_layout.addStretch()
        top.addWidget(actions_card, 0, 1)

        section = QLabel("Статистика")
        section.setStyleSheet("font-size: 17px; font-weight: 750; margin-top: 4px;")
        layout.addWidget(section)

        stats = QGridLayout()
        stats.setHorizontalSpacing(14)
        self.processed_stat = StatCard("0", "обработано файлов")
        self.templates_stat = StatCard("0", "создано шаблонов")
        self.last_run_stat = StatCard("—", "последний запуск")
        stats.addWidget(self.processed_stat, 0, 0)
        stats.addWidget(self.templates_stat, 0, 1)
        stats.addWidget(self.last_run_stat, 0, 2)
        for column in range(3):
            stats.setColumnStretch(column, 1)
        layout.addLayout(stats)
        layout.addStretch()

        self.refresh()

    def refresh(self) -> None:
        folder = Settings.get_last_folder()
        path = Path(folder) if folder else None
        exists = bool(path and path.exists() and path.is_dir())
        count = 0

        if exists:
            try:
                count = sum(
                    1
                    for item in path.iterdir()
                    if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
                )
            except OSError:
                count = 0
            self.project_name.setText(path.name or str(path))
            self.project_path.setText(str(path))
        else:
            self.project_name.setText("Проектов пока нет")
            self.project_path.setText("Откройте папку с изображениями, чтобы начать работу")

        suffix = "фотография" if count == 1 else "фотографий"
        self.project_meta.setText(f"{count} {suffix}")
        self.continue_button.setEnabled(exists)

        stats = Settings.get_dashboard_stats()
        self.processed_stat.value_label.setText(str(stats.get("processed_files", 0)))

        try:
            templates_count = len(TemplateManager.list_templates())
        except Exception:
            templates_count = int(stats.get("templates_created", 0) or 0)
        self.templates_stat.value_label.setText(str(templates_count))

        last_run = stats.get("last_run", "")
        if last_run:
            try:
                last_run = datetime.fromisoformat(last_run).strftime("%d.%m.%Y %H:%M")
            except (TypeError, ValueError):
                pass
        self.last_run_stat.value_label.setText(last_run or "—")
