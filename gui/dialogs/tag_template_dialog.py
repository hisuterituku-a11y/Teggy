from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMessageBox, QPushButton, QSplitter, QTextEdit,
    QVBoxLayout, QWidget,
)

from core.tag_template_store import TagTemplateStore
from gui.components.window_title_bar import WindowTitleBar


class TagTemplateDialog(QDialog):
    template_applied = Signal(dict)
    templates_changed = Signal()

    FIELD_LABELS = (
        ("title", "Название"), ("subject", "Тема"),
        ("comment", "Комментарий"), ("artist", "Автор"),
        ("copyright", "Авторские права"), ("keywords", "Теги"),
    )

    def __init__(self, current_metadata: dict[str, str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._store = TagTemplateStore()
        self._templates = self._store.load()
        self._current_metadata = dict(current_metadata or {})
        self._fields: dict[str, QWidget] = {}
        self._loaded_name: str | None = None

        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(820, 580)
        self.resize(900, 640)

        shell = QWidget(self)
        shell.setObjectName("TemplateDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(WindowTitleBar(
            self, title="Управление шаблонами метаданных",
            show_help=False, show_minimize=False, show_maximize=False,
        ))

        content = QWidget()
        content.setObjectName("TemplateContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 20, 22, 22)
        content_layout.setSpacing(14)
        intro = QLabel(
            "Создавайте, редактируйте и применяйте наборы метаданных. "
            "Эти же шаблоны доступны при загрузке фотографий из Яндекс Карт."
        )
        intro.setObjectName("CardSubtitle")
        intro.setWordWrap(True)
        content_layout.addWidget(intro)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        sidebar = QFrame()
        sidebar.setObjectName("TemplateSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)
        sidebar_title = QLabel("Шаблоны")
        sidebar_title.setObjectName("CardTitle")
        sidebar_layout.addWidget(sidebar_title)
        self.template_list = QListWidget()
        self.template_list.setObjectName("TemplateList")
        self.template_list.currentItemChanged.connect(self._load_selected)
        self.template_list.itemDoubleClicked.connect(lambda _: self.apply_selected())
        sidebar_layout.addWidget(self.template_list, 1)
        for text, handler, object_name in (
            ("＋ Новый шаблон", self.new_template, "TemplateManagerButton"),
            ("Дублировать", self.duplicate_selected, "TemplateManagerButton"),
            ("Удалить шаблон", self.delete_selected, "TemplateDangerButton"),
        ):
            button = QPushButton(text)
            button.setObjectName(object_name)
            button.clicked.connect(handler)
            sidebar_layout.addWidget(button)

        editor = QFrame()
        editor.setObjectName("TemplateEditor")
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(18, 16, 18, 16)
        editor_layout.setSpacing(12)
        editor_title = QLabel("Содержимое шаблона")
        editor_title.setObjectName("CardTitle")
        editor_layout.addWidget(editor_title)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Стоматология, Ресторан, Салон красоты")
        form.addRow("Название шаблона", self.name_edit)
        for key, label_text in self.FIELD_LABELS:
            if key in {"comment", "keywords"}:
                field = QTextEdit()
                field.setFixedHeight(76 if key == "keywords" else 64)
            else:
                field = QLineEdit()
            field.setPlaceholderText("По одному тегу в строке" if key == "keywords" else f"Введите: {label_text.lower()}")
            self._fields[key] = field
            form.addRow(label_text, field)
        editor_layout.addLayout(form)
        use_current_button = QPushButton("Заполнить из текущих полей")
        use_current_button.setObjectName("TemplateManagerButton")
        use_current_button.clicked.connect(self.fill_from_current)
        editor_layout.addWidget(use_current_button, alignment=Qt.AlignmentFlag.AlignLeft)
        editor_layout.addStretch(1)
        save_row = QHBoxLayout()
        save_row.addStretch(1)
        save_button = QPushButton("Сохранить изменения")
        save_button.setObjectName("TemplatePrimaryButton")
        save_button.clicked.connect(self.save_template)
        save_row.addWidget(save_button)
        editor_layout.addLayout(save_row)

        splitter.addWidget(sidebar)
        splitter.addWidget(editor)
        splitter.setSizes([260, 560])
        content_layout.addWidget(splitter, 1)
        action_row = QHBoxLayout()
        close_button = QPushButton("Закрыть")
        close_button.setObjectName("AboutSecondaryButton")
        close_button.clicked.connect(self.reject)
        action_row.addWidget(close_button)
        action_row.addStretch(1)
        apply_button = QPushButton("Применить выбранный шаблон")
        apply_button.setObjectName("TemplatePrimaryButton")
        apply_button.clicked.connect(self.apply_selected)
        action_row.addWidget(apply_button)
        content_layout.addLayout(action_row)
        shell_layout.addWidget(content, 1)
        self._refresh_list()
        self.new_template()

    def _field_values(self) -> dict[str, str]:
        return {
            key: widget.toPlainText() if isinstance(widget, QTextEdit) else widget.text()
            for key, widget in self._fields.items()
        }

    def _set_field_values(self, values: dict[str, str]) -> None:
        for key, widget in self._fields.items():
            value = str(values.get(key, ""))
            if isinstance(widget, QTextEdit):
                widget.setPlainText(value)
            else:
                widget.setText(value)

    def _refresh_list(self, select_name: str | None = None) -> None:
        self.template_list.blockSignals(True)
        self.template_list.clear()
        for name in sorted(self._templates, key=str.casefold):
            self.template_list.addItem(name)
        self.template_list.blockSignals(False)
        if select_name:
            matches = self.template_list.findItems(select_name, Qt.MatchFlag.MatchExactly)
            if matches:
                self.template_list.setCurrentItem(matches[0])

    def _load_selected(self, current, previous=None) -> None:
        if current is None:
            return
        name = current.text()
        values = self._templates.get(name)
        if values is not None:
            self._loaded_name = name
            self.name_edit.setText(name)
            self._set_field_values(values)

    def new_template(self) -> None:
        self.template_list.clearSelection()
        self.template_list.setCurrentItem(None)
        self._loaded_name = None
        self.name_edit.clear()
        self._set_field_values({})
        self.name_edit.setFocus()

    def fill_from_current(self) -> None:
        self._set_field_values(self._current_metadata)

    def save_template(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Нет названия", "Введите название шаблона.")
            return
        if self._loaded_name and self._loaded_name != name:
            self._templates.pop(self._loaded_name, None)
        self._templates[name] = self._field_values()
        self._store.save_all(self._templates)
        self._loaded_name = name
        self._refresh_list(name)
        self.templates_changed.emit()

    def duplicate_selected(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "Шаблон не выбран", "Сначала выберите шаблон.")
            return
        source_name = item.text()
        candidate = f"{source_name} — копия"
        index = 2
        while candidate in self._templates:
            candidate = f"{source_name} — копия {index}"
            index += 1
        self._templates[candidate] = dict(self._templates.get(source_name, {}))
        self._store.save_all(self._templates)
        self._refresh_list(candidate)
        self.templates_changed.emit()

    def delete_selected(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            return
        name = item.text()
        answer = QMessageBox.question(
            self, "Удалить шаблон", f"Удалить шаблон «{name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._templates.pop(name, None)
        self._store.save_all(self._templates)
        self.templates_changed.emit()
        self._refresh_list()
        self.new_template()

    def apply_selected(self) -> None:
        name = self.name_edit.text().strip()
        values = self._templates.get(name)
        if values is None:
            item = self.template_list.currentItem()
            values = self._templates.get(item.text()) if item else None
        if values is None:
            QMessageBox.warning(self, "Шаблон не выбран", "Выберите сохранённый шаблон из списка.")
            return
        self.template_applied.emit(dict(values))
        self.accept()
