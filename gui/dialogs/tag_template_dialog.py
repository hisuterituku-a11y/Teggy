from __future__ import annotations

import json

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.components.window_title_bar import WindowTitleBar


class TagTemplateDialog(QDialog):
    template_applied = Signal(dict)

    SETTINGS_KEY = "tagging/templates"

    def __init__(self, current_metadata: dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self._current_metadata = dict(current_metadata)
        self._settings = QSettings("Teggy", "Teggy")
        self._templates = self._load_templates()

        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(560, 430)

        shell = QWidget(self)
        shell.setObjectName("TemplateDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(
            WindowTitleBar(
                self,
                title="Шаблоны метаданных",
                show_help=False,
                show_minimize=False,
                show_maximize=False,
            )
        )

        content = QWidget()
        content.setObjectName("TemplateContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 22)
        content_layout.setSpacing(12)

        hint = QLabel(
            "Сохраняйте заполненные метаданные и применяйте их к новым наборам фотографий."
        )
        hint.setObjectName("CardSubtitle")
        hint.setWordWrap(True)
        content_layout.addWidget(hint)

        self.template_list = QListWidget()
        self.template_list.setObjectName("TemplateList")
        self.template_list.itemDoubleClicked.connect(lambda _: self.apply_selected())
        content_layout.addWidget(self.template_list, 1)

        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название шаблона")
        save_button = QPushButton("Сохранить текущие поля")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_template)
        name_row.addWidget(self.name_edit, 1)
        name_row.addWidget(save_button)
        content_layout.addLayout(name_row)

        action_row = QHBoxLayout()
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("AboutSecondaryButton")
        delete_button.clicked.connect(self.delete_selected)
        action_row.addWidget(delete_button)
        action_row.addStretch(1)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("AboutSecondaryButton")
        close_button.clicked.connect(self.reject)
        apply_button = QPushButton("Применить")
        apply_button.setObjectName("AboutPrimaryButton")
        apply_button.clicked.connect(self.apply_selected)
        action_row.addWidget(close_button)
        action_row.addWidget(apply_button)
        content_layout.addLayout(action_row)

        shell_layout.addWidget(content, 1)
        self._refresh_list()

    def _load_templates(self) -> dict[str, dict[str, str]]:
        raw = self._settings.value(self.SETTINGS_KEY, "{}")
        try:
            data = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            str(name): {str(key): str(value) for key, value in values.items()}
            for name, values in data.items()
            if isinstance(values, dict)
        }

    def _save_templates(self) -> None:
        self._settings.setValue(
            self.SETTINGS_KEY,
            json.dumps(self._templates, ensure_ascii=False),
        )

    def _refresh_list(self) -> None:
        selected = self.template_list.currentItem()
        selected_name = selected.text() if selected else None
        self.template_list.clear()
        for name in sorted(self._templates, key=str.casefold):
            self.template_list.addItem(name)
        if selected_name:
            matches = self.template_list.findItems(
                selected_name,
                Qt.MatchFlag.MatchExactly,
            )
            if matches:
                self.template_list.setCurrentItem(matches[0])

    def save_template(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Нет названия", "Введите название шаблона.")
            return
        self._templates[name] = dict(self._current_metadata)
        self._save_templates()
        self._refresh_list()
        matches = self.template_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if matches:
            self.template_list.setCurrentItem(matches[0])
        self.name_edit.clear()

    def delete_selected(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            return
        self._templates.pop(item.text(), None)
        self._save_templates()
        self._refresh_list()

    def apply_selected(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "Шаблон не выбран", "Выберите шаблон из списка.")
            return
        values = self._templates.get(item.text())
        if values is None:
            return
        self.template_applied.emit(dict(values))
        self.accept()
