from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.components.window_title_bar import WindowTitleBar


class ProcessingResultDialog(QDialog):
    def __init__(
        self,
        *,
        total: int,
        processed: int,
        converted: int,
        failed: int,
        output_dir: Path | None,
        cancelled: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._output_dir = output_dir

        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(480, 370)

        shell = QWidget(self)
        shell.setObjectName("ResultDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(
            WindowTitleBar(
                self,
                title="Результат обработки",
                show_help=False,
                show_minimize=False,
                show_maximize=False,
            )
        )

        content = QWidget()
        content.setObjectName("ResultContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 26, 28, 26)
        content_layout.setSpacing(18)

        title = QLabel("Обработка отменена" if cancelled else "Готово")
        title.setObjectName("ResultTitle")
        title.setMinimumHeight(32)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)

        stats = QFrame()
        stats.setObjectName("ResultStats")
        stats_layout = QGridLayout(stats)
        stats_layout.setContentsMargins(18, 16, 18, 16)
        stats_layout.setHorizontalSpacing(24)
        stats_layout.setVerticalSpacing(12)

        rows = (
            ("Всего файлов", total),
            ("Протегировано", processed),
            ("Преобразовано в JPG", converted),
            ("Ошибок", failed),
        )
        for row, (label_text, value) in enumerate(rows):
            label = QLabel(label_text)
            label.setObjectName("ResultStatLabel")
            label.setMinimumHeight(24)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            value_label = QLabel(str(value))
            value_label.setObjectName("ResultStatValue")
            value_label.setMinimumHeight(24)
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            stats_layout.addWidget(label, row, 0)
            stats_layout.addWidget(value_label, row, 1)

        content_layout.addWidget(stats)

        if output_dir is not None:
            open_button = QPushButton("Открыть папку Teggy")
            open_button.setObjectName("AboutPrimaryButton")
            open_button.clicked.connect(self._open_output_dir)
            content_layout.addWidget(open_button)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("AboutSecondaryButton")
        close_button.clicked.connect(self.accept)
        content_layout.addWidget(close_button)

        shell_layout.addWidget(content, 1)

    def _open_output_dir(self) -> None:
        if self._output_dir is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._output_dir)))
