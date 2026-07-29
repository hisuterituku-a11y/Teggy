from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.paths import resource_path
from core.statistics import StatisticsStore
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

        StatisticsStore().increment(
            tagged=processed,
            converted=converted,
            failed=failed,
        )

        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(500)
        self.setMinimumHeight(500)

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
        content_layout.setContentsMargins(30, 20, 30, 24)
        content_layout.setSpacing(14)

        icon_name = (
            "dialog-info.svg"
            if cancelled
            else "dialog-error.svg"
            if failed
            else "dialog-success.svg"
        )

        icon_label = QLabel()
        icon_label.setObjectName("ResultIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedHeight(64)

        icon_pixmap = QPixmap(
            str(resource_path("assets", "icons", "teggy", icon_name))
        )

        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(
                    54,
                    54,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        content_layout.addWidget(icon_label)

        title_text = (
            "Обработка отменена"
            if cancelled
            else "Обработка завершена с ошибками"
            if failed
            else "Готово"
        )

        title = QLabel(title_text)
        title.setObjectName("ResultTitle")
        title.setFixedHeight(32)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)

        stats = QFrame()
        stats.setObjectName("ResultStats")
        stats.setMinimumHeight(130)
        stats.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        stats_layout = QGridLayout(stats)
        stats_layout.setContentsMargins(18, 14, 18, 14)
        stats_layout.setHorizontalSpacing(24)
        stats_layout.setVerticalSpacing(6)
        stats_layout.setColumnStretch(0, 1)
        stats_layout.setColumnStretch(1, 0)

        rows = (
            ("Всего файлов", total),
            ("Протегировано", processed),
            ("Преобразовано в JPG", converted),
            ("Ошибок", failed),
        )

        for row, (label_text, value) in enumerate(rows):
            label = QLabel(label_text)
            label.setObjectName("ResultStatLabel")
            label.setFixedHeight(22)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            value_label = QLabel(str(value))
            value_label.setObjectName("ResultStatValue")
            value_label.setFixedHeight(22)
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            stats_layout.addWidget(label, row, 0)
            stats_layout.addWidget(value_label, row, 1)

        content_layout.addWidget(stats)

        if output_dir is not None:
            open_button = QPushButton("Открыть папку Teggy")
            open_button.setObjectName("PrimaryButton")
            open_button.setFixedHeight(56)
            open_button.clicked.connect(self._open_output_dir)
            content_layout.addWidget(open_button)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("AboutSecondaryButton")
        close_button.setFixedHeight(40)
        close_button.clicked.connect(self.accept)
        content_layout.addWidget(close_button)

        shell_layout.addWidget(content)

        self.adjustSize()

    def _open_output_dir(self) -> None:
        if self._output_dir is not None:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._output_dir))
            )
