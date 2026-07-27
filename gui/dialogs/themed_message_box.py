from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainterPath, QPixmap, QRegion
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.paths import resource_path
from gui.components.window_title_bar import WindowTitleBar


class _MessageDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton,
        default_button: QMessageBox.StandardButton | None,
    ) -> None:
        super().__init__(parent)
        self.result_button = QMessageBox.StandardButton.NoButton

        self.setObjectName("ThemedMessageBox")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(480)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(
            WindowTitleBar(
                self,
                title=title,
                show_help=False,
                show_minimize=False,
                show_maximize=False,
            )
        )

        content = QWidget()
        content.setObjectName("ThemedMessageContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 18, 20, 20)
        content_layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("ThemedMessageCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(16)

        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_file = ThemedMessageBox.ICON_FILES.get(icon)
        if icon_file:
            pixmap = QPixmap(str(resource_path("assets", "icons", "teggy", icon_file)))
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(
                        44,
                        44,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        card_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_label = QLabel(text)
        text_label.setObjectName("ThemedMessageText")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_label.setMinimumWidth(320)
        card_layout.addWidget(text_label, 1)
        content_layout.addWidget(card)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        for standard, caption, object_name in self._button_specs(buttons):
            button = QPushButton(caption)
            button.setObjectName(object_name)
            button.setMinimumSize(112, 38)
            button.clicked.connect(lambda checked=False, value=standard: self._finish(value))
            if default_button == standard:
                button.setDefault(True)
                button.setFocus()
            button_row.addWidget(button)
        content_layout.addLayout(button_row)
        root.addWidget(content)

    @staticmethod
    def _button_specs(buttons: QMessageBox.StandardButton):
        specs = []
        if buttons & QMessageBox.StandardButton.No:
            specs.append((QMessageBox.StandardButton.No, "Нет", "AboutSecondaryButton"))
        if buttons & QMessageBox.StandardButton.Cancel:
            specs.append((QMessageBox.StandardButton.Cancel, "Отмена", "AboutSecondaryButton"))
        if buttons & QMessageBox.StandardButton.Yes:
            specs.append((QMessageBox.StandardButton.Yes, "Да", "PrimaryButton"))
        if buttons & QMessageBox.StandardButton.Ok:
            specs.append((QMessageBox.StandardButton.Ok, "OK", "PrimaryButton"))
        return specs

    def _finish(self, result: QMessageBox.StandardButton) -> None:
        self.result_button = result
        self.accept()

    def reject(self) -> None:
        if self.result_button == QMessageBox.StandardButton.NoButton:
            self.result_button = QMessageBox.StandardButton.No
        super().reject()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 12, 12)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))


class ThemedMessageBox:
    """Teggy-styled replacement for QMessageBox helper methods."""

    ICON_FILES = {
        QMessageBox.Icon.Warning: "dialog-warning.svg",
        QMessageBox.Icon.Critical: "dialog-error.svg",
        QMessageBox.Icon.Question: "dialog-question.svg",
        QMessageBox.Icon.Information: "dialog-info.svg",
    }

    @classmethod
    def _exec(
        cls,
        parent: QWidget | None,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton,
        default_button: QMessageBox.StandardButton | None = None,
    ) -> QMessageBox.StandardButton:
        dialog = _MessageDialog(
            parent,
            icon=icon,
            title=title,
            text=text,
            buttons=buttons,
            default_button=default_button,
        )
        dialog.exec()
        return dialog.result_button

    @classmethod
    def warning(cls, parent: QWidget | None, title: str, text: str) -> QMessageBox.StandardButton:
        return cls._exec(parent, QMessageBox.Icon.Warning, title, text, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)

    @classmethod
    def critical(cls, parent: QWidget | None, title: str, text: str) -> QMessageBox.StandardButton:
        return cls._exec(parent, QMessageBox.Icon.Critical, title, text, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)

    @classmethod
    def information(cls, parent: QWidget | None, title: str, text: str) -> QMessageBox.StandardButton:
        return cls._exec(parent, QMessageBox.Icon.Information, title, text, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)

    @classmethod
    def question(
        cls,
        parent: QWidget | None,
        title: str,
        text: str,
        default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.No,
    ) -> QMessageBox.StandardButton:
        return cls._exec(
            parent,
            QMessageBox.Icon.Question,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button,
        )
