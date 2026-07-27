from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.version import display_version


class Dashboard(QWidget):
    """Главная страница с реальными быстрыми действиями Teggy."""

    navigate_requested = Signal(str)
    check_updates_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(900)

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
        cards.addWidget(
            self._quick_action(
                "Тегирование",
                "Фото, теги и метаданные",
                "Тегирование",
                "🏷",
            )
        )
        cards.addWidget(
            self._quick_action(
                "Яндекс Карты",
                "Фото, сторис и отзывы",
                "Яндекс Карты",
                "☁",
            )
        )
        cards.addWidget(
            self._quick_action(
                "Шаблоны",
                "Повторное использование полей",
                "Тегирование",
                "✦",
            )
        )
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
        button.clicked.connect(
            lambda checked=False, name=page: self.navigate_requested.emit(name)
        )
        box.addWidget(button)
        return card

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
        layout.addWidget(tip)
        layout.addStretch(1)

        button = QPushButton("Перейти к тегированию")
        button.setObjectName("DashboardActionButton")
        button.clicked.connect(
            lambda checked=False: self.navigate_requested.emit("Тегирование")
        )
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
