from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
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

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(22)
        self._shadow.setOffset(0, 7)
        self._shadow.setColor(QColor(0, 0, 0, 65))
        self.setGraphicsEffect(self._shadow)

        self._animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._animation.setDuration(170)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self and event.type() in (QEvent.Enter, QEvent.Leave):
            self._animation.stop()
            self._animation.setStartValue(self._shadow.blurRadius())
            self._animation.setEndValue(36 if event.type() == QEvent.Enter else 22)
            self._animation.start()
        return super().eventFilter(watched, event)


class QuickAction(QPushButton):
    def __init__(self, title: str, icon_path: str, parent=None):
        super().__init__(title, parent)
        self.setProperty("class", "QuickAction")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(52)
        self._icon_path = icon_path
        self.set_icon_color("#FFFFFF")

    def set_icon_color(self, color: str) -> None:
        self.setIcon(load_svg_icon(resource_path(self._icon_path), color))
        self.setIconSize(QSize(20, 20))


class StatCard(DashboardCard):
    def __init__(self, value: str, caption: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "StatCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setProperty("class", "StatValue")
        caption_label = QLabel(caption)
        caption_label.setProperty("class", "StatCaption")
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
        scroll.setProperty("class", "HomeScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        content = QWidget()
        content.setProperty("class", "HomeContent")
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 36)
        layout.setSpacing(22)

        eyebrow = QLabel("TEGGY WORKSPACE")
        eyebrow.setProperty("class", "DashboardEyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("Добро пожаловать в Teggy")
        title.setProperty("class", "DashboardTitle")
        layout.addWidget(title)

        subtitle = QLabel("Продолжайте последний проект или начните новую задачу.")
        subtitle.setProperty("class", "DashboardSubtitle")
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
        project_kicker.setProperty("class", "DashboardEyebrow")
        self.project_name = QLabel("Проектов пока нет")
        self.project_name.setProperty("class", "ProjectName")
        self.project_path = QLabel("Откройте папку с изображениями, чтобы начать работу")
        self.project_path.setProperty("class", "ProjectPath")
        self.project_path.setWordWrap(True)
        self.project_meta = QLabel("0 фотографий")
        self.project_meta.setProperty("class", "ProjectMeta")

        self.continue_button = QPushButton("Продолжить")
        self.continue_button.setProperty("class", "DashboardPrimaryButton")
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.setFixedHeight(42)
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
        actions_title.setProperty("class", "DashboardSectionTitle")
        actions_layout.addWidget(actions_title)

        self.quick_actions = [
            QuickAction("Открыть папку", "assets/icons/folder-open.svg"),
            QuickAction("Импорт из Яндекса", "assets/icons/download.svg"),
            QuickAction("Шаблоны", "assets/icons/files.svg"),
            QuickAction("Создать шаблон", "assets/icons/file-pen.svg"),
        ]
        self.quick_actions[0].clicked.connect(self.open_folder_requested)
        self.quick_actions[1].clicked.connect(lambda: self.page_requested.emit("yandex"))
        self.quick_actions[2].clicked.connect(lambda: self.page_requested.emit("templates"))
        self.quick_actions[3].clicked.connect(self.create_template_requested)
        for button in self.quick_actions:
            actions_layout.addWidget(button)
        actions_layout.addStretch()
        top.addWidget(actions_card, 0, 1)

        section = QLabel("Статистика")
        section.setProperty("class", "DashboardSectionTitle")
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

    def apply_theme_colors(self, accent: str, icon: str) -> None:
        color = accent or icon or "#FFFFFF"
        for action in self.quick_actions:
            action.set_icon_color(color)

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
