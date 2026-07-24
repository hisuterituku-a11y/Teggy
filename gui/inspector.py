from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from core.metadata.metadata_service import MetadataService


class Inspector(QWidget):
    """Контекстная правая панель для файлов, шаблонов и импорта."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Inspector")
        self.setMinimumWidth(280)
        self.setMaximumWidth(340)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.eyebrow = QLabel("КОНТЕКСТ")
        self.eyebrow.setProperty("class", "InspectorEyebrow")
        root.addWidget(self.eyebrow)

        self.title = QLabel("Инспектор")
        self.title.setProperty("class", "InspectorTitle")
        self.title.setWordWrap(True)
        root.addWidget(self.title)

        self.subtitle = QLabel("")
        self.subtitle.setProperty("class", "InspectorMuted")
        self.subtitle.setWordWrap(True)
        root.addWidget(self.subtitle)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setProperty("class", "InspectorSeparator")
        root.addWidget(separator)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, stretch=1)

        self.info_container = QWidget()
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(10)
        self.info_layout.addStretch()
        scroll.setWidget(self.info_container)

        self.info_widgets: list[QWidget] = []
        self.show_placeholder()

    def set_context(self, context: str, payload: Mapping[str, Any] | None = None) -> None:
        payload = payload or {}
        if context == "metadata":
            self.show_placeholder("Файл не выбран", "Выберите изображение в списке, чтобы увидеть сведения и метаданные.")
        elif context == "templates":
            self.update_template_info(payload)
        elif context == "yandex":
            self.update_import_info(payload)
        else:
            self.show_placeholder()

    def show_placeholder(
        self,
        title: str = "Нет выбранного объекта",
        subtitle: str = "Информация появится здесь после выбора элемента.",
    ) -> None:
        self.clear_info()
        self.eyebrow.setText("КОНТЕКСТ")
        self.title.setText(title)
        self.subtitle.setText(subtitle)
        placeholder = QLabel("Выберите элемент\nв рабочей области")
        placeholder.setProperty("class", "InspectorPlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        self._add_widget(placeholder)

    def update_file_info(self, file_info) -> None:
        if not file_info:
            self.set_context("metadata")
            return

        self.clear_info()
        self.eyebrow.setText("ФАЙЛ")
        self.title.setText(file_info.name)
        self.subtitle.setText(str(file_info.path.parent))

        size = (
            f"{file_info.size_kb:.1f} KB"
            if file_info.size < 1024 * 1024
            else f"{file_info.size_mb:.1f} MB"
        )
        self._add_section(
            "Сведения",
            {
                "Формат": file_info.extension.upper().replace(".", ""),
                "Размер": size,
                "Изменён": file_info.modified.strftime("%d.%m.%Y %H:%M"),
                "Статус": "Готов к записи" if file_info.extension.lower() in {".jpg", ".jpeg"} else "Будет конвертирован в JPG",
            },
        )

        if file_info.extension.lower() not in {".jpg", ".jpeg"}:
            return

        try:
            metadata = MetadataService.read_metadata(str(file_info.path)) or {}
        except Exception:
            metadata = {}

        keywords = metadata.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [item.strip() for item in keywords.split(",") if item.strip()]

        self._add_section(
            "Метаданные",
            {
                "Название": metadata.get("title") or "—",
                "Тема": metadata.get("subject") or "—",
                "Автор": metadata.get("artist") or "—",
                "Тегов": len(keywords) if isinstance(keywords, list) else 0,
                "Рейтинг": metadata.get("rating") or "—",
            },
        )

        if keywords:
            self._add_tags(keywords[:12])

    def update_template_info(self, data: Mapping[str, Any] | None = None) -> None:
        data = data or {}
        name = str(data.get("name") or "Новый шаблон")
        keywords = data.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [item.strip() for item in keywords.replace("\n", ",").split(",") if item.strip()]

        self.clear_info()
        self.eyebrow.setText("ШАБЛОН")
        self.title.setText(name)
        self.subtitle.setText("Набор метаданных для массовой обработки")
        self._add_section(
            "Содержимое",
            {
                "Название": data.get("title") or "—",
                "Тема": data.get("subject") or "—",
                "Автор": data.get("artist") or "—",
                "Тегов": len(keywords) if isinstance(keywords, list) else 0,
                "Комментарий": data.get("comment") or "—",
            },
        )
        if keywords:
            self._add_tags(keywords[:16])

    def update_import_info(self, data: Mapping[str, Any] | None = None) -> None:
        data = data or {}
        running = bool(data.get("running", False))
        status = str(data.get("status") or ("Импорт выполняется" if running else "Готов к работе"))
        folder = str(data.get("folder") or "Не выбрана")
        url = str(data.get("url") or "Не указана")

        self.clear_info()
        self.eyebrow.setText("ИМПОРТ")
        self.title.setText("Яндекс Карты")
        self.subtitle.setText(status)
        self._add_section(
            "Задача",
            {
                "Состояние": "Выполняется" if running else "Ожидание",
                "Папка": folder,
                "Источник": url,
                "Пропускать существующие": "Да" if data.get("skip_existing", True) else "Нет",
            },
        )

    def _add_section(self, title: str, values: Mapping[str, Any]) -> None:
        section = QLabel(title)
        section.setProperty("class", "InspectorSubtitle")
        self._add_widget(section)

        card = QFrame()
        card.setProperty("class", "InspectorCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        for key, value in values.items():
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)
            key_label = QLabel(str(key))
            key_label.setProperty("class", "InspectorKey")
            value_label = QLabel(str(value))
            value_label.setProperty("class", "InspectorValue")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row_layout.addWidget(key_label)
            row_layout.addWidget(value_label)
            layout.addWidget(row)
        self._add_widget(card)

    def _add_tags(self, tags: list[str]) -> None:
        title = QLabel("Теги")
        title.setProperty("class", "InspectorSubtitle")
        self._add_widget(title)
        label = QLabel("  •  ".join(str(tag) for tag in tags))
        label.setProperty("class", "InspectorTags")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._add_widget(label)

    def _add_widget(self, widget: QWidget) -> None:
        self.info_layout.insertWidget(self.info_layout.count() - 1, widget)
        self.info_widgets.append(widget)

    def clear_info(self) -> None:
        for widget in self.info_widgets:
            self.info_layout.removeWidget(widget)
            widget.deleteLater()
        self.info_widgets.clear()
