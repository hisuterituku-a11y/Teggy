from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt


class Card(QFrame):
    """Базовая карточка с отступами и скруглением."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setAttribute(Qt.WA_StyledBackground, True)  # <-- ДОБАВИТЬ
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

    def add_widget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)

    def content_layout(self):
        return self._layout


class CardHeader(QFrame):
    """Заголовок карточки."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "CardHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)  # <-- ДОБАВИТЬ
        self.setFocusPolicy(Qt.NoFocus)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        self._title_label = QLabel()
        self._title_label.setProperty("class", "CardHeaderLabel")
        self._title_label.setFocusPolicy(Qt.NoFocus)
        self._title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        self._layout.addWidget(self._title_label)
        self._layout.addStretch()

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)

    def add_left_widget(self, widget: QWidget) -> None:
        self._layout.insertWidget(0, widget)

    def add_right_widget(self, widget: QWidget) -> None:
        self._layout.insertWidget(self._layout.count() - 1, widget)

    def mousePressEvent(self, event):
        
        print(f"Focus widget: {self.window().focusWidget()}")
        super().mousePressEvent(event)

class CardBody(QFrame):
    """Тело карточки."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "CardBody")
        self.setAttribute(Qt.WA_StyledBackground, True)  # <-- ДОБАВИТЬ
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

    def add_widget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)