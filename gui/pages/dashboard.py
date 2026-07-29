from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.statistics import StatisticsStore
from core.version import display_version


class StatisticsDonut(QWidget):
    COLORS = (
        QColor("#9B5CFF"),
        QColor("#C274FF"),
        QColor("#5D8CFF"),
        QColor("#FF668F"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(116, 116)
        self._values = [0, 0, 0, 0]
        self._progress = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(950)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self._set_progress)

    def set_values(self, values: list[int]) -> None:
        self._values = [max(0, int(value)) for value in values]
        self._animation.stop()
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()

    def _set_progress(self, value) -> None:
        self._progress = float(value)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(12, 12, self.width() - 24, self.height() - 24)
        width = 11

        painter.setPen(QPen(QColor(70, 82, 132, 95), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 0, 360 * 16)

        total = sum(self._values)
        start_angle = 90 * 16
        if total > 0:
            gap = 4 * 16
            for value, color in zip(self._values, self.COLORS):
                if value <= 0:
                    continue
                span = int((value / total) * 360 * 16 * self._progress)
                painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawArc(rect, start_angle, -(max(0, span - gap)))
                start_angle -= span
        else:
            painter.setPen(QPen(self.COLORS[0], width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(rect, 90 * 16, int(-300 * 16 * self._progress))

        painter.setPen(QColor("#FFFFFF"))
        font = QFont(self.font())
        font.setBold(True)
        font.setPointSize(17)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, -7, 0, 0), Qt.AlignmentFlag.AlignCenter, f"{total:,}".replace(",", " "))

        painter.setPen(QColor("#9AA8D2"))
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, 27, 0, 0), Qt.AlignmentFlag.AlignCenter, "файлов")


