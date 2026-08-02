from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from gui.pages.tagging_fixed import TaggingPage as BaseTaggingPage


class TaggingPage(BaseTaggingPage):
    """Финальный слой страницы тегирования с едиными карточками и шаблонами."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Подпись вынесена в отдельный QLabel, поэтому в самом QCheckBox
        # оставляем только индикатор состояния.
        self.delete_originals_checkbox.setText("")
        self.delete_originals_checkbox.setFixedWidth(24)

    def _build_processing_options(self) -> QFrame:
        card = QFrame()
        card.setObjectName("DownloadOptionCard")
        card.setProperty("selected", False)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        self.delete_originals_checkbox = QCheckBox()
        self.delete_originals_checkbox.setObjectName("DownloadOptionCheck")
        self.delete_originals_checkbox.setFixedWidth(24)
        self.delete_originals_checkbox.setToolTip(
            "Teggy сначала обрабатывает временные копии и только после полностью "
            "успешной обработки заменяет исходные фотографии на месте."
        )
        layout.addWidget(self.delete_originals_checkbox, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        title = QLabel("Заменять исходные фото обработанными")
        title.setObjectName("DownloadOptionTitle")
        text_layout.addWidget(title)

        description = QLabel(
            "Без галочки исходники сохраняются, а готовые копии появляются в папке Teggy. "
            "С галочкой отдельная папка Teggy не создаётся: после успешной обработки "
            "исходные файлы заменяются обработанными в выбранных папках."
        )
        description.setObjectName("DownloadOptionDescription")
        description.setWordWrap(True)
        text_layout.addWidget(description)

        layout.addLayout(text_layout, 1)

        def update_card_state(state: int) -> None:
            selected = state == Qt.CheckState.Checked.value
            card.setProperty("selected", "true" if selected else "false")
            card.style().unpolish(card)
            card.style().polish(card)
            card.update()

        self.delete_originals_checkbox.stateChanged.connect(update_card_state)
        return card

    def _install_template_button(self) -> None:
        for label in self.findChildren(QLabel):
            if label.text() != "2. Метаданные":
                continue
            layout = label.parentWidget().layout()
            if layout is None:
                return
            button = QPushButton("✦  Шаблоны метаданных")
            button.setObjectName("TemplateProminentButton")
            button.setMinimumHeight(40)
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
