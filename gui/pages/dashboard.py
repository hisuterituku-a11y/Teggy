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
    """Функциональная главная без выдуманной статистики и демо-задач."""

    navigate_requested = Signal(str)
    check_updates_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("#DashboardPage { background: #070B18; }")
        self.setMinimumWidth(900)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        title = QLabel("Рабочий стол")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "Основные действия Teggy без декоративной статистики и прочих уверенных выдумок."
        )
        subtitle.setObjectName("CardSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        actions = QGridLayout()
        actions.setHorizontalSpacing(18)
        actions.setVerticalSpacing(18)

        actions.addWidget(
            self._action_card(
                title="Тегирование фотографий",
                description="Выберите папки, заполните метаданные и запустите обработку изображений.",
                button_text="Открыть тегирование",
                page_name="Тегирование",
            ),
            0,
            0,
        )
        actions.addWidget(
            self._action_card(
                title="Яндекс Карты",
                description="Загрузите фотографии, отзывы и данные карточки организации в папку проекта.",
                button_text="Открыть Яндекс Карты",
                page_name="Яндекс Карты",
            ),
            0,
            1,
        )
        actions.addWidget(
            self._action_card(
                title="Настройки интерфейса",
                description="Верните безопасный размер окна и управляйте параметрами приложения.",
                button_text="Открыть настройки",
                page_name="Настройки",
            ),
            1,
            0,
        )
        actions.addWidget(self._status_card(), 1, 1)

        actions.setColumnStretch(0, 1)
        actions.setColumnStretch(1, 1)
        root.addLayout(actions)

        scope_card = QFrame()
        scope_card.setObjectName("PhotoPanel")
        scope_layout = QVBoxLayout(scope_card)
        scope_layout.setContentsMargins(24, 22, 24, 22)
        scope_layout.setSpacing(10)

        scope_title = QLabel("Что уже работает")
        scope_title.setObjectName("CardTitle")
        scope_layout.addWidget(scope_title)

        scope_text = QLabel(
            "• тегирование и запись метаданных\n"
            "• загрузка данных из Яндекс Карт\n"
            "• шаблоны и теги в боковой навигации\n"
            "• проверка обновлений и система версий"
        )
        scope_text.setObjectName("CardSubtitle")
        scope_text.setWordWrap(True)
        scope_layout.addWidget(scope_text)

        root.addWidget(scope_card)
        root.addStretch(1)

    def _action_card(
        self,
        *,
        title: str,
        description: str,
        button_text: str,
        page_name: str,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        card.setMinimumHeight(190)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("CardTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)

        body = QLabel(description)
        body.setObjectName("CardSubtitle")
        body.setWordWrap(True)
        layout.addWidget(body)
        layout.addStretch(1)

        button = QPushButton(button_text)
        button.setObjectName("PrimaryButton")
        button.clicked.connect(
            lambda checked=False, name=page_name: self.navigate_requested.emit(name)
        )
        layout.addWidget(button)

        return card

    def _status_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PhotoPanel")
        card.setMinimumHeight(190)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        heading = QLabel("Состояние приложения")
        heading.setObjectName("CardTitle")
        layout.addWidget(heading)

        version_row = QHBoxLayout()
        version_label = QLabel("Текущая версия")
        version_label.setObjectName("CardSubtitle")
        version_value = QLabel(display_version())
        version_value.setObjectName("CardTitle")
        version_row.addWidget(version_label)
        version_row.addStretch(1)
        version_row.addWidget(version_value)
        layout.addLayout(version_row)
        layout.addStretch(1)

        check_button = QPushButton("Проверить обновления")
        check_button.setObjectName("PrimaryButton")
        check_button.clicked.connect(self.check_updates_requested)
        layout.addWidget(check_button)

        return card
