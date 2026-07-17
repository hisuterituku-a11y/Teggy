from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Qt


class LogWidget(QPlainTextEdit):
    """Виджет для лога с цветными сообщениями."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setProperty("class", "LogWidget")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def info(self, msg: str):
        self.appendHtml(f'<span class="log-info">ℹ️ {msg}</span>')

    def success(self, msg: str):
        self.appendHtml(f'<span class="log-success">✅ {msg}</span>')

    def warning(self, msg: str):
        self.appendHtml(f'<span class="log-warning">⚠️ {msg}</span>')

    def error(self, msg: str):
        self.appendHtml(f'<span class="log-error">❌ {msg}</span>')