class Dashboard(QWidget):
    """Главная страница с быстрыми действиями и статистикой Teggy."""

    navigate_requested = Signal(str)
    check_updates_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(900)

        self._statistics_store = StatisticsStore()
        self._stat_labels: dict[str, QLabel] = {}
        self._stat_animations: list[QVariantAnimation] = []
        self._statistics_effect: QGraphicsOpacityEffect | None = None
        self._statistics_fade: QVariantAnimation | None = None
        self._donut: StatisticsDonut | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        welcome = QLabel("Добро пожаловать в Teggy")
        welcome.setObjectName("DashboardWelcome")
        root.addWidget(welcome)

        subtitle = QLabel(
            "Подготовьте фотографии, добавьте метаданные и загрузите материалы из Яндекс Карт."
        )
        subtitle.setObjectName("DashboardSubtitle")
        root.addWidget(subtitle)

        content = QGridLayout()
        content.setHorizontalSpacing(18)
        content.setVerticalSpacing(18)
        content.setColumnStretch(0, 3)
        content.setColumnStretch(1, 2)
        content.addWidget(self._quick_start_panel(), 0, 0)
        content.addWidget(self._status_panel(), 0, 1)
        content.addWidget(self._workflow_panel(), 1, 0)
        content.addWidget(self._tips_panel(), 1, 1)
        root.addLayout(content)
        root.addStretch(1)

        QTimer.singleShot(120, self.refresh_statistics)

    def _quick_start_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("DashboardHero")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("Быстрый старт")
        title.setObjectName("DashboardPanelTitle")
        layout.addWidget(title)

        hint = QLabel("Выберите действие для начала работы")
        hint.setObjectName("DashboardPanelText")
        layout.addWidget(hint)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(self._quick_action("Тегирование", "Фото, теги и метаданные", "Тегирование", "🏷"))
        cards.addWidget(self._quick_action("Яндекс Карты", "Фото, сторис и отзывы", "Яндекс Карты", "☁"))
        cards.addWidget(self._statistics_panel())
        layout.addLayout(cards)
        return panel

    def _quick_action(self, title: str, text: str, page: str, icon: str) -> QFrame:
        card = QFrame()
        card.setObjectName("DashboardActionCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        box = QVBoxLayout(card)
        box.setContentsMargins(16, 16, 16, 16)
        box.setSpacing(7)

        icon_label = QLabel(icon)
        icon_label.setObjectName("DashboardActionIcon")
        box.addWidget(icon_label)

        heading = QLabel(title)
        heading.setObjectName("DashboardActionTitle")
        box.addWidget(heading)

        description = QLabel(text)
        description.setObjectName("DashboardPanelText")
        description.setWordWrap(True)
        box.addWidget(description)
        box.addStretch(1)

        button = QPushButton("Открыть")
        button.setObjectName("DashboardActionButton")
        button.clicked.connect(lambda checked=False, name=page: self.navigate_requested.emit(name))
        box.addWidget(button)
        return card

    def _statistics_panel(self) -> QFrame:
        card = QFrame()
        card.setObjectName("DashboardStatisticsCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        card.setStyleSheet(
            """
            QFrame#DashboardStatisticsCard {
                background-color: rgba(18, 25, 54, 218);
                border: 1px solid rgba(145, 91, 255, 165);
                border-radius: 16px;
            }
            QLabel#DashboardStatisticsTitle { color: #ffffff; font-size: 15px; font-weight: 700; }
            QLabel#DashboardStatisticsName { color: #aab6dd; font-size: 10px; }
            QLabel#DashboardStatisticsValue { color: #ffffff; font-size: 15px; font-weight: 800; }
            QLabel#DashboardStatisticsDot { font-size: 14px; }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(5)

        title = QLabel("Статистика")
        title.setObjectName("DashboardStatisticsTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self._donut = StatisticsDonut(card)
        layout.addWidget(self._donut, 0, Qt.AlignmentFlag.AlignHCenter)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        rows = (
            ("downloaded", "Скачано", "#9B5CFF"),
            ("tagged", "Протегировано", "#C274FF"),
            ("converted", "В JPG", "#5D8CFF"),
            ("failed", "Ошибок", "#FF668F"),
        )
        for index, (key, caption, color) in enumerate(rows):
            row = index // 2
            column = (index % 2) * 2

            text_box = QVBoxLayout()
            text_box.setSpacing(0)
            line = QHBoxLayout()
            line.setSpacing(3)
            dot = QLabel("●")
            dot.setObjectName("DashboardStatisticsDot")
            dot.setStyleSheet(f"color: {color};")
            name = QLabel(caption)
            name.setObjectName("DashboardStatisticsName")
            line.addWidget(dot)
            line.addWidget(name)
            line.addStretch(1)

            value = QLabel("0")
            value.setObjectName("DashboardStatisticsValue")
            self._stat_labels[key] = value
            text_box.addLayout(line)
            text_box.addWidget(value)
            grid.addLayout(text_box, row, column)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(2, 1)
        layout.addLayout(grid)

        self._statistics_effect = QGraphicsOpacityEffect(card)
        self._statistics_effect.setOpacity(0.0)
        card.setGraphicsEffect(self._statistics_effect)
        return card

    def refresh_statistics(self) -> None:
        statistics = self._statistics_store.load()
        targets = {
            "downloaded": statistics.downloaded,
            "tagged": statistics.tagged,
            "converted": statistics.converted,
            "failed": statistics.failed,
        }

        if self._donut is not None:
            self._donut.set_values(list(targets.values()))

        for animation in self._stat_animations:
            animation.stop()
        self._stat_animations.clear()

        for index, (key, target) in enumerate(targets.items()):
            label = self._stat_labels.get(key)
            if label is None:
                continue
            try:
                start_value = int(label.text().replace(" ", ""))
            except ValueError:
                start_value = 0

            animation = QVariantAnimation(self)
            animation.setStartValue(start_value)
            animation.setEndValue(target)
            animation.setDuration(620 + index * 70)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.valueChanged.connect(
                lambda value, target_label=label: target_label.setText(f"{int(value):,}".replace(",", " "))
            )
            animation.start()
            self._stat_animations.append(animation)

        if self._statistics_effect is not None and self._statistics_effect.opacity() < 1.0:
            self._statistics_fade = QVariantAnimation(self)
            self._statistics_fade.setStartValue(0.0)
            self._statistics_fade.setEndValue(1.0)
            self._statistics_fade.setDuration(420)
            self._statistics_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._statistics_fade.valueChanged.connect(self._statistics_effect.setOpacity)
            self._statistics_fade.start()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_statistics()

    def _status_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("DashboardPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Состояние приложения")
        title.setObjectName("DashboardPanelTitle")
        layout.addWidget(title)

        version_caption = QLabel("Установленная версия")
        version_caption.setObjectName("DashboardPanelText")
        layout.addWidget(version_caption)

        version = QLabel(display_version())
        version.setObjectName("DashboardVersion")
        layout.addWidget(version)

        self.update_status_label = QLabel("Teggy готов к работе")
        self.update_status_label.setObjectName("DashboardSuccessText")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setMinimumHeight(42)
        layout.addWidget(self.update_status_label)
        layout.addStretch(1)

        self.check_updates_button = QPushButton("Проверить обновления")
        self.check_updates_button.setObjectName("DashboardSecondaryButton")
        self.check_updates_button.clicked.connect(self.check_updates_requested)
        layout.addWidget(self.check_updates_button)
        return panel

    def _workflow_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("DashboardPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Рабочий процесс")
        title.setObjectName("DashboardPanelTitle")
        layout.addWidget(title)

        for number, heading, text in (
            ("1", "Загрузите фотографии", "Выберите папку или отдельные изображения."),
            ("2", "Примените шаблон", "Заполните метаданные один раз и используйте повторно."),
            ("3", "Запустите обработку", "Teggy подготовит итоговые файлы в отдельной папке."),
        ):
            row = QFrame()
            row.setObjectName("DashboardWorkflowRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(14, 11, 14, 11)
            badge = QLabel(number)
            badge.setObjectName("DashboardStepBadge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedSize(30, 30)
            row_layout.addWidget(badge)
            text_box = QVBoxLayout()
            head = QLabel(heading)
            head.setObjectName("DashboardActionTitle")
            desc = QLabel(text)
            desc.setObjectName("DashboardPanelText")
            desc.setWordWrap(True)
            text_box.addWidget(head)
            text_box.addWidget(desc)
            row_layout.addLayout(text_box, 1)
            layout.addWidget(row)
        return panel

    def _tips_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("DashboardPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Полезно знать")
        title.setObjectName("DashboardPanelTitle")
        layout.addWidget(title)

        tip = QLabel(
            "Создайте шаблоны для разных типов бизнеса. После загрузки из Яндекс Карт "
            "их можно применять автоматически ко всем новым фотографиям."
        )
        tip.setObjectName("DashboardTip")
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        tip.setMinimumHeight(96)
        tip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        layout.addWidget(tip)
        layout.addStretch(1)

        button = QPushButton("Перейти к тегированию")
        button.setObjectName("DashboardActionButton")
        button.clicked.connect(lambda checked=False: self.navigate_requested.emit("Тегирование"))
        layout.addWidget(button)
        return panel

    def set_update_checking(self) -> None:
        self.update_status_label.setText("Проверяем обновления…")
        self.check_updates_button.setEnabled(False)
        self.check_updates_button.setText("Проверка…")

    def set_update_result(self, message: str) -> None:
        self.update_status_label.setText(message)
        self.check_updates_button.setEnabled(True)
        self.check_updates_button.setText("Проверить обновления")
