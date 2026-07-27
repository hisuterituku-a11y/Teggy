from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from gui.pages.tagging_fixed import TaggingPage as BaseTaggingPage


class TaggingPage(BaseTaggingPage):
    """Финальный слой страницы тегирования с заметным управлением шаблонами."""

    def _install_template_button(self) -> None:
        for label in self.findChildren(QLabel):
            if label.text() != "2. Метаданные":
                continue
            layout = label.parentWidget().layout()
            if layout is None:
                return
            button = QPushButton("✦  Шаблоны метаданных")
            button.setObjectName("PrimaryButton")
            button.setMinimumHeight(36)
            button.setToolTip("Создать, изменить или применить шаблон метаданных")
            button.clicked.connect(self.open_template_dialog)
            layout.addWidget(
                button,
                0,
                1,
                alignment=Qt.AlignmentFlag.AlignRight,
            )
            self.template_button = button
            return
