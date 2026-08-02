from __future__ import annotations

import os
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton

from core.converter import ImageConverter
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

    def _replace_processed_sources(self) -> list[str]:
        """Заменяет исходники, даже если временные файлы лежат на другом диске.

        Сначала обработанный файл копируется во временный файл рядом с
        назначением. Затем локальный временный файл атомарно подменяет итоговый.
        Так Windows не получает попытку ``os.replace`` между C: и X:.
        """
        errors: list[str] = []
        updated_selected_files: dict[Path, Path] = {}

        for source, prepared in self._replacement_jobs:
            converted = ImageConverter.needs_conversion(source)
            processed = prepared.with_suffix(".jpg") if converted else prepared
            destination = source.with_suffix(".jpg") if converted else source
            local_temp = destination.parent / (
                f".{destination.name}.teggy-{uuid4().hex}.tmp"
            )

            try:
                if not processed.is_file() or processed.stat().st_size == 0:
                    raise OSError("обработанный файл не создан")

                destination.parent.mkdir(parents=True, exist_ok=True)
                copy2(processed, local_temp)

                if not local_temp.is_file() or local_temp.stat().st_size == 0:
                    raise OSError("не удалось подготовить файл для замены")

                os.replace(local_temp, destination)

                if destination.resolve() != source.resolve():
                    source.unlink(missing_ok=True)

                processed.unlink(missing_ok=True)
                updated_selected_files[source.resolve()] = destination.resolve()
            except OSError as error:
                errors.append(f"{source}: {error}")
            finally:
                local_temp.unlink(missing_ok=True)

        if updated_selected_files:
            self.selected_files = [
                updated_selected_files.get(Path(path).resolve(), Path(path))
                for path in self.selected_files
                if updated_selected_files.get(Path(path).resolve(), Path(path)).exists()
            ]

        return errors
