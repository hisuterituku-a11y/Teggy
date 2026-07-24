from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.paths import resource_path
from core.svg_loader import load_svg_icon


class ActionCard(QPushButton):
    activated = Signal(str)

    def __init__(
        self,
        title: str,
        description: str,
        icon_path: str,
        page: str,
        parent=None,
    ):
        super().__init__(parent)
        self._page = page
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "HomeActionCard")
        self.setMinimumHeight(148)
        self.clicked.connect(lambda: self.activated.emit(self._page))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(
            load_svg_icon(resource_path(icon_path), "#8B5CF6").pixmap(30, 30)
        )
        icon.setFixedSize(34, 34)
        icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(icon, alignment=Qt.AlignLeft)

        title_label = QLabel(title)
        title_label.setProperty("class", "HomeActionTitle")
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setProperty("class", "HomeActionDescription")
        description_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(description_label)
        layout.addStretch()


class HomePage(QWidget):
    page_requested = Signal(str)

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
        content.setProperty("class", "HomePageContent")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(24)

        eyebrow = QLabel("TEGGY WORKSPACE")
        eyebrow.setProperty("class", "EyebrowLabel")
        layout.addWidget(eyebrow)

        title = QLabel("Что делаем сегодня?")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title.setFont(font)
        title.setProperty("class", "PageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Все основные инструменты Teggy — в одном рабочем пространстве."
        )
        subtitle.setProperty("class", "PageSubtitle")
        layout.addWidget(subtitle)

        cards = QGridLayout()
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(16)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)

        items = [
            (
                "Метаданные",
                "Теги, EXIF, геоданные и пакетная обработка изображений.",
                "assets/icons/file-pen.svg",
                "metadata",
            ),
            (
                "Шаблоны",
                "Создавай и применяй готовые наборы данных для бизнеса.",
                "assets/icons/files.svg",
                "templates",
            ),
            (
                "Импорт из Яндекса",
                "Скачивание фото, историй и материалов из Яндекс Бизнеса.",
                "assets/icons/download.svg",
                "yandex",
            ),
            (
                "Открыть фотографии",
                "Перейди к рабочему набору изображений и продолжи обработку.",
                "assets/icons/images.svg",
                "photos",
            ),
        ]

        for index, item in enumerate(items):
            card = ActionCard(*item)
            card.activated.connect(self.page_requested)
            cards.addWidget(card, index // 2, index % 2)

        layout.addLayout(cards)
        layout.addStretch()
