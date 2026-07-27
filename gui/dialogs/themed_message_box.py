from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget

from core.paths import resource_path


class ThemedMessageBox:
    """Application-styled, non-native QMessageBox helpers."""

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
        box = QMessageBox(parent)
        box.setObjectName("ThemedMessageBox")
        box.setOption(QMessageBox.Option.DontUseNativeDialog, True)

        icon_file = cls.ICON_FILES.get(icon)
        pixmap = (
            QPixmap(str(resource_path("assets", "icons", "teggy", icon_file)))
            if icon_file
            else QPixmap()
        )
        if not pixmap.isNull():
            box.setIconPixmap(
                pixmap.scaled(
                    44,
                    44,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            box.setIcon(icon)

        box.setWindowTitle(title)
        box.setText(text)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setStandardButtons(buttons)
        if default_button is not None:
            box.setDefaultButton(default_button)

        for button in box.findChildren(QPushButton):
            standard = box.standardButton(button)
            if standard in {
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Save,
                QMessageBox.StandardButton.Apply,
            }:
                button.setObjectName("PrimaryButton")
                button.setMinimumWidth(112)
            else:
                button.setObjectName("AboutSecondaryButton")
                button.setMinimumWidth(104)
            button.setMinimumHeight(38)

        box.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        box.setWindowModality(Qt.WindowModality.WindowModal)
        box.setMinimumWidth(460)
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
    def information(cls, parent: QWidget | None, title: str, text: str) -> QMessageBox.StandardButton:
        return cls._exec(
            parent,
            QMessageBox.Icon.Information,
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
