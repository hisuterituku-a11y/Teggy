from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent, QKeySequence
from PySide6.QtWidgets import QTextEdit


class PlainPasteFilter(QObject):
    """Вставляет в QTextEdit только обычный текст без HTML-оформления."""

    def eventFilter(self, watched, event) -> bool:
        if not isinstance(watched, QTextEdit):
            return False
        if event.type() != QEvent.Type.KeyPress:
            return False
        if not isinstance(event, QKeyEvent):
            return False

        is_paste = (
            event.key() == Qt.Key.Key_V
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ) or event.matches(QKeySequence.StandardKey.Paste)
        if not is_paste or watched.isReadOnly():
            return False

        watched.textCursor().insertText(QGuiApplication.clipboard().text())
        return True
