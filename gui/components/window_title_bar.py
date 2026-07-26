from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from core.version import display_version


class WindowTitleBar(QFrame):
    """Кастомная верхняя панель frameless-окна Teggy."""

    def __init__(self, window):
        super().__init__(window)
        self._window = window
        self._drag_position: QPoint | None = None

        self.setObjectName("WindowTitleBar")
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel(display_version())
        title.setObjectName("WindowTitle")
        layout.addWidget(title)
        layout.addStretch()

        self.help_button = self._button("?", "WindowHelpButton", "О программе")
        self.minimize_button = self._button("−", "WindowControlButton", "Свернуть")
        self.maximize_button = self._button("□", "WindowControlButton", "Развернуть")
        self.close_button = self._button("×", "WindowCloseButton", "Закрыть")

        self.minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(window.close)

        layout.addWidget(self.help_button)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

    def _button(self, text: str, object_name: str, tooltip: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setToolTip(tooltip)
        button.setFixedSize(46, 42)
        return button

    def _toggle_maximized(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
            self.maximize_button.setText("□")
        else:
            self._window.showMaximized()
            self.maximize_button.setText("❐")

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
            event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._window.isMaximized():
            self._drag_position = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and not self._window.isMaximized()
        ):
            self._window.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_position = None
        super().mouseReleaseEvent(event)
