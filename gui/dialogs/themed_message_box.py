from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QWidget


class ThemedMessageBox:
    """Application-styled replacement for native QMessageBox helpers."""

    @staticmethod
    def _exec(
        parent: QWidget | None,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton,
        default_button: QMessageBox.StandardButton | None = None,
    ) -> QMessageBox.StandardButton:
        box = QMessageBox(parent)
        box.setObjectName("ThemedMessageBox")
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setStandardButtons(buttons)
        if default_button is not None:
            box.setDefaultButton(default_button)
        box.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        box.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        box.setMinimumWidth(390)
        return QMessageBox.StandardButton(box.exec())

    @classmethod
    def warning(cls, parent: QWidget | None, title: str, text: str) -> QMessageBox.StandardButton:
        return cls._exec(
            parent,
            QMessageBox.Icon.Warning,
            title,
            text,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
        )

    @classmethod
    def critical(cls, parent: QWidget | None, title: str, text: str) -> QMessageBox.StandardButton:
        return cls._exec(
            parent,
            QMessageBox.Icon.Critical,
            title,
            text,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
        )

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
