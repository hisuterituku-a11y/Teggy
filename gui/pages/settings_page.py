from __future__ import annotations

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SettingsPage(QWidget):
    reset_interface_requested = Signal()
    theme_changed = Signal(str)
    check_updates_requested = Signal()

    THEME_LABELS = {
        "default": ("🌙  Тёмная", "Фирменная тёмная тема Teggy с фиолетовым акцентом"),
        "light": ("☀️  Светлая", "Чистый светлый интерфейс с мягкими тенями"),
        "corporate": ("💼  Корпоративная", "Графит, строгая геометрия и оранжевый акцент"),
        "frogs": ("🐸  Лягушки", "Глубокий зелёный, мята и уютная болотная палитра"),
        "sakura": ("🌸  Сакура", "Тёплая тема с ветвями, веерами, цветами и облаками"),
    }

    def __init__(self, available_themes: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self.setMinimumWidth(760)
        self._settings = QSettings("Teggy", "Teggy")
        self._available_themes = available_themes or ["default"]
        self._theme_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 28)
        root.setSpacing(18)

        title = QLabel("Настройки")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        subtitle = QLabel("Оформление, обновления и параметры интерфейса Teggy.")
        subtitle.setObjectName("CardSubtitle")
        root.addWidget(subtitle)

        root.addWidget(self._build_theme_card())
        root.addWidget(self._build_updates_card())
        root.addWidget(self._build_interface_card())
        root.addStretch(1)

    def set_selected_theme(self, theme_name: str) -> None:
        button = self._theme_buttons.get(theme_name)
        if button is not None and not button.isChecked():
            button.setChecked(True)

    def _build_theme_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Оформление")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        description = QLabel("Выберите тему. Карточка нажимается целиком, изменения применяются сразу.")
        description.setObjectName("CardSubtitle")
        description.setWordWrap(True)
        layout.addWidget(description)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        group = QButtonGroup(self)
        group.setExclusive(True)

        current_theme = str(self._settings.value("appearance/theme", "default"))
        for index, theme_name in enumerate(self._available_themes):
            label, details = self.THEME_LABELS.get(theme_name, (theme_name, "Тема Teggy"))
            button = QPushButton(f"{label}\n{details}")
            button.setObjectName("ThemeChoiceButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setFixedHeight(82)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setProperty("themeName", theme_name)
            group.addButton(button)
            self._theme_buttons[theme_name] = button

            def choose_theme(checked: bool, name=theme_name) -> None:
                if checked:
                    self._settings.setValue("appearance/theme", name)
                    self.theme_changed.emit(name)

            button.toggled.connect(choose_theme)
            button.setChecked(theme_name == current_theme)
            row = index // 2
            column = index % 2
            grid.setRowMinimumHeight(row, 82)
            grid.addWidget(button, row, column)

        if current_theme not in self._theme_buttons and "default" in self._theme_buttons:
            self._theme_buttons["default"].setChecked(True)

        layout.addLayout(grid)
        return card

    def _build_updates_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Обновления и уведомления")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self.auto_updates_checkbox = QCheckBox("Проверять обновления при запуске")
        self.auto_updates_checkbox.setObjectName("SettingsCheckBox")
        self.auto_updates_checkbox.setChecked(
            self._settings.value("updates/check_on_startup", True, type=bool)
        )
        self.auto_updates_checkbox.toggled.connect(
            lambda enabled: self._settings.setValue("updates/check_on_startup", enabled)
        )
        layout.addWidget(self.auto_updates_checkbox)

        self.release_notifications_checkbox = QCheckBox("Показывать уведомления о новых версиях")
        self.release_notifications_checkbox.setObjectName("SettingsCheckBox")
        self.release_notifications_checkbox.setChecked(
            self._settings.value("updates/show_notifications", True, type=bool)
        )
        self.release_notifications_checkbox.toggled.connect(
            lambda enabled: self._settings.setValue("updates/show_notifications", enabled)
        )
        layout.addWidget(self.release_notifications_checkbox)

        row = QHBoxLayout()
        check_button = QPushButton("Проверить обновления сейчас")
        check_button.setObjectName("PrimaryButton")
        check_button.clicked.connect(self.check_updates_requested)
        row.addWidget(check_button)
        row.addStretch(1)
        layout.addLayout(row)
        return card

    def _build_interface_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Интерфейс")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        description = QLabel("Вернуть окно к безопасному размеру и расположить его по центру экрана.")
        description.setObjectName("CardSubtitle")
        description.setWordWrap(True)
        layout.addWidget(description)

        row = QHBoxLayout()
        reset_button = QPushButton("Сбросить размер и положение окна")
        reset_button.setObjectName("YandexActionButton")
        reset_button.clicked.connect(self.reset_interface_requested)
        row.addWidget(reset_button)
        row.addStretch(1)
        layout.addLayout(row)
        return card
