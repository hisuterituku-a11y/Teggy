from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton

from gui.dialogs.tag_template_dialog import TagTemplateDialog
from gui.pages.tagging import TaggingPage as BaseTaggingPage


class TaggingPage(BaseTaggingPage):
    """Активная страница тегирования с шаблонами и заменой исходников."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.delete_originals_checkbox.setObjectName("DownloadOptionCheck")
        self.delete_originals_checkbox.setText(
            "Заменять исходные фото обработанными"
        )
        self.delete_originals_checkbox.setToolTip(
            "Без галочки исходники сохраняются, а обработанные копии появляются "
            "в папке Teggy. С галочкой Teggy обрабатывает временные копии и "
            "после успешной обработки заменяет исходные файлы на месте."
        )
        self.delete_sources_checkbox: QCheckBox = self.delete_originals_checkbox
        self.delete_sources_checkbox.style().unpolish(
            self.delete_sources_checkbox
        )
        self.delete_sources_checkbox.style().polish(
            self.delete_sources_checkbox
        )

        self.drop_hint.setText("Перетащите папки или фото сюда")
        self._install_template_button()

    def _install_template_button(self) -> None:
        for label in self.findChildren(QLabel):
            if label.text() != "2. Метаданные":
                continue

            layout = label.parentWidget().layout()
            if layout is None:
                return

            button = QPushButton("Шаблоны")
            button.setObjectName("AboutSecondaryButton")
            button.setMinimumHeight(30)
            button.clicked.connect(self.open_template_dialog)
            layout.addWidget(
                button,
                0,
                1,
                alignment=Qt.AlignmentFlag.AlignRight,
            )
            return

    def _current_metadata(self) -> dict[str, str]:
        return {
            key: widget.toPlainText() if key == "keywords" else widget.text()
            for key, widget in self.metadata_fields.items()
        }

    def open_template_dialog(self) -> None:
        dialog = TagTemplateDialog(self._current_metadata(), parent=self)
        dialog.template_applied.connect(self.apply_template)
        dialog.exec()

    def apply_template(self, values: dict) -> None:
        for key, widget in self.metadata_fields.items():
            value = str(values.get(key, ""))
            if key == "keywords":
                widget.setPlainText(value)
            else:
                widget.setText(value)
